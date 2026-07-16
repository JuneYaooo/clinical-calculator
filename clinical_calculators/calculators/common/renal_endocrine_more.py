from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _nonnegative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return value


def _integer_value(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer")
    return int(numeric_value)


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    integer_value = _integer_value(inputs[key], key)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _sex(inputs: dict[str, Any]) -> str:
    if "sex" not in inputs:
        raise KeyError("sex")

    sex = str(inputs["sex"]).strip().lower()
    if sex in {"male", "female"}:
        return sex
    raise ValueError("sex must be 'male' or 'female'")


def _score_items(inputs: dict[str, Any], count: int, minimum: int, maximum: int) -> list[int]:
    if "items" not in inputs:
        raise KeyError("items")

    values = inputs["items"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"items must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"items must contain exactly {count} scores")

    scores = []
    for index, value in enumerate(values):
        item_key = f"items[{index}]"
        score = _integer_value(value, item_key)
        if score < minimum or score > maximum:
            raise ValueError(f"{item_key} must be between {minimum} and {maximum}")
        scores.append(score)
    return scores


def _range_label(score: int, ranges: tuple[tuple[int, int, str], ...]) -> str:
    for minimum, maximum, label in ranges:
        if minimum <= score <= maximum:
            return label
    raise ValueError("score is outside the supported interpretation range")


def _normalized_text(inputs: dict[str, Any], key: str) -> str:
    if key not in inputs:
        raise KeyError(key)
    return str(inputs[key]).strip().lower().replace("-", "_").replace(" ", "_")


def _required_bool(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)
    value = inputs[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    raise ValueError(f"{key} must be a boolean")


def sanaka_creatinine_clearance(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = _sex(inputs)
    weight_kg = _positive_number(inputs, "weight_kg")
    serum_albumin_g_dl = _positive_number(inputs, "serum_albumin_g_dl")
    serum_creatinine_mg_dl = _positive_number(inputs, "serum_creatinine_mg_dl")

    multiplier, additive = (13, 29) if sex == "female" else (19, 32)
    value = weight_kg * (multiplier * serum_albumin_g_dl + additive) / (100 * serum_creatinine_mg_dl)
    return result(metadata, value, "mL/min", "Sanaka estimated creatinine clearance.")


def twenty_four_hour_urine_creatinine_excretion_estimate(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _positive_number(inputs, "age_years")
    weight_kg = _positive_number(inputs, "weight_kg")
    sex = _sex(inputs)
    black_race = bool(inputs.get("black_race", False))

    estimated = 879.89 + 12.51 * weight_kg - 6.19 * age_years
    if black_race:
        estimated += 34.51
    if sex == "female":
        estimated -= 379.42

    value: dict[str, float] = {"estimated_creatinine_excretion_mg_day": round(estimated, 4)}
    interpretation = "Estimated 24-hour urine creatinine excretion."
    if "urine_creatinine_mg_dl" in inputs or "urine_volume_ml" in inputs:
        urine_creatinine_mg_dl = _positive_number(inputs, "urine_creatinine_mg_dl")
        urine_volume_ml = _positive_number(inputs, "urine_volume_ml")
        measured = urine_creatinine_mg_dl * urine_volume_ml / 100
        percent = measured / estimated * 100
        value["measured_creatinine_excretion_mg_day"] = round(measured, 4)
        value["measured_percent_of_estimated"] = round(percent, 4)
        if 80 <= percent <= 120:
            interpretation = "Measured urine creatinine is compatible with a complete 24-hour collection."
        elif percent < 80:
            interpretation = "Measured urine creatinine is lower than expected; undercollection is possible."
        else:
            interpretation = "Measured urine creatinine is higher than expected; overcollection or high creatinine generation is possible."

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="mg/day",
        interpretation=interpretation,
    )


def burch_wartofsky_point_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "temperature_f" in inputs:
        temperature_f = _positive_number(inputs, "temperature_f")
    elif "temperature_c" in inputs:
        temperature_f = _positive_number(inputs, "temperature_c") * 9 / 5 + 32
    else:
        raise KeyError("temperature_f or temperature_c")

    if temperature_f < 99:
        thermoregulation = 0
    elif temperature_f < 100:
        thermoregulation = 5
    elif temperature_f < 101:
        thermoregulation = 10
    elif temperature_f < 102:
        thermoregulation = 15
    elif temperature_f < 103:
        thermoregulation = 20
    elif temperature_f < 104:
        thermoregulation = 25
    else:
        thermoregulation = 30

    heart_rate = _positive_number(inputs, "heart_rate_bpm")
    if heart_rate < 90:
        tachycardia = 0
    elif heart_rate < 110:
        tachycardia = 5
    elif heart_rate < 120:
        tachycardia = 10
    elif heart_rate < 130:
        tachycardia = 15
    elif heart_rate < 140:
        tachycardia = 20
    else:
        tachycardia = 25

    cns = _normalized_text(inputs, "cns_effects")
    cns_points = {
        "absent": 0,
        "none": 0,
        "mild": 10,
        "moderate": 20,
        "severe": 30,
    }.get(cns)
    if cns_points is None:
        raise ValueError("cns_effects must be absent, mild, moderate, or severe")

    gi = _normalized_text(inputs, "gi_hepatic_dysfunction")
    gi_points = {
        "absent": 0,
        "none": 0,
        "moderate": 10,
        "severe": 20,
    }.get(gi)
    if gi_points is None:
        raise ValueError("gi_hepatic_dysfunction must be absent, moderate, or severe")

    chf = _normalized_text(inputs, "congestive_heart_failure")
    chf_points = {
        "absent": 0,
        "none": 0,
        "mild": 5,
        "moderate": 10,
        "severe": 15,
    }.get(chf)
    if chf_points is None:
        raise ValueError("congestive_heart_failure must be absent, mild, moderate, or severe")

    total = (
        thermoregulation
        + tachycardia
        + cns_points
        + gi_points
        + chf_points
        + (10 if bool(inputs.get("atrial_fibrillation", False)) else 0)
        + (10 if bool(inputs.get("precipitating_event", False)) else 0)
    )
    if total >= 45:
        interpretation = "Burch-Wartofsky score is highly suggestive of thyroid storm."
    elif total >= 25:
        interpretation = "Burch-Wartofsky score is consistent with impending thyroid storm."
    else:
        interpretation = "Burch-Wartofsky score makes thyroid storm unlikely."
    return result(metadata, total, "points", interpretation)


def wagner_diabetic_foot_ulcer_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    category = _normalized_text(inputs, "wound_category")
    categories = {
        "no_open_lesion": (0, "intact skin or healed ulcer with possible deformity or cellulitis"),
        "superficial_ulcer": (1, "superficial diabetic foot ulcer"),
        "deep_ulcer_to_tendon_or_capsule": (2, "deep ulcer extending to tendon, bone, or capsule"),
        "deep_abscess_or_osteomyelitis": (3, "deep ulcer with abscess, osteomyelitis, or joint sepsis"),
        "forefoot_gangrene": (4, "localized forefoot or heel gangrene"),
        "extensive_gangrene": (5, "extensive whole-foot gangrene"),
    }
    if category not in categories:
        raise ValueError("wound_category is not a supported Wagner grade category")

    grade, label = categories[category]
    return result(metadata, grade, "grade", f"Wagner grade {grade}: {label}.")


def university_of_texas_diabetic_foot_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 0, 3)
    infected = bool(inputs.get("infected", False))
    ischemic = bool(inputs.get("ischemic", False))

    if infected and ischemic:
        stage, stage_label = "D", "infection and ischemia"
    elif ischemic:
        stage, stage_label = "C", "ischemia without infection"
    elif infected:
        stage, stage_label = "B", "infection without ischemia"
    else:
        stage, stage_label = "A", "no infection or ischemia"

    grade_labels = {
        0: "pre- or postulcerative lesion, completely epithelialized",
        1: "superficial wound not involving tendon, capsule, or bone",
        2: "wound penetrates to tendon or capsule",
        3: "wound penetrates to bone or joint",
    }
    classification = f"{grade}{stage}"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"classification": classification, "grade": grade, "stage": stage},
        unit="grade/stage",
        interpretation=f"University of Texas {classification}: {grade_labels[grade]}; {stage_label}.",
    )


def _damico_stage_level(stage: str) -> int:
    normalized = stage.strip().lower().replace(" ", "")
    if normalized.startswith("ct"):
        normalized = normalized[1:]
    if normalized.startswith("pt"):
        normalized = normalized[1:]

    stage_order = {
        "t1": 1,
        "t1a": 1,
        "t1b": 1,
        "t1c": 1,
        "t2": 2,
        "t2a": 2,
        "t2b": 3,
        "t2c": 4,
        "t3": 5,
        "t3a": 5,
        "t3b": 5,
        "t4": 6,
    }
    if normalized not in stage_order:
        raise ValueError("clinical_t_stage must be T1-T4 with optional a/b/c substage")
    return stage_order[normalized]


def _damico_grade_group(inputs: dict[str, Any]) -> int:
    if "grade_group" in inputs:
        return _integer_in_range(inputs, "grade_group", 1, 5)
    gleason = _integer_in_range(inputs, "gleason_score", 2, 10)
    if gleason <= 6:
        return 1
    if gleason == 7:
        return 2
    return 4


def damico_prostate_cancer_risk_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    psa = _positive_number(inputs, "psa_ng_ml")
    if "clinical_t_stage" not in inputs:
        raise KeyError("clinical_t_stage")
    stage_level = _damico_stage_level(str(inputs["clinical_t_stage"]))
    grade_group = _damico_grade_group(inputs)

    high_reasons = []
    if psa > 20:
        high_reasons.append("PSA >20")
    if grade_group >= 4:
        high_reasons.append("grade group 4-5 or Gleason 8-10")
    if stage_level >= 4:
        high_reasons.append("clinical stage T2c or higher")
    if high_reasons:
        risk = "high risk"
        reasons = ", ".join(high_reasons)
    else:
        intermediate_reasons = []
        if psa > 10:
            intermediate_reasons.append("PSA >10 to 20")
        if grade_group in {2, 3}:
            intermediate_reasons.append("grade group 2-3 or Gleason 7")
        if stage_level == 3:
            intermediate_reasons.append("clinical stage T2b")
        if intermediate_reasons:
            risk = "intermediate risk"
            reasons = ", ".join(intermediate_reasons)
        else:
            risk = "low risk"
            reasons = "PSA <=10, grade group 1/Gleason <=6, and clinical stage T1-T2a"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=risk,
        unit="risk category",
        interpretation=f"D'Amico {risk}: {reasons}.",
    )


