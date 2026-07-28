from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .calculators import IMPLEMENTATIONS, IMPLEMENTATIONS_BY_ID
from .contracts import load_declared_contracts, validate_contract_alignment
from .extensions import ManifestError, discover_custom_calculators
from .models import CalculatorMetadata
from .release import CLINICALLY_RELEASED_IDS
from .search import SearchIndex, SearchMatch, SearchResponse
from .skill import CalculatorSkill


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "clinical_calculator_inventory_full.csv"
DEFAULT_ALIASES_CSV = ROOT / "clinical_calculator_aliases.csv"

PARTIAL_INPUT_MARKERS = {
    "acute_physiology_score",
    "component_points",
    "components",
    "log_odds",
    "risk_score",
    "total_score",
}
KNOWN_PARTIAL_IDS = {
    "CALC-0004",  # SOFA currently accepts six pre-scored organ components.
    "CALC-0234",
    "CALC-0237",
    "CALC-0278",
    "CALC-0283",
}

FIELD_MAP = {
    "id": "id",
    "专业类别": "category",
    "亚专科": "subspecialty",
    "疾病/场景": "scenario",
    "中文名称": "name_cn",
    "英文名称": "name_en",
    "输入": "inputs",
    "输出": "output",
    "量表/方程": "formula",
    "评分解读": "interpretation",
    "用途": "purpose",
    "来源类型": "source_type",
    "来源/指南": "source",
    "来源链接": "source_url",
    "获取渠道": "channel",
    "真实性层级": "evidence_tier",
    "常用程度": "commonness",
    "覆盖说明": "coverage_note",
    "临床使用说明": "clinical_note",
    "版本/年份": "version",
    "条目来源": "entry_source",
    "来源分组": "source_group",
    "备注": "notes",
}


@dataclass(frozen=True)
class CalculatorSearchResult:
    skill: CalculatorSkill
    match: SearchMatch


@dataclass(frozen=True)
class CalculatorSearchResponse:
    status: str
    results: tuple[CalculatorSearchResult, ...]
    suggestions: tuple[str, ...] = ()

    @property
    def skills(self) -> list[CalculatorSkill]:
        """Return skills for the legacy list-returning search methods."""

        return [result.skill for result in self.results]

    def match_for(self, calculator_id: str) -> SearchMatch | None:
        """Return match diagnostics for an ID within this response."""

        return next(
            (
                result.match
                for result in self.results
                if result.skill.metadata.id == calculator_id
            ),
            None,
        )


