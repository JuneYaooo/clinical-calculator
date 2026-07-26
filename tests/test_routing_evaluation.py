from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_routing import VALID_CATEGORIES, evaluate_cases, load_cases


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reports" / "routing_baseline.json"
HELDOUT_CASES = ROOT / "evaluation" / "routing_cases_heldout.csv"
RATCHET_MESSAGE = "路由质量不得低于预留门槛"
REQUIRED_CRITICAL_QUERIES = {
    "肺栓塞概率",
    "脓毒症",
    "小儿脱水",
    "预测死亡率的评分",
    "chads vasc",
    "Wells DVT",
    "Wells PE",
    "CHA（2）DS（2）-VASc",
    "CHA₂DS₂-VASc",
    "cha2ds2vasc",
    "qSOFA",
}


def test_routing_case_set_is_large_and_categorized():
    cases = load_cases()
    assert len(cases) >= 120
    assert {case["category"] for case in cases} <= VALID_CATEGORIES


def test_routing_quality_does_not_regress():
    current = evaluate_cases(load_cases())
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    thresholds = baseline["thresholds"]

    assert current["recall_at_1"] >= thresholds["recall_at_1"], RATCHET_MESSAGE
    assert current["recall_at_5"] >= thresholds["recall_at_5"], RATCHET_MESSAGE
    assert current["mrr"] >= thresholds["mrr"], RATCHET_MESSAGE
    assert current["zero_result_rate"] <= thresholds["zero_result_rate"], RATCHET_MESSAGE


def test_critical_routing_cases_remain_top_1():
    current = evaluate_cases(load_cases())

    # 失败信息和指标必须来自同一次评测结果，否则两条独立的检索路径可能给出
    # 互相矛盾的报告（指标说掉了，点名的用例却在 rank 1）。
    failure_message = "掉落的 critical 用例:\n" + "\n".join(
        f"query={item['query']!r}, expected_ids={item['expected_ids']}, "
        f"relevant_rank={item['relevant_rank']}, top_ids={item['top_ids']}"
        for item in current["critical_failures"]
    )
    assert current["critical_recall_at_1"] == 1.0, failure_message


def test_required_queries_cannot_be_removed_from_critical_subset():
    critical_queries = {
        str(case["query"]) for case in load_cases() if case["critical"] == "yes"
    }
    assert REQUIRED_CRITICAL_QUERIES <= critical_queries


def test_heldout_routing_quality_meets_thresholds():
    cases = load_cases(HELDOUT_CASES)
    current = evaluate_cases(cases)
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    thresholds = baseline["heldout_thresholds"]

    assert len(cases) == 30
    assert {case["category"] for case in cases} <= VALID_CATEGORIES
    assert current["recall_at_1"] >= thresholds["recall_at_1"], RATCHET_MESSAGE
    assert current["recall_at_5"] >= thresholds["recall_at_5"], RATCHET_MESSAGE
    assert current["mrr"] >= thresholds["mrr"], RATCHET_MESSAGE
    assert current["zero_result_rate"] <= thresholds["zero_result_rate"], RATCHET_MESSAGE
