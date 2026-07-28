from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

from clinical_calculators.registry import load_registry
from clinical_calculators.search import load_search_aliases, tokenize_search_text


ROOT = Path(__file__).resolve().parents[1]


def test_cha2ds2_notation_variants_share_compact_tokens():
    variants = (
        tokenize_search_text("CHA（2）DS（2）-VASc"),
        tokenize_search_text("CHA₂DS₂-VASc"),
        tokenize_search_text("cha2ds2 vasc"),
    )
    assert all("cha2ds2vasc" in tokens for tokens in variants)
    assert all("chadsvasc" in tokens for tokens in variants)


def test_latin_camel_case_boundaries_produce_additional_tokens():
    tokens = tokenize_search_text("renalRiskScore")
    assert {"renalriskscore", "renal", "risk", "score"} <= set(tokens)


def test_search_index_is_built_once_and_exposes_match_details():
    registry = load_registry()
    index_identity = id(registry._search_index)

    response = registry.search_detailed("chads vasc")
    matches = response.skills

    assert id(registry._search_index) == index_identity
    assert matches[0].metadata.id == "CALC-0049"
    match = response.match_for("CALC-0049")
    assert match is not None
    assert match.coverage == 1.0
    assert "name_en" in match.matched_fields
    assert "chadsvasc" in match.matched_terms


@pytest.mark.parametrize(
    ("query", "expected_id"),
    (
        ("肺栓塞概率", "CALC-0051"),
        ("脓毒症", "CALC-0004"),
        ("小儿脱水", "CALC-0513"),
        ("预测死亡率的评分", "CALC-0212"),
        ("chads vasc", "CALC-0049"),
    ),
)
def test_previously_failing_queries_route(query, expected_id):
    registry = load_registry()
    assert expected_id in {skill.metadata.id for skill in registry.search(query, limit=5)}


def test_no_match_cli_has_status_and_suggestions():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "clinical_calculator.py"),
            "search",
            "完全不存在的东西xyz",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["status"] == "no_match"
    assert payload["results"] == []
    assert len(payload["suggestions"]) <= 5


def test_clinical_scenario_routes_only_to_executable_calculators():
    registry = load_registry()

    response = registry.search_detailed("脓毒症")
    assert response.status == "ok"
    assert [skill.metadata.id for skill in response.skills] == ["CALC-0004", "CALC-0009"]
    assert all(skill.implemented for skill in response.skills)


def test_search_alias_validation_rejects_self_loop_and_duplicate_term(tmp_path):
    path = tmp_path / "terms.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("term", "expands_to", "note"))
        writer.writerow(("房颤", "房颤", "self loop"))
    with pytest.raises(ValueError, match="cannot expand to itself"):
        load_search_aliases(path)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("term", "expands_to", "note"))
        writer.writerow(("房颤", "心房颤动", "first"))
        writer.writerow(("房颤", "atrial fibrillation", "duplicate"))
    with pytest.raises(ValueError, match="duplicate search term"):
        load_search_aliases(path)
