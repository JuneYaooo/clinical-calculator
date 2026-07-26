from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_routing import evaluate_cases, load_cases


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reports" / "routing_baseline.json"
RATCHET_MESSAGE = "路由质量不得倒退，如确为有意变更请同步更新基线文件"


def test_routing_case_set_is_large_and_categorized():
    cases = load_cases()
    assert len(cases) >= 120
    assert {case["category"] for case in cases} == {"direct", "synonym"}


def test_routing_quality_does_not_regress():
    current = evaluate_cases(load_cases())
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert current["recall_at_1"] >= baseline["recall_at_1"], RATCHET_MESSAGE
    assert current["recall_at_5"] >= baseline["recall_at_5"], RATCHET_MESSAGE
    assert current["zero_result_rate"] <= baseline["zero_result_rate"], RATCHET_MESSAGE