class CalculatorRegistry:
    def __init__(
        self,
        skills: list[CalculatorSkill],
        aliases: dict[str, tuple[str, str]] | None = None,
        inventory_rows: int | None = None,
    ) -> None:
        self.skills = skills
        self.aliases = aliases or {}
        self.inventory_rows = inventory_rows if inventory_rows is not None else len(skills)
        self._by_name: dict[str, CalculatorSkill] = {}
        self._all_by_name: dict[str, list[CalculatorSkill]] = {}
        self._by_id: dict[str, CalculatorSkill] = {}
        for skill in skills:
            self._by_id[skill.metadata.id] = skill
            self._by_name.setdefault(skill.metadata.name_cn, skill)
            self._all_by_name.setdefault(skill.metadata.name_cn, []).append(skill)
        for alias_id, (canonical_id, _) in self.aliases.items():
            if alias_id in self._by_id:
                raise ValueError(f"alias id is still present as a calculator row: {alias_id}")
            if canonical_id not in self._by_id:
                raise ValueError(
                    f"calculator alias target does not exist: {alias_id} -> {canonical_id}"
                )
        self._search_index = SearchIndex(skills)

    def __len__(self) -> int:
        return len(self.skills)

    def unique_names(self) -> set[str]:
        return set(self._by_name)

    def get(self, name_or_id: str) -> CalculatorSkill:
        if name_or_id in self.aliases:
            name_or_id = self.aliases[name_or_id][0]
        if name_or_id in self._by_id:
            return self._by_id[name_or_id]
        if name_or_id in self._by_name:
            return self._by_name[name_or_id]
        raise KeyError(name_or_id)

    def alias_target(self, calculator_id: str) -> str | None:
        alias = self.aliases.get(calculator_id)
        return alias[0] if alias else None

    def get_all(self, name: str) -> list[CalculatorSkill]:
        """Return every row for a duplicated display name."""
        return list(self._all_by_name.get(name, ()))

    def ambiguous_names(self) -> dict[str, tuple[str, ...]]:
        return {
            name: tuple(skill.metadata.id for skill in skills)
            for name, skills in self._all_by_name.items()
            if len(skills) > 1
        }

    def search(self, query: str, limit: int | None = 20) -> list[CalculatorSkill]:
        return self.search_detailed(query, limit).skills

    def search_detailed(
        self, query: str, limit: int | None = 20
    ) -> CalculatorSearchResponse:
        return self._search(query, limit=limit)

    def _search(
        self,
        query: str,
        *,
        limit: int | None,
        allowed_ids: set[str] | None = None,
    ) -> CalculatorSearchResponse:
        response = self._search_index.search(
            query,
            limit=limit,
            allowed_ids=allowed_ids,
        )
        if response.status == "no_match" and allowed_ids is not None:
            catalog_response = self._search_index.search(query, limit=5)
            catalog_suggestions = [
                self._by_id[hit.calculator_id].metadata.name_cn
                for hit in catalog_response.hits
            ]
            catalog_suggestions.extend(catalog_response.suggestions)
            suggestions = tuple(
                dict.fromkeys((*catalog_suggestions, *response.suggestions))
            )[:5]
            response = SearchResponse("no_match", (), suggestions)
        return CalculatorSearchResponse(
            response.status,
            tuple(
                CalculatorSearchResult(self._by_id[hit.calculator_id], hit.match)
                for hit in response.hits
            ),
            response.suggestions,
        )

    def by_category(self, category: str) -> list[CalculatorSkill]:
        return [skill for skill in self.skills if skill.metadata.category == category]

    def categories(self) -> list[str]:
        return sorted({skill.metadata.category for skill in self.skills})

    def implemented(self) -> list[CalculatorSkill]:
        return [skill for skill in self.skills if skill.implemented]

    def runnable(self) -> list[CalculatorSkill]:
        """Return complete and partial entries with executable local logic."""
        return self.implemented()

    def automated_review_ready(self) -> list[CalculatorSkill]:
        """Return entries passing automated gates; clinician approval is separate."""
        return [skill for skill in self.skills if skill.medical_review_check().ok]

    def released(self) -> list[CalculatorSkill]:
        """Return only entries on the explicit clinician-approved release allowlist."""
        return [skill for skill in self.skills if skill.metadata.id in CLINICALLY_RELEASED_IDS]

    def search_runnable(self, query: str, limit: int | None = 20) -> list[CalculatorSkill]:
        return self.search_runnable_detailed(query, limit).skills

    def search_runnable_detailed(
        self, query: str, limit: int | None = 20
    ) -> CalculatorSearchResponse:
        runnable_ids = {skill.metadata.id for skill in self.runnable()}
        return self._search(query, limit=limit, allowed_ids=runnable_ids)

    def search_released(self, query: str, limit: int | None = 20) -> list[CalculatorSkill]:
        return self.search_released_detailed(query, limit).skills

    def search_released_detailed(
        self, query: str, limit: int | None = 20
    ) -> CalculatorSearchResponse:
        released_ids = {skill.metadata.id for skill in self.released()}
        return self._search(query, limit=limit, allowed_ids=released_ids)

    def summary(self) -> dict[str, object]:
        implemented = self.implemented()
        implemented_names = sorted({skill.metadata.name_cn for skill in implemented})
        return {
            "total_rows": len(self.skills),
            "inventory_rows": self.inventory_rows,
            "merged_alias_rows": len(self.aliases),
            "unique_chinese_names": len(self.unique_names()),
            "implemented_rows": len(implemented),
            "implemented_unique_names": len(implemented_names),
            "implementation_levels": {
                level: sum(skill.implementation_level == level for skill in self.skills)
                for level in ("complete", "partial")
            },
            "ambiguous_name_groups": len(self.ambiguous_names()),
            "versioned_rows": sum(bool(skill.metadata.version) for skill in self.skills),
            "medical_review_ready_rows": sum(skill.medical_review_check().ok for skill in self.skills),
            "released_rows": len(self.released()),
            "custom_rows": sum(skill.metadata.source_group == "custom" for skill in self.skills),
            "implemented_names": implemented_names,
        }


