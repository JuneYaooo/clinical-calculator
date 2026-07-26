from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

from .calculators import IMPLEMENTATIONS, IMPLEMENTATIONS_BY_ID
from .extensions import ManifestError, discover_custom_calculators
from .models import CalculatorMetadata
from .release import CLINICALLY_RELEASED_IDS
from .skill import CalculatorSkill


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "clinical_calculator_inventory_full.csv"
DEFAULT_ALIASES_CSV = ROOT / "clinical_calculator_aliases.csv"
IMPLEMENTATION_STATUS_CSV = ROOT / "reports" / "calculator_implementation_status.csv"

PARTIAL_INPUT_MARKERS = {
    "acute_physiology_score",
    "component_points",
    "components",
    "log_odds",
    "risk_score",
    "total_score",
}
LICENSED_BLOCKERS = {"rights_limited_questionnaire", "staging_or_subscription"}
SOURCE_CANDIDATE_BLOCKERS = {
    "formula_audit_needed",
    "formula_missing",
    "manual_research_needed",
    "model_coefficients_needed",
    "reference_tables_needed",
    "chart_digitization_needed",
}
GUIDANCE_KNOWLEDGE_BLOCKERS = {
    "guideline_pathway",
    "drug_rule",
    "prevention_guideline",
}
CONTROLLED_CONTENT_BLOCKERS = {
    "rights_limited_questionnaire",
    "staging_or_subscription",
}
CATALOG_LAYERS = (
    "executable",
    "source_candidate",
    "guidance_knowledge",
    "controlled_content",
)
KNOWN_PARTIAL_IDS = {
    "CALC-0004",  # SOFA currently accepts six pre-scored organ components.
    "CALC-0234",
    "CALC-0237",
    "CALC-0278",
    "CALC-0283",
}

# Search aliases are deliberately small and domain-specific. They bridge common
# clinician wording without changing calculator metadata or guessing formulas.
SEARCH_ALIASES = {
    "卒中": ("卒中", "中风", "stroke"),
    "中风": ("中风", "卒中", "stroke"),
    "房颤": ("房颤", "心房颤动", "atrial fibrillation"),
    "心房颤动": ("心房颤动", "房颤", "atrial fibrillation"),
    "房颤卒中": ("房颤中风", "atrial fibrillation stroke", "cha2ds2"),
    "房颤卒中风险": ("房颤中风危险", "atrial fibrillation stroke risk", "cha2ds2"),
    "肾功能": (
        "肾功能",
        "肾小球滤过率",
        "肌酐清除率",
        "egfr",
        "ckd-epi",
        "mdrd",
        "cockcroft",
    ),
    "renal function": (
        "renal function",
        "glomerular filtration rate",
        "creatinine clearance",
        "egfr",
        "ckd-epi",
        "mdrd",
        "cockcroft",
    ),
    "心梗": ("心梗", "心肌梗死", "myocardial infarction"),
    "心肌梗死": ("心肌梗死", "心梗", "myocardial infarction"),
    "肺栓塞": ("肺栓塞", "pulmonary embolism"),
}