def finnish_diabetes_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _positive_number(inputs, "age_years")
    if age_years < 18:
        raise ValueError("age_years must be at least 18")
    sex = _sex(inputs)
    bmi = _positive_number(inputs, "bmi")
    waist_circumference_cm = _positive_number(inputs, "waist_circumference_cm")

    if age_years < 45:
        age_points = 0
    elif age_years < 55:
        age_points = 2
    elif age_years < 65:
        age_points = 3
    else:
        age_points = 4

    if bmi < 25:
        bmi_points = 0
    elif bmi < 30:
        bmi_points = 1
    else:
        bmi_points = 3

    if sex == "male":
        if waist_circumference_cm < 94:
            waist_points = 0
        elif waist_circumference_cm <= 102:
            waist_points = 3
        else:
            waist_points = 4
    else:
        if waist_circumference_cm < 80:
            waist_points = 0
        elif waist_circumference_cm <= 88:
            waist_points = 3
        else:
            waist_points = 4

    physical_activity_points = 0 if _required_bool(inputs, "physically_active_daily") else 2
    diet_points = 0 if _required_bool(inputs, "daily_fruit_vegetable_or_berry") else 1
    antihypertensive_points = 2 if _required_bool(inputs, "antihypertensive_medication") else 0
    glucose_points = 5 if _required_bool(inputs, "history_high_blood_glucose") else 0

    family_history = _normalized_text(inputs, "family_history")
    family_history_points_by_code = {
        "no": 0,
        "none": 0,
        "no_family_history": 0,
        "second_degree": 3,
        "grandparent_aunt_uncle_cousin": 3,
        "non_first_degree": 3,
        "first_degree": 5,
        "parent_sibling_child": 5,
        "parent_brother_sister_child": 5,
    }
    if family_history not in family_history_points_by_code:
        raise ValueError("family_history must be 'none', 'second_degree', or 'first_degree'")
    family_history_points = family_history_points_by_code[family_history]

    components = {
        "age": age_points,
        "bmi": bmi_points,
        "waist_circumference": waist_points,
        "physical_activity": physical_activity_points,
        "diet": diet_points,
        "antihypertensive_medication": antihypertensive_points,
        "history_high_blood_glucose": glucose_points,
        "family_history": family_history_points,
    }
    score = sum(components.values())
    if score < 7:
        risk_category, estimated_risk = "low", "1 in 100"
    elif score <= 11:
        risk_category, estimated_risk = "slightly elevated", "1 in 25"
    elif score <= 14:
        risk_category, estimated_risk = "moderate", "1 in 6"
    elif score <= 20:
        risk_category, estimated_risk = "high", "1 in 3"
    else:
        risk_category, estimated_risk = "very high", "1 in 2"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": score,
            "risk_category": risk_category,
            "estimated_10_year_risk": estimated_risk,
            "components": components,
        },
        unit="points",
        interpretation=f"FINDRISC {score} points: {risk_category} 10-year diabetes risk ({estimated_risk}).",
    )


