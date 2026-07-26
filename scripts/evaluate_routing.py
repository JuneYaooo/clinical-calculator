#!/usr/bin/env python3
"""Evaluate deterministic calculator routing against the checked-in case set."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clinical_calculators import load_registry  # noqa: E402


DEFAULT_CASES = ROOT / "evaluation" / "routing_cases.csv"
DEFAULT_REPORT = ROOT / "reports" / "routing_evaluation.json"
REQUIRED_COLUMNS = ("query", "expected_ids", "locale", "category", "critical", "note")
VALID_CATEGORIES = {"direct", "synonym", "abbrev", "scenario", "partial"}


def load_cases(path: str | Path = DEFAULT_CASES) -> list[dict[str, object]]:
    case_path = Path(path)
    with case_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise ValueError(f"routing cases missing columns: {', '.join(missing)}")
        cases: list[dict[str, object]] = []
        for line_number, row in enumerate(reader, start=2):
            query = row.get("query", "").strip()
            expected_ids = tuple(
                dict.fromkeys(
                    item.strip()
                    for item in row.get("expected_ids", "").split(";")
                    if item.strip()
                )
            )
            locale = row.get("locale", "").strip()
            category = row.get("category", "").strip()
            critical = row.get("critical", "").strip()
            note = row.get("note", "").strip()
            if not query or not expected_ids or not locale or not category or not critical or not note:
                raise ValueError(f"routing case row {line_number} has an empty required value")
            if category not in VALID_CATEGORIES:
                raise ValueError(
                    f"routing case row {line_number} category must be one of: "
                    f"{', '.join(sorted(VALID_CATEGORIES))}"
                )
            if critical not in {"yes", "no"}:
                raise ValueError(
                    f"routing case row {line_number} critical must be yes or no"
                )
            expected_inputs = tuple(
                item.strip()
                for item in row.get("expected_inputs", "").split(";")
                if item.strip()
            )
            cases.append(
                {
                    "query": query,
                    "expected_ids": expected_ids,
                    "locale": locale,
                    "category": category,
                    "critical": critical,
                    "note": note,
                    "expected_inputs": expected_inputs,
                }
            )
    return cases


def evaluate_cases(cases: Iterable[dict[str, object]]) -> dict[str, object]:
    registry = load_registry()
    known_ids = {skill.metadata.id for skill in registry.skills}
    evaluated: list[dict[str, object]] = []
    critical_evaluated: list[dict[str, object]] = []
    for case in cases:
        expected_ids = tuple(str(item) for item in case["expected_ids"])
        unknown = sorted(set(expected_ids) - known_ids)
        if unknown:
            raise ValueError(
                f"routing case {case['query']!r} references unknown canonical IDs: {', '.join(unknown)}"
            )
        expected_inputs = tuple(str(item) for item in case.get("expected_inputs", ()))
        if expected_inputs:
            for calculator_id in expected_ids:
                actual_inputs = registry.get(calculator_id).required_inputs
                if actual_inputs != expected_inputs:
                    raise ValueError(
                        f"routing case {case['query']!r} expected_inputs mismatch for "
                        f"{calculator_id}: expected {expected_inputs}, got {actual_inputs}"
                    )

        matches = registry.search(str(case["query"]), limit=None)
        result_ids = [skill.metadata.id for skill in matches]
        expected = set(expected_ids)
        relevant_rank = next(
            (rank for rank, calculator_id in enumerate(result_ids, start=1) if calculator_id in expected),
            None,
        )
        result = {
            "query": case["query"],
            "expected_ids": list(expected_ids),
            "locale": case["locale"],
            "category": case["category"],
            "top_ids": result_ids[:5],
            "relevant_rank": relevant_rank,
            "zero_results": not result_ids,
        }
        evaluated.append(result)
        if case["critical"] == "yes":
            critical_evaluated.append(result)

    report = {
        **_metrics(evaluated),
        "critical_recall_at_1": _metrics(critical_evaluated)["recall_at_1"],
        "critical_case_count": len(critical_evaluated),
        "critical_failures": [
            item for item in critical_evaluated if item["relevant_rank"] != 1
        ],
        "by_category": _group_metrics(evaluated, "category"),
        "by_locale": _group_metrics(evaluated, "locale"),
        "failures": [
            item for item in evaluated if item["relevant_rank"] is None or item["relevant_rank"] > 5
        ],
    }
    return report


def _metrics(evaluated: list[dict[str, object]]) -> dict[str, object]:
    count = len(evaluated)
    if not count:
        return {
            "case_count": 0,
            "recall_at_1": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "zero_result_rate": 0.0,
        }
    reciprocal_ranks = [
        1 / int(item["relevant_rank"]) if item["relevant_rank"] is not None else 0
        for item in evaluated
    ]
    return {
        "case_count": count,
        "recall_at_1": round(
            sum(item["relevant_rank"] == 1 for item in evaluated) / count, 6
        ),
        "recall_at_5": round(
            sum(
                item["relevant_rank"] is not None and int(item["relevant_rank"]) <= 5
                for item in evaluated
            )
            / count,
            6,
        ),
        "mrr": round(sum(reciprocal_ranks) / count, 6),
        "zero_result_rate": round(sum(item["zero_results"] for item in evaluated) / count, 6),
    }


def _group_metrics(
    evaluated: list[dict[str, object]], key: str
) -> dict[str, dict[str, object]]:
    return {
        str(value): _metrics([item for item in evaluated if item[key] == value])
        for value in sorted({item[key] for item in evaluated})
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    report = evaluate_cases(load_cases(args.cases))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