def _metadata_from_row(row: dict[str, str]) -> CalculatorMetadata:
    values = {target: row.get(source, "").strip() for source, target in FIELD_MAP.items()}
    return CalculatorMetadata(**values)


def _calculator_aliases(path: Path) -> dict[str, tuple[str, str]]:
    if path.resolve() != DEFAULT_CSV.resolve() or not DEFAULT_ALIASES_CSV.exists():
        return {}
    aliases: dict[str, tuple[str, str]] = {}
    with DEFAULT_ALIASES_CSV.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            alias_id = row.get("alias_id", "").strip()
            canonical_id = row.get("canonical_id", "").strip()
            reason = row.get("reason", "").strip()
            if not alias_id or not canonical_id or not reason:
                raise ValueError("calculator alias rows require alias_id, canonical_id, and reason")
            if alias_id == canonical_id:
                raise ValueError(f"calculator alias cannot target itself: {alias_id}")
            if alias_id in aliases:
                raise ValueError(f"duplicate calculator alias id: {alias_id}")
            aliases[alias_id] = (canonical_id, reason)
    alias_ids = set(aliases)
    chained = sorted(
        alias_id for alias_id, (target, _) in aliases.items() if target in alias_ids
    )
    if chained:
        raise ValueError(f"calculator aliases cannot target other aliases: {', '.join(chained)}")
    return aliases


def _implementation_level(
    calculator_id: str, required_inputs: tuple[str, ...]
) -> str:
    if calculator_id in KNOWN_PARTIAL_IDS:
        return "partial"
    if any(
        name in PARTIAL_INPUT_MARKERS
        or name in {"l", "m", "s"}
        or "component" in name
        or name.endswith(("_score", "_points"))
        for name in required_inputs
    ):
        return "partial"
    return "complete"


def load_registry(
    csv_path: str | Path | None = None,
    *,
    custom_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
    include_custom: bool = True,
) -> CalculatorRegistry:
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    aliases = _calculator_aliases(path)
    skills: list[CalculatorSkill] = []
    resolved_required_inputs: dict[str, tuple[str, ...]] = {}
    inventory_rows = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            inventory_rows += 1
            if row.get("id", "").strip() in aliases:
                continue
            metadata = _metadata_from_row(row)
            implementation, required_inputs = IMPLEMENTATIONS_BY_ID.get(
                metadata.id, IMPLEMENTATIONS.get(metadata.name_cn, (None, ()))
            )
            if implementation is None:
                raise ValueError(
                    f"inventory contains calculator without local implementation: {metadata.id}"
                )
            implementation_module = implementation.__module__ if implementation else ""
            resolved_required_inputs[metadata.id] = required_inputs
            level = _implementation_level(metadata.id, required_inputs)
            skills.append(
                CalculatorSkill(
                    metadata,
                    implementation,
                    required_inputs,
                    implementation_module,
                    level,
                )
            )
    validate_contract_alignment(
        load_declared_contracts(),
        resolved_required_inputs,
        {skill.metadata.id for skill in skills},
    )
    if include_custom:
        built_in_ids = {skill.metadata.id for skill in skills} | set(aliases)
        for definition in discover_custom_calculators(custom_dirs):
            if definition.metadata.id in built_in_ids:
                raise ManifestError(
                    f"custom calculator id collides with an existing calculator: {definition.metadata.id}"
                )
            built_in_ids.add(definition.metadata.id)
            skills.append(
                CalculatorSkill(
                    definition.metadata,
                    definition.implementation,
                    definition.required_inputs,
                    definition.implementation.__module__,
                    "complete",
                    definition.input_schema,
                )
            )
    return CalculatorRegistry(skills, aliases, inventory_rows)
