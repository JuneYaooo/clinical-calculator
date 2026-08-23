from __future__ import annotations

import pytest

from clinical_calculators import calculate_selected, recommend_for_case
from clinical_calculators.workbench import (
    detect_case_intents,
    detect_privacy_risks,
    extract_case_values,
)


def test_case_extraction_only_uses_explicit_values():
    values = extract_case_values(
        "74岁男性，房颤。\n"
        "hypertension=true\n"
        "diabetes=false\n"
        "体重 72 kg，身高 175 cm"
    )

    assert values == {
        "age_years": 74.0,
        "weight_kg": 72.0,
        "height_cm": 175.0,
        "sex": "male",
        "hypertension": True,
        "diabetes": False,
    }
    assert "stroke_tia_thromboembolism" not in values


def test_privacy_detector_reports_categories_without_echoing_values():
    warnings = detect_privacy_risks("姓名：某某，联系电话：13812345678")

    assert "疑似手机号码" in warnings
    assert "疑似直接身份字段" in warnings
    assert all("13812345678" not in warning for warning in warnings)


def test_recommendation_exposes_evidence_inputs_and_audit_log():
    payload = recommend_for_case(
        "房颤 卒中风险",
        "74岁男性\nhypertension=true\ndiabetes=false",
        limit=3,
    )

    assert payload["status"] == "ok"
    assert payload["scope"] == "local_evidence_catalog"
    assert payload["candidates"][0]["id"] == "CALC-0049"
    candidate = payload["candidates"][0]
    assert candidate["evidence"]["source_url"].startswith("http")
    assert candidate["formula"]
    assert "stroke_tia_thromboembolism" in candidate["missing_inputs"]
    assert "hypertension" not in candidate["missing_inputs"]
    assert [item["event"] for item in payload["audit_log"]] == [
        "case_received",
        "values_extracted",
        "case_intents_detected",
        "catalog_searched",
    ]


def test_case_only_discovers_relevant_assessment_directions():
    payload = recommend_for_case(
        "",
        "74岁男性，非瓣膜性房颤，有高血压和既往脑卒中，无糖尿病。",
        limit=4,
    )

    assert payload["mode"] == "case_driven"
    assert [item["label"] for item in payload["detected_intents"]] == [
        "房颤相关卒中风险",
        "房颤抗凝相关出血风险",
    ]
    assert [item["id"] for item in payload["candidates"][:2]] == [
        "CALC-0049",
        "CALC-0057",
    ]
    assert payload["extracted_values"]["hypertension"] is True
    assert payload["extracted_values"]["diabetes"] is False
    assert payload["extracted_values"]["stroke_tia_thromboembolism"] is True
    assert payload["candidates"][0]["recommendation_reasons"]


def test_case_only_can_surface_multiple_independent_assessments():
    case_text = (
        "68岁，发热咳嗽，肺炎，呼吸频率32次/分，"
        "血压88/56 mmHg，意识模糊。"
    )
    payload = recommend_for_case("", case_text, limit=4)

    assert [item["label"] for item in payload["detected_intents"]] == [
        "肺炎严重度",
        "感染相关病情恶化风险",
    ]
    assert [item["id"] for item in payload["candidates"][:2]] == [
        "CALC-0091",
        "CALC-0009",
    ]
    assert {
        key: payload["extracted_values"][key]
        for key in (
            "age_years",
            "respiratory_rate",
            "systolic_bp",
            "diastolic_bp",
            "altered_mentation",
            "confusion",
        )
    } == {
        "age_years": 68.0,
        "respiratory_rate": 32.0,
        "systolic_bp": 88.0,
        "diastolic_bp": 56.0,
        "altered_mentation": True,
        "confusion": True,
    }


def test_case_intent_detection_does_not_guess_without_supported_cues():
    assert detect_case_intents("患者复诊，暂无明确诊断或评估目标。") == []
    payload = recommend_for_case("", "患者复诊，暂无明确诊断或评估目标。")
    assert payload["status"] == "no_match"
    assert payload["candidates"] == []


def test_selected_calculation_includes_snapshot_formula_source_and_trace():
    payload = calculate_selected(
        {
            "CALC-0049": {
                "congestive_heart_failure": False,
                "hypertension": True,
                "age_years": 74,
                "diabetes": False,
                "stroke_tia_thromboembolism": True,
                "vascular_disease": False,
                "sex": "male",
                "ignored_patient_name": "must not enter snapshot",
            }
        },
        session_id="test-session",
    )

    assert payload["status"] == "completed"
    assert payload["session_id"] == "test-session"
    run = payload["runs"][0]
    assert run["status"] == "implemented"
    assert run["value"] == 4
    assert run["input_snapshot"]["age_years"] == 74
    assert "ignored_patient_name" not in run["input_snapshot"]
    display_inputs = {
        item["label"]: item["display_value"] for item in run["input_display"]
    }
    assert {key: display_inputs[key] for key in (
        "年龄",
        "高血压",
        "糖尿病",
        "卒中、TIA 或血栓栓塞史",
    )} == {
        "年龄": "74 岁",
        "高血压": "是",
        "糖尿病": "否",
        "卒中、TIA 或血栓栓塞史": "是",
    }
    assert run["status_label"] == "计算完成"
    assert "卒中风险较高" in run["clinical_explanation"]
    assert run["review"]["label"] == "使用前需核对来源与版本"
    assert all("missing source" not in gap for gap in run["review"]["gaps"])
    assert run["formula"]
    assert run["source"]["url"].startswith("http")
    assert [step["kind"] for step in run["trace"]] == [
        "input",
        "validation",
        "formula",
        "result",
    ]


def test_missing_selected_inputs_remain_visible_in_result():
    payload = calculate_selected(
        {"CALC-0009": {"respiratory_rate": 24}},
        session_id="missing-session",
    )

    assert payload["status"] == "needs_input"
    run = payload["runs"][0]
    assert run["status"] == "missing_inputs"
    assert set(run["required_inputs"]) == {"systolic_bp", "altered_mentation"}


def test_malformed_workbench_payloads_are_rejected_as_user_errors():
    with pytest.raises(ValueError, match="候选数量必须是整数"):
        recommend_for_case("房颤", limit="many")

    with pytest.raises(ValueError, match="输入必须是对象"):
        calculate_selected({"CALC-0049": [1, 2, 3]})
