from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _items(inputs: dict[str, Any], expected: int, low: int, high: int, key: str = "items") -> list[int]:
    raw = inputs.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{key} must be a sequence of numeric scores")
    if len(raw) != expected:
        raise ValueError(f"{key} must contain {expected} scores")
    values = [int(value) for value in raw]
    if any(value < low or value > high for value in values):
        raise ValueError(f"{key} must be scored from {low} to {high}")
    return values


def _bounded_component(inputs: dict[str, Any], key: str, low: int = 0, high: int = 2) -> int:
    value = int(number(inputs, key))
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}")
    return value


def _integer_in_range(inputs: dict[str, Any], key: str, low: int, high: int) -> int:
    value = int(number(inputs, key))
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}")
    return value


def ocular_surface_disease_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    values = _items(inputs, 12, 0, 4)
    value = sum(values) * 25 / len(values)
    if value < 13:
        interpretation = "normal ocular surface symptoms"
    elif value < 23:
        interpretation = "mild ocular surface disease"
    elif value < 33:
        interpretation = "moderate ocular surface disease"
    else:
        interpretation = "severe ocular surface disease"
    return result(metadata, value, "score", interpretation)


def voice_handicap_index_10(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 10, 0, 4))
    interpretation = "elevated voice handicap burden" if score > 11 else "lower voice handicap burden"
    return result(metadata, score, "points", interpretation)


def eating_assessment_tool_10(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 10, 0, 4))
    interpretation = "abnormal dysphagia screen range" if score >= 3 else "lower dysphagia symptom burden"
    return result(metadata, score, "points", interpretation)


def reflux_symptom_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 9, 0, 5))
    interpretation = "elevated reflux symptom burden" if score > 13 else "lower reflux symptom burden"
    return result(metadata, score, "points", interpretation)


def gerd_q_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 6, 0, 3))
    interpretation = (
        "GERD-Q: score supports increased GERD likelihood using the common >=8 cutoff."
        if score >= 8
        else "GERD-Q: below the common >=8 cutoff for increased GERD likelihood."
    )
    return result(metadata, score, "points", interpretation)


def iciq_ui_short_form_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    frequency = _integer_in_range(inputs, "frequency", 0, 5)
    amount = _integer_in_range(inputs, "amount", 0, 6)
    life_impact = _integer_in_range(inputs, "life_impact", 0, 10)
    score = frequency + amount + life_impact
    return result(
        metadata,
        score,
        "points",
        "ICIQ-UI Short Form pre-scored total; higher scores indicate greater urinary incontinence impact.",
    )


def incontinence_impact_questionnaire_7_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    values = _items(inputs, 7, 0, 3)
    score = sum(values) / len(values) * (100 / 3)
    return result(
        metadata,
        score,
        "score",
        "IIQ-7 transformed score on a 0-100 scale; higher scores indicate greater incontinence impact.",
    )


def pelvic_floor_distress_inventory_20_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    popdi_items = _items(inputs, 6, 0, 4, key="popdi_6_items")
    cradi_items = _items(inputs, 8, 0, 4, key="cradi_8_items")
    udi_items = _items(inputs, 6, 0, 4, key="udi_6_items")

    popdi_score = sum(popdi_items) / len(popdi_items) * 25
    cradi_score = sum(cradi_items) / len(cradi_items) * 25
    udi_score = sum(udi_items) / len(udi_items) * 25
    total = popdi_score + cradi_score + udi_score
    value = {
        "popdi_6_score": round(popdi_score, 4),
        "cradi_8_score": round(cradi_score, 4),
        "udi_6_score": round(udi_score, 4),
        "total_score": round(total, 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="score",
        interpretation="PFDI-20 pre-scored summary; each subscale is 0-100 and total range is 0-300.",
    )


def visual_function_index_14_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw = inputs.get("item_scores")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("item_scores must be a sequence of 14 pre-scored values or None")
    if len(raw) != 14:
        raise ValueError("item_scores must contain 14 entries")

    scored_items = []
    for index, value in enumerate(raw):
        if value is None:
            continue
        score = int(value)
        if score < 0 or score > 4:
            raise ValueError(f"item_scores[{index}] must be between 0 and 4, or None")
        scored_items.append(score)
    if not scored_items:
        raise ValueError("item_scores must include at least one applicable scored item")

    score = sum(scored_items) / len(scored_items) * 25
    value = {"score": round(score, 4), "answered_items": len(scored_items)}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="score",
        interpretation="VF-14 pre-scored visual function score on a 0-100 scale; higher scores indicate better function.",
    )