def _capra_stage_points(inputs: dict[str, Any]) -> int:
    if "clinical_t_stage" not in inputs:
        raise KeyError("clinical_t_stage")
    normalized = str(inputs["clinical_t_stage"]).strip().lower().replace(" ", "")
    if normalized.startswith("ct") or normalized.startswith("pt"):
        normalized = normalized[1:]
    supported = {
        "t1",
        "t1a",
        "t1b",
        "t1c",
        "t2",
        "t2a",
        "t2b",
        "t2c",
        "t3",
        "t3a",
        "t3b",
        "t4",
        "t4a",
        "t4b",
    }
    if normalized not in supported:
        raise ValueError("clinical_t_stage must be T1-T4 with optional a/b/c substage")
    return 1 if normalized.startswith("t3") or normalized.startswith("t4") else 0


def _capra_gleason_points(inputs: dict[str, Any]) -> int:
    if "grade_group" in inputs:
        grade_group = _integer_in_range(inputs, "grade_group", 1, 5)
        if grade_group == 1:
            return 0
        if grade_group == 2:
            return 1
        return 3

    primary = _integer_in_range(inputs, "gleason_primary", 1, 5)
    secondary = _integer_in_range(inputs, "gleason_secondary", 1, 5)
    if primary + secondary > 10:
        raise ValueError("gleason_primary + gleason_secondary must be no greater than 10")
    if primary >= 4:
        return 3
    if secondary >= 4:
        return 1
    return 0