def _normalize_search_text(value: str) -> str:
    """Normalize width, case, punctuation, and whitespace for search only."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", normalized)
    return " ".join(normalized.split())


def _query_groups(query: str) -> tuple[tuple[str, ...], ...]:
    """Return AND-ed query groups whose members are OR-ed search aliases."""

    normalized = _normalize_search_text(query)
    if not normalized:
        return ()
    if normalized in SEARCH_ALIASES:
        return (tuple(_normalize_search_text(item) for item in SEARCH_ALIASES[normalized]),)
    return tuple(
        tuple(_normalize_search_text(item) for item in SEARCH_ALIASES.get(token, (token,)))
        for token in normalized.split()
    )


def _matches_groups(haystack: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    return all(any(alias in haystack for alias in aliases) for aliases in groups)


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
        needle = _normalize_search_text(query)
        groups = _query_groups(query)
        if not groups:
            return []

        scored: list[tuple[int, str, CalculatorSkill]] = []
        for skill in self.skills:
            metadata = skill.metadata
            fields = (
                metadata.name_cn,
                metadata.name_en,
                metadata.category,
                metadata.subspecialty,
                metadata.scenario,
                metadata.purpose,
                metadata.source,
            )
            normalized_fields = tuple(_normalize_search_text(field) for field in fields)
            combined = " ".join(normalized_fields)
            if not _matches_groups(combined, groups):
                continue
            score = 100
            name_cn, name_en, category, subspecialty, scenario, purpose, source = normalized_fields
            if name_cn == needle or name_en == needle:
                score = 0
            elif name_cn.startswith(needle) or name_en.startswith(needle):
                score = 10
            elif needle in name_cn or needle in name_en:
                score = 20
            elif _matches_groups(f"{name_cn} {name_en}", groups):
                score = 30
            elif needle in scenario:
                score = 40
            elif _matches_groups(scenario, groups):
                score = 50
            elif _matches_groups(f"{category} {subspecialty}", groups):
                score = 60
            elif _matches_groups(purpose, groups):
                score = 80
            elif _matches_groups(source, groups):
                score = 90
            scored.append((score, metadata.name_cn, skill))

        scored.sort(key=lambda item: (item[0], item[1], item[2].metadata.id))
        matches = [skill for _, _, skill in scored]
        return matches[:limit] if limit is not None else matches

    def by_category(self, category: str) -> list[CalculatorSkill]:
        return [skill for skill in self.skills if skill.metadata.category == category]

    def categories(self) -> list[str]:
        return sorted({skill.metadata.category for skill in self.skills})

    def implemented(self) -> list[CalculatorSkill]:
        return [skill for skill in self.skills if skill.implemented]

    def runnable(self) -> list[CalculatorSkill]:
        """Return complete and partial entries with executable local logic."""
        return self.implemented()

    def backlog(self) -> list[CalculatorSkill]:
        """Return metadata-only and licensed entries that cannot run locally."""
        return [skill for skill in self.skills if not skill.implemented]

    def by_catalog_layer(self, layer: str) -> list[CalculatorSkill]:
        if layer not in CATALOG_LAYERS:
            raise ValueError(f"unknown catalog layer: {layer}")
        return [skill for skill in self.skills if skill.catalog_layer == layer]

    def automated_review_ready(self) -> list[CalculatorSkill]:
        """Return entries passing automated gates; clinician approval is separate."""
        return [skill for skill in self.skills if skill.medical_review_check().ok]

    def released(self) -> list[CalculatorSkill]:
        """Return only entries on the explicit clinician-approved release allowlist."""
        return [skill for skill in self.skills if skill.metadata.id in CLINICALLY_RELEASED_IDS]

    def search_runnable(self, query: str, limit: int | None = 20) -> list[CalculatorSkill]:
        runnable_ids = {skill.metadata.id for skill in self.runnable()}
        matches = self.search(query, limit=None)
        matches = [skill for skill in matches if skill.metadata.id in runnable_ids]
        return matches[:limit] if limit is not None else matches

    def search_layer(
        self, query: str, layer: str, limit: int | None = 20
    ) -> list[CalculatorSkill]:
        layer_ids = {skill.metadata.id for skill in self.by_catalog_layer(layer)}
        matches = [skill for skill in self.search(query, limit=None) if skill.metadata.id in layer_ids]
        return matches[:limit] if limit is not None else matches

    def search_released(self, query: str, limit: int | None = 20) -> list[CalculatorSkill]:
        released_ids = {skill.metadata.id for skill in self.released()}
        matches = self.search(query, limit=None)
        matches = [skill for skill in matches if skill.metadata.id in released_ids]
        return matches[:limit] if limit is not None else matches

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
            "metadata_only_rows": len(self.skills) - len(implemented),
            "implementation_levels": {
                level: sum(skill.implementation_level == level for skill in self.skills)
                for level in ("complete", "partial", "metadata_only", "licensed_rule")
            },
            "catalog_layers": {
                layer: sum(skill.catalog_layer == layer for skill in self.skills)
                for layer in CATALOG_LAYERS
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


def _pending_blockers() -> dict[str, str]:
    if not IMPLEMENTATION_STATUS_CSV.exists():
        return {}
    with IMPLEMENTATION_STATUS_CSV.open(encoding="utf-8-sig", newline="") as f:
        return {row["id"]: row.get("pending_blocker_type", "") for row in csv.DictReader(f)}


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
    calculator_id: str, implementation: object | None, required_inputs: tuple[str, ...], blockers: dict[str, str]
) -> str:
    if implementation is None:
        return "licensed_rule" if blockers.get(calculator_id) in LICENSED_BLOCKERS else "metadata_only"
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


def _catalog_layer(implementation: object | None, blocker: str) -> str:
    if implementation is not None:
        return "executable"
    if blocker in GUIDANCE_KNOWLEDGE_BLOCKERS:
        return "guidance_knowledge"
    if blocker in CONTROLLED_CONTENT_BLOCKERS:
        return "controlled_content"
    return "source_candidate"


def load_registry(
    csv_path: str | Path | None = None,
    *,
    custom_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
    include_custom: bool = True,
) -> CalculatorRegistry:
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    blockers = _pending_blockers()
    aliases = _calculator_aliases(path)
    skills: list[CalculatorSkill] = []
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
            implementation_module = implementation.__module__ if implementation else ""
            level = _implementation_level(metadata.id, implementation, required_inputs, blockers)
            blocker = blockers.get(metadata.id, "")
            skills.append(
                CalculatorSkill(
                    metadata,
                    implementation,
                    required_inputs,
                    implementation_module,
                    level,
                    catalog_layer=_catalog_layer(implementation, blocker),
                    pending_blocker_type=blocker,
                )
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
                    "executable",
                )
            )
    return CalculatorRegistry(skills, aliases, inventory_rows)