def speed_dry_eye_questionnaire_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    frequency_scores = _items(inputs, 4, 0, 3, key="frequency_scores")
    severity_scores = _items(inputs, 4, 0, 4, key="severity_scores")
    frequency_total = sum(frequency_scores)
    severity_total = sum(severity_scores)
    total = frequency_total + severity_total
    value = {
        "frequency_total": frequency_total,
        "severity_total": severity_total,
        "total_score": total,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="SPEED dry eye questionnaire pre-scored total; higher scores indicate greater symptom burden.",
    )


def premature_ejaculation_diagnostic_tool_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_items(inputs, 5, 0, 4))
    if score <= 8:
        interpretation = "PEDT: premature ejaculation unlikely."
    elif score <= 10:
        interpretation = "PEDT: possible premature ejaculation range."
    else:
        interpretation = "PEDT: likely premature ejaculation range."
    return result(metadata, score, "points", interpretation)


def patient_oriented_eczema_measure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 7, 0, 4))
    if score <= 2:
        interpretation = "clear or almost clear eczema symptoms"
    elif score <= 7:
        interpretation = "mild eczema symptoms"
    elif score <= 16:
        interpretation = "moderate eczema symptoms"
    elif score <= 24:
        interpretation = "severe eczema symptoms"
    else:
        interpretation = "very severe eczema symptoms"
    return result(metadata, score, "points", interpretation)


def apfel_ponv_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(bool(inputs.get("female", False)))
    score += int(bool(inputs.get("non_smoker", False)))
    score += int(bool(inputs.get("history_ponv_or_motion_sickness", False)))
    score += int(bool(inputs.get("postoperative_opioids", False)))
    if score <= 1:
        interpretation = "low PONV risk"
    elif score == 2:
        interpretation = "moderate PONV risk"
    else:
        interpretation = "high PONV risk"
    return result(metadata, score, "points", interpretation)


def aldrete_recovery_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = ("activity", "respiration", "circulation", "consciousness", "oxygen_saturation")
    score = sum(_bounded_component(inputs, key) for key in keys)
    interpretation = "commonly compatible with PACU discharge threshold" if score >= 9 else "below common PACU discharge threshold"
    return result(metadata, score, "points", interpretation)