def _capra_percent_positive_cores(inputs: dict[str, Any]) -> float:
    if "percent_positive_cores" in inputs:
        percent = number(inputs, "percent_positive_cores")
        if percent < 0 or percent > 100:
            raise ValueError("percent_positive_cores must be between 0 and 100")
        return percent

    positive_cores = _integer_in_range(inputs, "positive_biopsy_cores", 0, 10_000)
    total_cores = _integer_in_range(inputs, "total_biopsy_cores", 1, 10_000)
    if positive_cores > total_cores:
        raise ValueError("positive_biopsy_cores must be no greater than total_biopsy_cores")
    return positive_cores / total_cores * 100


def ucsf_capra_prostate_cancer_risk_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _positive_number(inputs, "age_years")
    psa_ng_ml = _positive_number(inputs, "psa_ng_ml")

    age_points = 1 if age_years >= 50 else 0
    if psa_ng_ml <= 6:
        psa_points = 0
    elif psa_ng_ml <= 10:
        psa_points = 1
    elif psa_ng_ml <= 20:
        psa_points = 2
    elif psa_ng_ml <= 30:
        psa_points = 3
    else:
        psa_points = 4

    gleason_points = _capra_gleason_points(inputs)
    stage_points = _capra_stage_points(inputs)
    percent_positive_cores = _capra_percent_positive_cores(inputs)
    core_points = 1 if percent_positive_cores >= 34 else 0

    components = {
        "age": age_points,
        "psa": psa_points,
        "gleason": gleason_points,
        "clinical_t_stage": stage_points,
        "positive_biopsy_cores": core_points,
    }
    score = sum(components.values())
    risk_category = _range_label(
        score,
        (
            (0, 2, "low risk"),
            (3, 5, "intermediate risk"),
            (6, 10, "high risk"),
        ),
    )

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": score,
            "risk_category": risk_category,
            "percent_positive_cores": round(percent_positive_cores, 4),
            "components": components,
        },
        unit="points",
        interpretation=f"UCSF-CAPRA score {score}: {risk_category}.",
    )


