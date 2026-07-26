#!/usr/bin/env python3
"""JSON CLI for the clinical-calculator skill and its custom extensions."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clinical_calculators import ManifestError, load_custom_manifest, load_registry  # noqa: E402
from clinical_calculators.extensions import DEFAULT_CUSTOM_DIR  # noqa: E402


IMPLEMENTATION_STATUS_REPORT = ROOT / "reports" / "calculator_implementation_status.csv"
SOURCE_CANDIDATE_PRIORITIES = {
    "formula_audit_needed": {
        "priority_tier": 1,
        "data_needed": "公开的逐项计分规则、适用人群、版本和至少两个已知答案",
        "next_action": "定位原始文献或官方规则，逐项审计本地元数据后实现并做边界测试",
        "suggested_structure": "formula、formula_set 或 decision_tree",
    },
    "formula_missing": {
        "priority_tier": 2,
        "data_needed": "完整公式、变量定义、单位、截断规则、版本和已知答案",
        "next_action": "从官方计算器或原始论文回源提取完整公式，不从名称反推",
        "suggested_structure": "formula、formula_set 或 Python",
    },
    "reference_tables_needed": {
        "priority_tier": 3,
        "data_needed": "可再分发的完整参考表、分层维度、边界、版本和校验样例",
        "next_action": "确认数据授权并提取全表；仅离散匹配时使用多维查表",
        "suggested_structure": "multidimensional_lookup；需要插值时使用 Python",
    },
    "model_coefficients_needed": {
        "priority_tier": 4,
        "data_needed": "所有分层系数、基线风险、变量变换、上下限、适用人群和校准版本",
        "next_action": "定位模型附录或官方代码，核对系数集与模型版本后实现",
        "suggested_structure": "formula_set 或经过来源审计的 Python 模型",
    },
    "chart_digitization_needed": {
        "priority_tier": 5,
        "data_needed": "权威数值表或公开公式；若仅有图形还需数字化误差与边界验证",
        "next_action": "优先寻找原始数值表/公式，无法取得时评估是否应继续保留为候选",
        "suggested_structure": "multidimensional_lookup；需要插值时使用 Python",
    },
    "manual_research_needed": {
        "priority_tier": 6,
        "data_needed": "可追溯的一手来源、计算规则类型、输入输出、版本及可验证样例",
        "next_action": "先做定向来源检索和可执行性判断，再决定公式、查表或移出计算器候选",
        "suggested_structure": "待回源判断",
    },
}


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def skill_summary(skill: Any, match: Any = None) -> dict[str, Any]:
    summary = {
        "id": skill.metadata.id,
        "name_cn": skill.metadata.name_cn,
        "name_en": skill.metadata.name_en,
        "category": skill.metadata.category,
        "scenario": skill.metadata.scenario,
        "implementation_level": skill.implementation_level,
        "catalog_layer": skill.catalog_layer,
        "pending_blocker_type": skill.pending_blocker_type,
        "runnable": skill.implemented,
        "clinically_released": skill.metadata.id in {item.metadata.id for item in skill_registry.released()},
    }
    if match is not None:
        summary["match"] = match.as_dict()
    return summary


def compact_registry_summary(registry: Any) -> dict[str, Any]:
    summary = registry.summary()
    summary.pop("implemented_names", None)
    return summary


def resolve(registry: Any, identifier: str) -> Any:
    try:
        return registry.get(identifier)
    except KeyError:
        pass
    exact = [
        skill
        for skill in registry.skills
        if skill.metadata.name_en.casefold() == identifier.casefold()
    ]
    if not exact:
        raise KeyError(identifier)
    if len(exact) > 1:
        raise ValueError(
            f"ambiguous calculator name; use one of these IDs: {', '.join(item.metadata.id for item in exact)}"
        )
    return exact[0]


def resolve_unambiguous(registry: Any, identifier: str) -> Any:
    if identifier in {skill.metadata.id for skill in registry.skills}:
        return registry.get(identifier)
    chinese = registry.get_all(identifier)
    if len(chinese) > 1:
        raise ValueError(
            f"ambiguous calculator name; use one of these IDs: {', '.join(item.metadata.id for item in chinese)}"
        )
    return chinese[0] if chinese else resolve(registry, identifier)


def parse_assignment(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise ValueError(f"input must use key=value syntax: {raw}")
    key, text = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError("input name cannot be empty")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = text
    return key, value


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--custom-dir",
        action="append",
        default=[],
        help="additional custom manifest directory (repeatable)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="show registry coverage")

    search = subparsers.add_parser("search", help="search names, specialties, scenarios, and sources")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search_scope = search.add_mutually_exclusive_group()
    search_scope.add_argument(
        "--runnable",
        action="store_true",
        help="show only locally executable entries (the default)",
    )
    search_scope.add_argument(
        "--all",
        action="store_true",
        help="include pending, guidance, and controlled-content entries",
    )
    search_scope.add_argument(
        "--layer",
        choices=("executable", "source_candidate", "guidance_knowledge", "controlled_content"),
        help="search one catalog layer",
    )

    info = subparsers.add_parser("info", help="show metadata and exact input contract")
    info.add_argument("calculator")

    run = subparsers.add_parser("run", help="run a calculator by ID or unambiguous exact name")
    run.add_argument("calculator")
    run.add_argument("--input", action="append", default=[], metavar="KEY=VALUE")

    subparsers.add_parser("validate", help="validate the registry and all discovered custom manifests")

    backlog = subparsers.add_parser(
        "backlog", help="rank source-candidate calculators for evidence retrieval"
    )
    backlog.add_argument("--limit", type=int, default=50)
    backlog.add_argument(
        "--blocker",
        choices=tuple(SOURCE_CANDIDATE_PRIORITIES),
        help="show only one evidence blocker type",
    )

    validate_custom = subparsers.add_parser("validate-custom", help="validate one custom manifest")
    validate_custom.add_argument("path", type=Path)

    scaffold = subparsers.add_parser("scaffold", help="create an editable custom calculator manifest")
    scaffold.add_argument("--output", type=Path, required=True)
    scaffold.add_argument("--id", required=True)
    scaffold.add_argument("--name-cn", required=True)
    scaffold.add_argument("--name-en", required=True)
    scaffold.add_argument(
        "--kind",
        choices=("formula", "multi-formula", "lookup", "multi-lookup", "decision-tree"),
        default="formula",
        help="declarative calculator type",
    )

    install = subparsers.add_parser("install-custom", help="validate and copy a manifest into a custom directory")
    install.add_argument("manifest", type=Path)
    install.add_argument("--destination", type=Path, default=DEFAULT_CUSTOM_DIR)
    return parser


def scaffold_payload(args: argparse.Namespace) -> dict[str, Any]:
    common = {
        "schema_version": 2,
        "id": args.id,
        "category": "待填写专业",
        "subspecialty": "",
        "scenario": "待填写使用场景",
        "name_cn": args.name_cn,
        "name_en": args.name_en,
        "purpose": "待填写用途",
        "clinical_note": "仅作决策支持；临床使用前须独立核对公式、版本和适用人群。",
        "source": {
            "type": "publication",
            "name": "替换为具体指南或原始文献",
            "url": "https://example.org/replace-with-specific-source",
            "version": "替换为版本或年份",
            "evidence_tier": "custom; requires review",
        },
    }
    if args.kind == "multi-formula":
        return {
            **common,
            "inputs": [
                {
                    "name": "base_value",
                    "type": "number",
                    "unit": "1",
                    "minimum": 0,
                    "description": "示例输入；替换为来源定义的变量",
                }
            ],
            "outputs": [
                {"name": "score", "unit": "points", "round": 0},
                {"name": "risk_percent", "unit": "%", "round": 1},
            ],
            "calculation": {
                "type": "formula_set",
                "expressions": {
                    "score": "base_value * 2",
                    "risk_percent": "base_value * 10",
                },
            },
            "interpretation": [
                {"when": "risk_percent >= 50", "text": "示例较高分层"}
            ],
            "default_interpretation": "示例较低分层",
            "test_cases": [
                {
                    "name": "示例多输出",
                    "inputs": {"base_value": 5},
                    "expected_values": {"score": 10, "risk_percent": 50},
                    "expected_interpretation": "示例较高分层",
                }
            ],
        }
    if args.kind == "multi-lookup":
        return {
            **common,
            "inputs": [
                {
                    "name": "sex",
                    "type": "choice",
                    "choices": ["male", "female"],
                    "description": "示例精确匹配维度",
                },
                {
                    "name": "age_years",
                    "type": "number",
                    "unit": "years",
                    "minimum": 0,
                    "maximum": 120,
                    "description": "示例区间维度",
                },
                {
                    "name": "weight_kg",
                    "type": "number",
                    "unit": "kg",
                    "minimum": 0,
                    "exclusive_minimum": True,
                    "description": "示例区间维度",
                },
            ],
            "outputs": [
                {"name": "score", "unit": "points", "round": 0},
                {"name": "risk_percent", "unit": "%", "round": 1},
            ],
            "calculation": {
                "type": "multidimensional_lookup",
                "dimensions": [
                    {"input": "sex", "match": "exact"},
                    {"input": "age_years", "match": "range"},
                    {"input": "weight_kg", "match": "range"},
                ],
                "rows": [
                    {
                        "keys": {
                            "sex": "male",
                            "age_years": {
                                "minimum": 18,
                                "maximum": 65,
                                "include_maximum": True,
                            },
                            "weight_kg": {
                                "minimum": 40,
                                "maximum": 120,
                                "include_maximum": True,
                            },
                        },
                        "values": {"score": 1, "risk_percent": 2.5},
                        "interpretation": "示例查表行",
                    }
                ],
            },
            "interpretation": [],
            "default_interpretation": "未匹配查表行",
            "test_cases": [
                {
                    "name": "示例多维边界",
                    "inputs": {"sex": "male", "age_years": 65, "weight_kg": 120},
                    "expected_values": {"score": 1, "risk_percent": 2.5},
                    "expected_interpretation": "示例查表行",
                }
            ],
        }
    if args.kind == "lookup":
        return {
            **common,
            "inputs": [
                {
                    "name": "risk_score",
                    "type": "number",
                    "unit": "points",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "需要查表的分值",
                }
            ],
            "output": {"unit": "category", "round": 0},
            "calculation": {
                "type": "lookup_table",
                "input": "risk_score",
                "match": "range",
                "rows": [
                    {
                        "maximum": 10,
                        "include_maximum": False,
                        "value": 0,
                        "interpretation": "示例低分层",
                    },
                    {
                        "minimum": 10,
                        "maximum": 100,
                        "include_minimum": True,
                        "include_maximum": True,
                        "value": 1,
                        "interpretation": "示例高分层",
                    },
                ],
            },
            "interpretation": [],
            "default_interpretation": "未匹配查表行",
            "test_cases": [
                {
                    "name": "示例边界",
                    "inputs": {"risk_score": 10},
                    "expected_value": 1,
                    "expected_interpretation": "示例高分层",
                }
            ],
        }
    if args.kind == "decision-tree":
        return {
            **common,
            "inputs": [
                {"name": "high_risk_feature", "type": "boolean", "description": "高危特征"},
                {
                    "name": "score",
                    "type": "number",
                    "unit": "points",
                    "minimum": 0,
                    "description": "示例分值",
                },
            ],
            "output": {"unit": "decision code", "round": 0},
            "calculation": {
                "type": "decision_tree",
                "rules": [
                    {
                        "when": "high_risk_feature or score >= 5",
                        "value": 1,
                        "interpretation": "示例阳性分支",
                    }
                ],
                "default": {"value": 0, "interpretation": "示例阴性分支"},
            },
            "interpretation": [],
            "default_interpretation": "未匹配分支",
            "test_cases": [
                {
                    "name": "示例阳性",
                    "inputs": {"high_risk_feature": True, "score": 0},
                    "expected_value": 1,
                    "expected_interpretation": "示例阳性分支",
                }
            ],
        }
    return {
        **common,
        "inputs": [
            {
                "name": "weight_kg",
                "type": "number",
                "unit": "kg",
                "minimum": 0,
                "exclusive_minimum": True,
                "description": "体重",
            },
            {
                "name": "height_cm",
                "type": "number",
                "unit": "cm",
                "minimum": 0,
                "exclusive_minimum": True,
                "description": "身高",
            },
        ],
        "output": {"unit": "kg/m^2", "round": 2},
        "calculation": {
            "type": "formula",
            "expression": "weight_kg / ((height_cm / 100) ** 2)",
        },
        "interpretation": [
            {"when": "value < 18.5", "text": "低于常用成人参考范围"},
            {"when": "value < 24", "text": "处于示例参考范围"},
        ],
        "default_interpretation": "高于示例参考范围",
        "test_cases": [
            {
                "name": "示例BMI",
                "inputs": {"weight_kg": 70, "height_cm": 175},
                "expected_value": 22.86,
                "tolerance": 0,
            }
        ],
    }


def source_candidate_backlog(blocker: str | None, limit: int) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("--limit must be greater than zero")
    try:
        with IMPLEMENTATION_STATUS_REPORT.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ValueError(f"cannot read implementation status report: {exc}") from exc

    candidates = [
        row
        for row in rows
        if row.get("pending_blocker_type") in SOURCE_CANDIDATE_PRIORITIES
        and (blocker is None or row.get("pending_blocker_type") == blocker)
    ]
    candidates.sort(
        key=lambda row: (
            SOURCE_CANDIDATE_PRIORITIES[row["pending_blocker_type"]]["priority_tier"],
            row["id"],
        )
    )
    queue = []
    for rank, row in enumerate(candidates, 1):
        guidance = SOURCE_CANDIDATE_PRIORITIES[row["pending_blocker_type"]]
        queue.append(
            {
                "rank": rank,
                "priority_tier": guidance["priority_tier"],
                "id": row["id"],
                "name_cn": row["中文名称"],
                "name_en": row["英文名称"],
                "blocker": row["pending_blocker_type"],
                "source": row["来源/指南"],
                "source_url": row["来源链接"],
                "data_needed": guidance["data_needed"],
                "next_action": guidance["next_action"],
                "suggested_structure": guidance["suggested_structure"],
            }
        )
    return {
        "source": str(IMPLEMENTATION_STATUS_REPORT),
        "blocker": blocker,
        "candidate_count": len(candidates),
        "returned_count": min(len(queue), limit),
        "queue": queue[:limit],
    }


def ensure_custom_source_is_final(definition: Any) -> None:
    metadata = definition.metadata
    source_text = " ".join(
        (metadata.source, metadata.source_url, metadata.version)
    ).casefold()
    markers = ("replace-with", "replace with", "placeholder", "待填写")
    if any(marker in source_text for marker in markers):
        raise ManifestError(
            "refusing to install a draft with placeholder source metadata; "
            "record the exact source and version first"
        )


def main() -> int:
    global skill_registry
    parser = make_parser()
    args = parser.parse_args()
    try:
        if args.command == "validate-custom":
            definition = load_custom_manifest(args.path)
            emit({"ok": True, "id": definition.metadata.id, "path": str(definition.manifest_path)})
            return 0

        if args.command == "scaffold":
            if args.output.exists():
                raise ValueError(f"refusing to overwrite existing file: {args.output}")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(scaffold_payload(args), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            emit(
                {
                    "ok": True,
                    "path": str(args.output),
                    "next": "replace placeholders and verify calculation/test_cases, then run validate-custom",
                }
            )
            return 0

        if args.command == "backlog":
            emit(source_candidate_backlog(args.blocker, args.limit))
            return 0

        if args.command == "install-custom":
            definition = load_custom_manifest(args.manifest)
            ensure_custom_source_is_final(definition)
            args.destination.mkdir(parents=True, exist_ok=True)
            destination = args.destination / f"{definition.metadata.id.lower()}.json"
            if destination.exists():
                raise ValueError(f"refusing to overwrite installed manifest: {destination}")
            shutil.copy2(args.manifest, destination)
            try:
                load_registry(custom_dirs=[args.destination])
            except Exception:
                destination.unlink(missing_ok=True)
                raise
            emit({"ok": True, "id": definition.metadata.id, "installed": str(destination)})
            return 0

        skill_registry = load_registry(custom_dirs=args.custom_dir)
        if args.command == "summary":
            emit(compact_registry_summary(skill_registry))
            return 0
        if args.command == "search":
            if args.all:
                matches = skill_registry.search(args.query, args.limit)
                scope = "all"
            elif args.layer:
                matches = skill_registry.search_layer(args.query, args.layer, args.limit)
                scope = args.layer
            else:
                matches = skill_registry.search_runnable(args.query, args.limit)
                scope = "executable"
            search_response = skill_registry.search_response()
            emit(
                {
                    "query": args.query,
                    "scope": scope,
                    "status": search_response.status,
                    "count": len(matches),
                    "results": [
                        skill_summary(item, skill_registry.search_match(item.metadata.id))
                        for item in matches
                    ],
                    "suggestions": list(search_response.suggestions),
                }
            )
            return 0
        if args.command == "info":
            skill = resolve_unambiguous(skill_registry, args.calculator)
            emit(
                {
                    **skill_summary(skill),
                    "metadata": asdict(skill.metadata),
                    "required_inputs": [asdict(spec) for spec in skill.input_schema],
                    "medical_review": asdict(skill.medical_review_check()),
                }
            )
            return 0
        if args.command == "run":
            skill = resolve_unambiguous(skill_registry, args.calculator)
            supplied: dict[str, Any] = {}
            for item in args.input:
                key, value = parse_assignment(item)
                if key in supplied:
                    raise ValueError(f"input supplied more than once: {key}")
                supplied[key] = value
            known = set(skill.required_inputs)
            unknown = sorted(set(supplied) - known)
            if unknown:
                raise ValueError(f"unknown inputs for {skill.metadata.id}: {', '.join(unknown)}")
            result = skill.run(supplied)
            emit(
                {
                    "calculator": skill_summary(skill),
                    "formula": skill.metadata.formula,
                    "source_url": skill.metadata.source_url,
                    "result": asdict(result),
                }
            )
            return 0 if result.status not in {"missing_inputs", "invalid_inputs", "needs_formula_implementation"} else 2
        if args.command == "validate":
            failures = [
                {"id": skill.metadata.id, "errors": skill.self_check().errors}
                for skill in skill_registry.skills
                if not skill.self_check().ok
            ]
            emit({"ok": not failures, "summary": compact_registry_summary(skill_registry), "failures": failures})
            return 0 if not failures else 1
    except (ManifestError, KeyError, ValueError, OSError) as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    return 0


skill_registry: Any = None


if __name__ == "__main__":
    raise SystemExit(main())