def post_anesthetic_discharge_scoring_system(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    keys = ("vital_signs", "activity", "nausea_vomiting", "pain", "surgical_bleeding")
    score = sum(_bounded_component(inputs, key) for key in keys)
    interpretation = "commonly compatible with ambulatory discharge threshold" if score >= 9 else "below common ambulatory discharge threshold"
    return result(metadata, score, "points", interpretation)


def critical_care_pain_observation_tool(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = ("facial_expression", "body_movements", "muscle_tension", "ventilator_compliance_or_vocalization")
    score = sum(_bounded_component(inputs, key) for key in keys)
    interpretation = "higher observed pain behaviors" if score >= 3 else "lower observed pain behaviors"
    return result(metadata, score, "points", interpretation)


def flacc_pediatric_pain_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = ("face", "legs", "activity", "cry", "consolability")
    score = sum(_bounded_component(inputs, key) for key in keys)
    if score == 0:
        interpretation = "no pain by FLACC score"
    elif score <= 3:
        interpretation = "mild pain by FLACC score"
    elif score <= 6:
        interpretation = "moderate pain by FLACC score"
    else:
        interpretation = "severe pain by FLACC score"
    return result(metadata, score, "points", interpretation)


def numeric_rating_scale_pain(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 0, 10)
    if score == 0:
        severity = "no pain"
    elif score <= 3:
        severity = "mild pain"
    elif score <= 6:
        severity = "moderate pain"
    else:
        severity = "severe pain"
    return result(metadata, score, "points", f"Numeric Rating Scale: {severity}.")


def ramsay_sedation_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 1, 6)
    labels = {
        1: "anxious, agitated, or restless",
        2: "cooperative, oriented, and tranquil",
        3: "responds to commands only",
        4: "brisk response to light glabellar tap or loud auditory stimulus",
        5: "sluggish response to light glabellar tap or loud auditory stimulus",
        6: "no response to stimulus",
    }
    return result(metadata, grade, "grade", f"Ramsay sedation scale grade {grade}: {labels[grade]}.")


def follicular_lymphoma_international_prognostic_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = int(number(inputs, "age_years") > 60)
    score += int(number(inputs, "ann_arbor_stage") >= 3)
    score += int(number(inputs, "hemoglobin_g_dl") < 12)
    score += int(number(inputs, "nodal_areas") > 4)
    score += int(bool(inputs.get("ldh_above_normal", False)))
    interpretation = "low risk" if score <= 1 else "intermediate risk" if score == 2 else "high risk"
    return result(metadata, score, "points", interpretation)


def international_prognostic_index_lymphoma(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(number(inputs, "age_years") > 60)
    score += int(number(inputs, "ann_arbor_stage") >= 3)
    score += int(bool(inputs.get("ldh_above_normal", False)))
    score += int(number(inputs, "ecog_performance_status") >= 2)
    score += int(number(inputs, "extranodal_sites") > 1)
    interpretation = "low risk" if score <= 1 else "low-intermediate risk" if score == 2 else "high-intermediate/high risk"
    return result(metadata, score, "points", interpretation)


def robson_ten_group_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    parity = str(inputs.get("parity", "")).strip().lower()
    if parity not in {"nulliparous", "multiparous"}:
        raise ValueError("parity must be one of: nulliparous, multiparous")
    previous_cesarean = bool(inputs.get("previous_cesarean", False))
    if parity == "nulliparous" and previous_cesarean:
        raise ValueError("previous_cesarean cannot be true for nulliparous patients")

    presentation = str(inputs.get("fetal_presentation", "")).strip().lower()
    if presentation not in {"cephalic", "breech", "transverse_oblique"}:
        raise ValueError("fetal_presentation must be one of: cephalic, breech, transverse_oblique")
    fetal_count = _integer_in_range(inputs, "fetal_count", 1, 20)
    gestational_age = number(inputs, "gestational_age_weeks")
    if gestational_age <= 0:
        raise ValueError("gestational_age_weeks must be positive")
    labor_onset = str(inputs.get("labor_onset", "")).strip().lower()
    if labor_onset not in {"spontaneous", "induced", "prelabor_cesarean"}:
        raise ValueError("labor_onset must be one of: spontaneous, induced, prelabor_cesarean")

    if fetal_count > 1:
        group = 8
        label = "multiple pregnancy"
    elif presentation == "transverse_oblique":
        group = 9
        label = "single pregnancy with transverse or oblique lie"
    elif presentation == "breech":
        if parity == "nulliparous":
            group = 6
            label = "nulliparous single breech pregnancy"
        else:
            group = 7
            label = "multiparous single breech pregnancy"
    elif gestational_age < 37:
        group = 10
        label = "single cephalic preterm pregnancy"
    elif previous_cesarean:
        group = 5
        label = "previous cesarean single cephalic term pregnancy"
    elif parity == "nulliparous":
        if labor_onset == "spontaneous":
            group = 1
            label = "nulliparous single cephalic term spontaneous labor"
        else:
            group = 2
            label = "nulliparous single cephalic term induced labor or prelabor cesarean"
    else:
        if labor_onset == "spontaneous":
            group = 3
            label = "multiparous without previous cesarean single cephalic term spontaneous labor"
        else:
            group = 4
            label = "multiparous without previous cesarean single cephalic term induced labor or prelabor cesarean"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"group": group, "label": label},
        unit="group",
        interpretation=f"Robson Ten-Group Classification group {group}: {label}.",
    )


def sinonasal_outcome_test_22(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 22, 0, 5))
    return result(
        metadata,
        score,
        "points",
        "SNOT-22: higher sinonasal symptom and quality-of-life burden with increasing score; total range 0-110.",
    )


def jankovic_rating_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    severity = _integer_in_range(inputs, "severity", 0, 4)
    frequency = _integer_in_range(inputs, "frequency", 0, 4)
    total = severity + frequency
    value = {"total_score": total, "severity": severity, "frequency": frequency}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="Jankovic Rating Scale: severity plus frequency; higher scores indicate greater blepharospasm burden.",
    )