def cdc_prediabetes_risk_test(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _positive_number(inputs, "age_years")
    if age_years < 18:
        raise ValueError("age_years must be at least 18")
    sex = _sex(inputs)
    bmi = _positive_number(inputs, "bmi")
    asian_american = _required_bool(inputs, "asian_american")

    if age_years < 40:
        age_points = 0
    elif age_years < 50:
        age_points = 1
    elif age_years < 60:
        age_points = 2
    else:
        age_points = 3

    history_gestational_diabetes = _required_bool(inputs, "history_gestational_diabetes")
    if sex == "male" and history_gestational_diabetes:
        raise ValueError("history_gestational_diabetes applies only when sex is 'female'")
    sex_or_gdm_points = 1 if sex == "male" or history_gestational_diabetes else 0

    bmi_normal_cutoff = 23 if asian_american else 25
    if bmi < bmi_normal_cutoff:
        bmi_points = 0
    elif bmi < 30:
        bmi_points = 1
    elif bmi < 40:
        bmi_points = 2
    else:
        bmi_points = 3

    components = {
        "age": age_points,
        "family_history": 1 if _required_bool(inputs, "first_degree_family_history") else 0,
        "high_blood_pressure": 1 if _required_bool(inputs, "high_blood_pressure") else 0,
        "physical_activity": 0 if _required_bool(inputs, "physically_active") else 1,
        "sex_or_gestational_diabetes": sex_or_gdm_points,
        "bmi": bmi_points,
    }
    score = sum(components.values())
    high_risk = score >= 5
    classification = "high risk" if high_risk else "not high risk"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": score,
            "classification": classification,
            "high_risk": high_risk,
            "components": components,
        },
        unit="points",
        interpretation=f"CDC prediabetes risk test score {score}: {classification} (high risk threshold >=5).",
    )


def homa_ir(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    fasting_insulin_uIU_ml = _positive_number(inputs, "fasting_insulin_uIU_ml")

    if "fasting_glucose_mmol_l" in inputs:
        fasting_glucose = _positive_number(inputs, "fasting_glucose_mmol_l")
        value = fasting_insulin_uIU_ml * fasting_glucose / 22.5
    elif "fasting_glucose_mg_dl" in inputs:
        fasting_glucose = _positive_number(inputs, "fasting_glucose_mg_dl")
        value = fasting_insulin_uIU_ml * fasting_glucose / 405
    else:
        raise KeyError("fasting_glucose_mmol_l or fasting_glucose_mg_dl")

    if value < 2:
        interpretation = "HOMA-IR: low."
    elif value < 3:
        interpretation = "HOMA-IR: possible insulin resistance."
    else:
        interpretation = "HOMA-IR: insulin resistance."
    return result(metadata, value, "index", interpretation)


def insulin_sensitivity_factor_estimate(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    total_daily_insulin_units = _positive_number(inputs, "total_daily_insulin_units")
    insulin_type = str(inputs.get("insulin_type", "rapid_acting")).strip().lower().replace("-", "_").replace(" ", "_")
    if insulin_type in {"rapid", "rapid_acting", "rapid_acting_analog", "analog"}:
        rule = 1800
    elif insulin_type in {"regular", "short", "short_acting"}:
        rule = 1500
    else:
        raise ValueError("insulin_type must be 'rapid_acting' or 'regular'")

    value = rule / total_daily_insulin_units
    return result(metadata, value, "mg/dL per unit", f"insulin sensitivity factor by the {rule} rule")


def diabetic_ketoacidosis_severity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    beta_hydroxybutyrate_mmol_l = _positive_number(inputs, "beta_hydroxybutyrate_mmol_l")
    ph = _positive_number(inputs, "ph")
    bicarbonate_mmol_l = _positive_number(inputs, "bicarbonate_mmol_l")
    mental_status = str(inputs.get("mental_status", "")).strip().lower()
    if mental_status == "alert":
        mental_status = "normal"
    if mental_status not in {"normal", "drowsy", "stupor", "coma"}:
        raise ValueError("mental_status must be 'alert', 'normal', 'drowsy', 'stupor', or 'coma'")
    if beta_hydroxybutyrate_mmol_l < 3:
        raise ValueError("beta_hydroxybutyrate_mmol_l must be at least 3 for DKA severity classification")

    severity_scores = [1]
    if beta_hydroxybutyrate_mmol_l > 6:
        severity_scores.append(3)
    if ph < 7.0:
        severity_scores.append(3)
    elif ph <= 7.25:
        severity_scores.append(2)
    if bicarbonate_mmol_l < 10:
        severity_scores.append(3)
    elif bicarbonate_mmol_l < 15:
        severity_scores.append(2)
    if mental_status in {"stupor", "coma"}:
        severity_scores.append(3)
    elif mental_status == "drowsy":
        severity_scores.append(2)

    severity = {1: "mild", 2: "moderate", 3: "severe"}[max(severity_scores)]
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=severity,
        unit="severity",
        interpretation=f"diabetic ketoacidosis severity: {severity}",
    )


def international_prostate_symptom_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_score_items(inputs, count=7, minimum=0, maximum=5))
    if "quality_of_life" in inputs:
        _integer_in_range(inputs, "quality_of_life", 0, 6)

    label = _range_label(
        score,
        (
            (0, 7, "mild"),
            (8, 19, "moderate"),
            (20, 35, "severe"),
        ),
    )
    return result(metadata, score, "points", f"IPSS symptom score: {label}.")


def ipss_quality_of_life(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "quality_of_life", 0, 6)
    labels = {
        0: "delighted",
        1: "pleased",
        2: "mostly satisfied",
        3: "mixed",
        4: "mostly dissatisfied",
        5: "unhappy",
        6: "terrible",
    }
    return result(metadata, score, "points", f"IPSS quality of life: {labels[score]}.")


def iief_5_erectile_function_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_score_items(inputs, count=5, minimum=1, maximum=5))
    label = _range_label(
        score,
        (
            (5, 7, "severe"),
            (8, 11, "moderate"),
            (12, 16, "mild-to-moderate"),
            (17, 21, "mild"),
            (22, 25, "no ED"),
        ),
    )
    return result(metadata, score, "points", f"IIEF-5 erectile function score: {label}.")


def kdigo_ckd_ga_risk_category(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    egfr_ml_min_1_73m2 = _nonnegative_number(inputs, "egfr_ml_min_1_73m2")
    acr_mg_g = _nonnegative_number(inputs, "acr_mg_g")

    if egfr_ml_min_1_73m2 >= 90:
        g_category = "G1"
    elif egfr_ml_min_1_73m2 >= 60:
        g_category = "G2"
    elif egfr_ml_min_1_73m2 >= 45:
        g_category = "G3a"
    elif egfr_ml_min_1_73m2 >= 30:
        g_category = "G3b"
    elif egfr_ml_min_1_73m2 >= 15:
        g_category = "G4"
    else:
        g_category = "G5"

    if acr_mg_g < 30:
        a_category = "A1"
    elif acr_mg_g <= 300:
        a_category = "A2"
    else:
        a_category = "A3"

    if g_category in {"G4", "G5"}:
        risk = "very high"
    elif g_category == "G3b":
        risk = "high" if a_category == "A1" else "very high"
    elif g_category == "G3a":
        risk = {"A1": "moderate", "A2": "high", "A3": "very high"}[a_category]
    elif a_category == "A1":
        risk = "low"
    elif a_category == "A2":
        risk = "moderate"
    else:
        risk = "high"

    value = {"G": g_category, "A": a_category, "risk": risk}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="category",
        interpretation=f"KDIGO CKD G-A risk: {g_category}/{a_category}, {risk} risk.",
    )