def drug_abuse_screening_test_10(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw = inputs.get("items")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("items must be a sequence of 10 coded boolean responses")
    if len(raw) != 10:
        raise ValueError("items must contain 10 coded boolean responses")

    responses = []
    for index, value in enumerate(raw):
        if isinstance(value, bool):
            responses.append(value)
        elif value == 0 or value == 1:
            responses.append(bool(value))
        else:
            raise ValueError(f"items[{index}] must be a bool or 0/1")

    score = sum(1 for index, response in enumerate(responses) if (not response if index == 2 else response))
    label = (
        "no problems reported"
        if score == 0
        else "low level"
        if score <= 2
        else "moderate level"
        if score <= 5
        else "substantial level"
        if score <= 8
        else "severe level"
    )
    return result(metadata, score, "points", f"DAST-10: {label}; total range 0-10.")


def lanss_pain_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw = inputs.get("component_points")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("component_points must be a sequence of 7 pre-scored components")
    if len(raw) != 7:
        raise ValueError("component_points must contain 7 pre-scored components")
    scores = [int(value) for value in raw]
    if any(score < 0 for score in scores):
        raise ValueError("component_points must be nonnegative")
    total = sum(scores)
    if total > 24:
        raise ValueError("LANSS total score cannot exceed 24")
    interpretation = "neuropathic pain mechanisms likely" if total >= 12 else "below neuropathic pain cutoff"
    return result(metadata, total, "points", f"LANSS Pain Scale: {interpretation}.")


def pain_catastrophizing_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_items(inputs, 13, 0, 4))
    label = "clinically relevant catastrophizing range" if score >= 30 else "below common clinical cutoff"
    return result(metadata, score, "points", f"Pain Catastrophizing Scale: {label}; total range 0-52.")


def brief_pain_inventory_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    severity_scores = _items(inputs, 4, 0, 10, key="severity_items")
    interference_scores = _items(inputs, 7, 0, 10, key="interference_items")
    severity_mean = sum(severity_scores) / len(severity_scores)
    interference_mean = sum(interference_scores) / len(interference_scores)
    value = {
        "severity_total": sum(severity_scores),
        "severity_mean": round(severity_mean, 4),
        "interference_total": sum(interference_scores),
        "interference_mean": round(interference_mean, 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="Brief Pain Inventory pre-scored severity and interference summaries.",
    )


def opioid_risk_tool(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")

    if sex == "female":
        weights = {
            "family_history_alcohol": 1,
            "family_history_illegal_drugs": 2,
            "family_history_prescription_drugs": 4,
            "personal_history_alcohol": 3,
            "personal_history_illegal_drugs": 4,
            "personal_history_prescription_drugs": 5,
            "age_16_to_45": 1,
            "preadolescent_sexual_abuse": 3,
            "psychological_disease": 2,
        }
    else:
        weights = {
            "family_history_alcohol": 3,
            "family_history_illegal_drugs": 3,
            "family_history_prescription_drugs": 4,
            "personal_history_alcohol": 3,
            "personal_history_illegal_drugs": 4,
            "personal_history_prescription_drugs": 5,
            "age_16_to_45": 1,
            "preadolescent_sexual_abuse": 0,
            "psychological_disease": 2,
        }

    score = sum(weight for key, weight in weights.items() if bool(inputs.get(key, False)))
    if score <= 3:
        label = "low risk"
    elif score <= 7:
        label = "moderate risk"
    else:
        label = "high risk"
    return result(metadata, score, "points", f"Opioid Risk Tool: {label}.")


def edmonton_symptom_assessment_system(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    raw = inputs.get("symptom_scores")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("symptom_scores must be a sequence of 9 core symptom scores")
    if len(raw) != 9:
        raise ValueError("symptom_scores must contain 9 core symptom scores")
    core_scores = [int(value) for value in raw]
    if any(score < 0 or score > 10 for score in core_scores):
        raise ValueError("symptom_scores must be scored from 0 to 10")

    optional = None
    if "optional_wellbeing_score" in inputs:
        optional = _integer_in_range(inputs, "optional_wellbeing_score", 0, 10)
    core_total = sum(core_scores)
    value = {
        "core_total": core_total,
        "total_with_optional": core_total if optional is None else core_total + optional,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="ESAS: higher coded symptom totals indicate greater symptom burden.",
    )