def ckd_epi_2021_creatinine_cystatin_c(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _positive_number(inputs, "age_years")
    if age_years < 18:
        raise ValueError("age_years must be at least 18")
    serum_creatinine_mg_dl = _positive_number(inputs, "serum_creatinine_mg_dl")
    cystatin_c_mg_l = _positive_number(inputs, "cystatin_c_mg_l")
    sex = _sex(inputs)

    if sex == "female":
        kappa = 0.7
        alpha = -0.219
        sex_factor = 0.963
    else:
        kappa = 0.9
        alpha = -0.144
        sex_factor = 1.0

    creatinine_ratio = serum_creatinine_mg_dl / kappa
    cystatin_ratio = cystatin_c_mg_l / 0.8
    value = (
        135
        * min(creatinine_ratio, 1) ** alpha
        * max(creatinine_ratio, 1) ** -0.544
        * min(cystatin_ratio, 1) ** -0.323
        * max(cystatin_ratio, 1) ** -0.778
        * 0.9961**age_years
        * sex_factor
    )
    return result(metadata, value, "mL/min/1.73m^2", "estimated GFR by 2021 CKD-EPI creatinine-cystatin C equation")


def metabolic_syndrome_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")

    waist = _positive_number(inputs, "waist_circumference_cm")
    triglycerides = _positive_number(inputs, "triglycerides_mg_dl")
    hdl = _positive_number(inputs, "hdl_mg_dl")
    systolic_bp = _positive_number(inputs, "systolic_bp")
    diastolic_bp = _positive_number(inputs, "diastolic_bp")
    fasting_glucose = _positive_number(inputs, "fasting_glucose_mg_dl")
    on_antihypertensive = bool(inputs.get("on_antihypertensive_treatment", False))
    on_glucose_lowering = bool(inputs.get("on_glucose_lowering_treatment", False))

    components = {
        "abdominal_obesity": waist > (102 if sex == "male" else 88),
        "triglycerides": triglycerides >= 150,
        "hdl": hdl < (40 if sex == "male" else 50),
        "blood_pressure": systolic_bp >= 130 or diastolic_bp >= 85 or on_antihypertensive,
        "fasting_glucose": fasting_glucose >= 100 or on_glucose_lowering,
    }
    criteria_met = sum(components.values())
    meets_syndrome = criteria_met >= 3

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "criteria_met": criteria_met,
            "metabolic_syndrome": meets_syndrome,
            "components": components,
        },
        unit="criteria",
        interpretation=(
            f"Metabolic syndrome criteria {'met' if meets_syndrome else 'not met'} "
            f"({criteria_met} of 5 components)."
        ),
    )


def bariatric_percent_excess_weight_loss(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    preoperative_weight_kg = _positive_number(inputs, "preoperative_weight_kg")
    current_weight_kg = _positive_number(inputs, "current_weight_kg")
    ideal_weight_kg = _positive_number(inputs, "ideal_weight_kg")

    if preoperative_weight_kg <= ideal_weight_kg:
        raise ValueError("preoperative_weight_kg must be greater than ideal_weight_kg")

    value = (preoperative_weight_kg - current_weight_kg) / (preoperative_weight_kg - ideal_weight_kg) * 100
    return result(metadata, value, "%", "percent excess weight loss after bariatric surgery")


def overactive_bladder_symptom_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    daytime_frequency = _integer_in_range(inputs, "daytime_frequency", 0, 2)
    nighttime_frequency = _integer_in_range(inputs, "nighttime_frequency", 0, 3)
    urgency = _integer_in_range(inputs, "urgency", 0, 5)
    urgency_incontinence = _integer_in_range(inputs, "urgency_incontinence", 0, 5)

    total = daytime_frequency + nighttime_frequency + urgency + urgency_incontinence
    severity = _range_label(
        total,
        (
            (0, 5, "mild"),
            (6, 11, "moderate"),
            (12, 15, "severe"),
        ),
    )
    oab_diagnostic_support = urgency >= 2 and total >= 3

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total,
            "severity": severity,
            "oab_diagnostic_support": oab_diagnostic_support,
            "components": {
                "daytime_frequency": daytime_frequency,
                "nighttime_frequency": nighttime_frequency,
                "urgency": urgency,
                "urgency_incontinence": urgency_incontinence,
            },
        },
        unit="points",
        interpretation=(
            f"OABSS {total} points: {severity} symptoms; "
            f"OAB diagnostic support {'present' if oab_diagnostic_support else 'not present'} "
            "(requires urgency score >=2 and total score >=3)."
        ),
    )


def clarke_hypoglycemia_awareness_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _integer_in_range(inputs, "impaired_awareness_responses", 0, 8)

    if score >= 4:
        classification = "impaired awareness"
    elif score == 3:
        classification = "borderline awareness"
    else:
        classification = "normal awareness"

    impaired_awareness = score >= 4
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": score,
            "classification": classification,
            "impaired_awareness": impaired_awareness,
        },
        unit="responses",
        interpretation=f"Clarke hypoglycemia awareness score: {classification} ({score} impaired-awareness responses).",
    )


def single_pool_kt_v_daugirdas_ii(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    pre_bun_mg_dl = _positive_number(inputs, "pre_bun_mg_dl")
    post_bun_mg_dl = _positive_number(inputs, "post_bun_mg_dl")
    dialysis_hours = _positive_number(inputs, "dialysis_hours")
    ultrafiltration_l = _nonnegative_number(inputs, "ultrafiltration_l")
    post_weight_kg = _positive_number(inputs, "post_weight_kg")

    ratio = post_bun_mg_dl / pre_bun_mg_dl
    log_argument = ratio - 0.008 * dialysis_hours
    if log_argument <= 0:
        raise ValueError("R - 0.008*t must be positive")

    value = -math.log(log_argument) + (4 - 3.5 * ratio) * ultrafiltration_l / post_weight_kg
    return result(metadata, value, "Kt/V", "single-pool Kt/V by Daugirdas II formula")


def peritoneal_dialysis_ktv(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    serum_urea = _positive_number(inputs, "serum_urea_mg_dl")
    dialysate_urea = _nonnegative_number(inputs, "dialysate_urea_mg_dl")
    dialysate_volume = _nonnegative_number(inputs, "dialysate_volume_l")
    urine_urea = _nonnegative_number(inputs, "urine_urea_mg_dl")
    urine_volume = _nonnegative_number(inputs, "urine_volume_l")
    distribution_volume = _positive_number(inputs, "urea_distribution_volume_l")
    collection_hours = _positive_number(inputs, "collection_hours")

    factor = 168 / collection_hours
    dialysate_weekly = dialysate_urea / serum_urea * dialysate_volume / distribution_volume * factor
    residual_weekly = urine_urea / serum_urea * urine_volume / distribution_volume * factor
    total = dialysate_weekly + residual_weekly
    value = {
        "total_weekly_ktv": round(total, 4),
        "dialysate_weekly_ktv": round(dialysate_weekly, 4),
        "residual_weekly_ktv": round(residual_weekly, 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="weekly Kt/V",
        interpretation="Peritoneal dialysis weekly Kt/V combines dialysate and residual renal urea clearance.",
    )


def peritoneal_equilibration_test_category(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    creatinine_ratio = _nonnegative_number(inputs, "dialysate_plasma_creatinine_ratio_4h")
    glucose_ratio = _nonnegative_number(inputs, "dialysate_initial_glucose_ratio_4h")
    if creatinine_ratio >= 0.81:
        category = "high"
    elif creatinine_ratio >= 0.65:
        category = "high average"
    elif creatinine_ratio >= 0.50:
        category = "low average"
    else:
        category = "low"
    value = {
        "transport_category": category,
        "dialysate_plasma_creatinine_ratio_4h": creatinine_ratio,
        "dialysate_initial_glucose_ratio_4h": glucose_ratio,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="category",
        interpretation=f"Peritoneal equilibration test transport category: {category}.",
    )


def dan_pss_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "symptom_scores" not in inputs:
        raise KeyError("symptom_scores")
    if "bother_scores" not in inputs:
        raise KeyError("bother_scores")
    symptom_scores = inputs["symptom_scores"]
    bother_scores = inputs["bother_scores"]
    if isinstance(symptom_scores, (str, bytes)) or not isinstance(symptom_scores, Sequence):
        raise ValueError("symptom_scores must be a sequence")
    if isinstance(bother_scores, (str, bytes)) or not isinstance(bother_scores, Sequence):
        raise ValueError("bother_scores must be a sequence")
    if len(symptom_scores) != len(bother_scores):
        raise ValueError("symptom_scores and bother_scores must have the same length")

    item_scores = []
    for index, (symptom, bother) in enumerate(zip(symptom_scores, bother_scores)):
        symptom_value = _integer_value(symptom, f"symptom_scores[{index}]")
        bother_value = _integer_value(bother, f"bother_scores[{index}]")
        if symptom_value < 0 or bother_value < 0:
            raise ValueError("DAN-PSS symptom and bother scores must be nonnegative")
        item_scores.append(symptom_value * bother_value)

    value = {"total_score": sum(item_scores), "item_scores": item_scores}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="DAN-PSS prescored symptom-bother product total; higher scores indicate greater burden.",
    )
