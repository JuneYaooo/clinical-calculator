from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _optional_integer_in_range(
    inputs: dict[str, Any], key: str, default: int, minimum: int, maximum: int
) -> int:
    if key not in inputs or inputs[key] is None:
        return default
    return _integer_in_range(inputs, key, minimum, maximum)


def _boolean_flag(inputs: dict[str, Any], key: str, default: bool | None = None) -> bool:
    if key not in inputs:
        if default is None:
            raise KeyError(key)
        return default

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0:
        return False
    if value == 1:
        return True
    raise ValueError(f"{key} must be a boolean or 0/1")


def _band_score(value: float, bands: tuple[tuple[float, float | None, int], ...]) -> int:
    for minimum, maximum, score in bands:
        if value >= minimum and (maximum is None or value <= maximum):
            return score
    raise ValueError("value is outside the supported scoring range")


def _sequence_of_integer_points(
    inputs: dict[str, Any],
    key: str,
    *,
    minimum_items: int | None = None,
    allowed_points: set[int] | None = None,
    minimum: int = 0,
    maximum: int | None = None,
) -> list[int]:
    raw = inputs.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{key} must be a sequence of coded point values")
    if minimum_items is not None and len(raw) != minimum_items:
        raise ValueError(f"{key} must contain {minimum_items} coded point values")

    points = []
    for index, value in enumerate(raw):
        if isinstance(value, bool):
            raise ValueError(f"{key}[{index}] must be an integer point value")
        numeric_value = float(value)
        if not numeric_value.is_integer():
            raise ValueError(f"{key}[{index}] must be an integer point value")
        point = int(numeric_value)
        if allowed_points is not None and point not in allowed_points:
            allowed = ", ".join(str(item) for item in sorted(allowed_points))
            raise ValueError(f"{key}[{index}] must be one of: {allowed}")
        if point < minimum or (maximum is not None and point > maximum):
            raise ValueError(f"{key}[{index}] must be between {minimum} and {maximum}")
        points.append(point)
    return points


def _logistic_percent(logit: float) -> float:
    return round(100 / (1 + math.exp(-logit)), 1)


def _news2_spo2_scale_1_score(spo2: float) -> int:
    if spo2 <= 91:
        return 3
    if spo2 <= 93:
        return 2
    if spo2 <= 95:
        return 1
    return 0


def news2_early_warning_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    spo2_scale = _optional_integer_in_range(inputs, "spo2_scale", default=1, minimum=1, maximum=2)
    if spo2_scale != 1:
        raise ValueError("spo2_scale 2 is not implemented; provide scale 1 component inputs only")

    consciousness = str(inputs["consciousness"]).strip().lower()

    score = 0
    score += _band_score(
        number(inputs, "respiratory_rate"),
        ((float("-inf"), 8, 3), (9, 11, 1), (12, 20, 0), (21, 24, 2), (25, None, 3)),
    )
    score += _news2_spo2_scale_1_score(number(inputs, "oxygen_saturation_percent"))
    if _boolean_flag(inputs, "supplemental_oxygen"):
        score += 2
    score += _band_score(
        number(inputs, "temperature_c"),
        (
            (float("-inf"), 35, 3),
            (35.1, 36, 1),
            (36.1, 38, 0),
            (38.1, 39, 1),
            (39.1, None, 2),
        ),
    )
    score += _band_score(
        number(inputs, "systolic_bp"),
        ((float("-inf"), 90, 3), (91, 100, 2), (101, 110, 1), (111, 219, 0), (220, None, 3)),
    )
    score += _band_score(
        number(inputs, "heart_rate"),
        ((float("-inf"), 40, 3), (41, 50, 1), (51, 90, 0), (91, 110, 1), (111, 130, 2), (131, None, 3)),
    )
    if consciousness != "alert":
        score += 3

    if score >= 7:
        interpretation = "NEWS2 high risk; urgent clinical response is indicated."
    elif score >= 5:
        interpretation = "NEWS2 medium risk; prompt clinical review is indicated."
    else:
        interpretation = "NEWS2 low risk; continue routine monitoring and clinical judgment."

    return result(metadata, score, "points", interpretation)


def peradeniya_organophosphorus_poisoning_scale(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    pupil_size = _integer_in_range(inputs, "pupil_size", 0, 2)
    respiratory_rate = _integer_in_range(inputs, "respiratory_rate", 0, 2)
    heart_rate = _integer_in_range(inputs, "heart_rate", 0, 1)
    fasciculations = _integer_in_range(inputs, "fasciculations", 0, 2)
    level_of_consciousness = _integer_in_range(inputs, "level_of_consciousness", 0, 2)
    seizures = _integer_in_range(inputs, "seizures", 0, 1)

    total = pupil_size + respiratory_rate + heart_rate + fasciculations + level_of_consciousness + seizures
    if total <= 3:
        severity = "mild"
    elif total <= 7:
        severity = "moderate"
    else:
        severity = "severe"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total,
            "severity": severity,
            "components": {
                "pupil_size": pupil_size,
                "respiratory_rate": respiratory_rate,
                "heart_rate": heart_rate,
                "fasciculations": fasciculations,
                "level_of_consciousness": level_of_consciousness,
                "seizures": seizures,
            },
        },
        unit="points",
        interpretation=(
            f"Peradeniya Organophosphorus Poisoning Scale: {severity} poisoning "
            f"({total} points; mild 0-3, moderate 4-7, severe 8-11)."
        ),
    )


def sofa_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    component_keys = ("respiration", "coagulation", "liver", "cardiovascular", "cns", "renal")
    score = sum(_integer_in_range(inputs, key, 0, 4) for key in component_keys)
    return result(
        metadata,
        score,
        "points",
        "SOFA total from provided component points; higher score indicates greater organ dysfunction.",
    )


def revised_trauma_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    gcs = number(inputs, "gcs")
    systolic_bp = number(inputs, "systolic_bp")
    respiratory_rate = number(inputs, "respiratory_rate")

    if gcs >= 13:
        gcs_code = 4
    elif gcs >= 9:
        gcs_code = 3
    elif gcs >= 6:
        gcs_code = 2
    elif gcs >= 4:
        gcs_code = 1
    else:
        gcs_code = 0

    if systolic_bp > 89:
        sbp_code = 4
    elif systolic_bp >= 76:
        sbp_code = 3
    elif systolic_bp >= 50:
        sbp_code = 2
    elif systolic_bp >= 1:
        sbp_code = 1
    else:
        sbp_code = 0

    if respiratory_rate >= 10 and respiratory_rate <= 29:
        rr_code = 4
    elif respiratory_rate > 29:
        rr_code = 3
    elif respiratory_rate >= 6:
        rr_code = 2
    elif respiratory_rate >= 1:
        rr_code = 1
    else:
        rr_code = 0

    score = 0.9368 * gcs_code + 0.7326 * sbp_code + 0.2908 * rr_code
    return result(metadata, score, "points", "Weighted Revised Trauma Score; higher score indicates less severe physiologic injury.")


def rass_sedation_agitation_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "score", -5, 4)
    labels = {
        4: "combative",
        3: "very agitated",
        2: "agitated",
        1: "restless",
        0: "alert and calm",
        -1: "drowsy",
        -2: "light sedation",
        -3: "moderate sedation",
        -4: "deep sedation",
        -5: "unarousable",
    }
    return result(metadata, score, "points", f"RASS: {labels[score]}.")


def asa_physical_status_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    asa_class = _integer_in_range(inputs, "class", 1, 6)
    emergency = _boolean_flag(inputs, "emergency", default=False)
    labels = {
        1: "normal healthy patient",
        2: "mild systemic disease",
        3: "severe systemic disease",
        4: "severe systemic disease that is a constant threat to life",
        5: "moribund patient not expected to survive without the operation",
        6: "declared brain-dead patient whose organs are being removed for donor purposes",
    }

    modifier = " Emergency modifier (E) present." if emergency else ""
    return result(metadata, asa_class, "class", f"ASA class {asa_class}: {labels[asa_class]}.{modifier}")


def _creatinine_ratio_and_increase(inputs: dict[str, Any]) -> tuple[float, float]:
    baseline = number(inputs, "baseline_creatinine_mg_dl")
    current = number(inputs, "current_creatinine_mg_dl")
    if baseline <= 0 or current < 0:
        raise ValueError("creatinine values must be nonnegative and baseline must be greater than 0")
    return current / baseline, current - baseline


def _urine_output_inputs(inputs: dict[str, Any]) -> tuple[float, float, float]:
    urine_output = number(inputs, "urine_output_ml_kg_hr")
    duration = number(inputs, "urine_output_duration_hours")
    anuria = number(inputs, "anuria_duration_hours")
    if urine_output < 0 or duration < 0 or anuria < 0:
        raise ValueError("urine output and duration inputs must be nonnegative")
    return urine_output, duration, anuria


def akin_acute_kidney_injury_stage(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ratio, increase = _creatinine_ratio_and_increase(inputs)
    urine_output, urine_duration, anuria_duration = _urine_output_inputs(inputs)

    creatinine_stage = 0
    if ratio > 3 or (number(inputs, "current_creatinine_mg_dl") >= 4 and increase >= 0.5):
        creatinine_stage = 3
    elif ratio > 2:
        creatinine_stage = 2
    elif ratio >= 1.5 or increase >= 0.3:
        creatinine_stage = 1

    urine_stage = 0
    if urine_output < 0.3 and urine_duration >= 24 or anuria_duration >= 12:
        urine_stage = 3
    elif urine_output < 0.5 and urine_duration >= 12:
        urine_stage = 2
    elif urine_output < 0.5 and urine_duration > 6:
        urine_stage = 1

    rrt = _boolean_flag(inputs, "renal_replacement_therapy", default=False)
    stage = max(creatinine_stage, urine_stage, 3 if rrt else 0)
    value = {
        "stage": stage,
        "creatinine_stage": creatinine_stage,
        "urine_output_stage": urine_stage,
        "renal_replacement_therapy": rrt,
    }
    interpretation = f"AKIN acute kidney injury stage {stage}."
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="stage",
        interpretation=interpretation,
    )


def rifle_acute_kidney_injury_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    ratio, increase = _creatinine_ratio_and_increase(inputs)
    urine_output, urine_duration, anuria_duration = _urine_output_inputs(inputs)
    current = number(inputs, "current_creatinine_mg_dl")

    creatinine_class = 0
    if ratio >= 3 or (current >= 4 and increase >= 0.5):
        creatinine_class = 3
    elif ratio >= 2:
        creatinine_class = 2
    elif ratio >= 1.5:
        creatinine_class = 1

    urine_class = 0
    if (urine_output < 0.3 and urine_duration >= 24) or anuria_duration >= 12:
        urine_class = 3
    elif urine_output < 0.5 and urine_duration >= 12:
        urine_class = 2
    elif urine_output < 0.5 and urine_duration >= 6:
        urine_class = 1

    class_index = max(creatinine_class, urine_class)
    labels = {0: "no RIFLE AKI class", 1: "risk", 2: "injury", 3: "failure"}
    value = {
        "class": labels[class_index],
        "creatinine_class": labels[creatinine_class],
        "urine_output_class": labels[urine_class],
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="class",
        interpretation=f"RIFLE acute kidney injury classification: {labels[class_index]}.",
    )


def apache_ii_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    acute_physiology_score = _integer_in_range(inputs, "acute_physiology_score", 0, 60)
    age_years = number(inputs, "age_years")
    if age_years < 0:
        raise ValueError("age_years must be nonnegative")

    if age_years >= 75:
        age_points = 6
    elif age_years >= 65:
        age_points = 5
    elif age_years >= 55:
        age_points = 3
    elif age_years >= 45:
        age_points = 2
    else:
        age_points = 0

    chronic_health_points = _integer_in_range(inputs, "chronic_health_points", 0, 5)
    if chronic_health_points not in {0, 2, 5}:
        raise ValueError("chronic_health_points must be coded as 0, 2, or 5")

    score = acute_physiology_score + age_points + chronic_health_points
    value = {
        "score": score,
        "acute_physiology_score": acute_physiology_score,
        "age_points": age_points,
        "chronic_health_points": chronic_health_points,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="APACHE II total score from pre-scored acute physiology, age, and chronic health points.",
    )


def saps_ii_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    component_points = _sequence_of_integer_points(inputs, "component_points", minimum=0)
    if not component_points:
        raise ValueError("component_points must contain at least one coded point value")

    score = sum(component_points)
    if score > 163:
        raise ValueError("SAPS II total score cannot exceed 163")

    logit = (0.0737 * score) + (0.9971 * math.log(score + 1)) - 7.7631
    value = {
        "score": score,
        "mortality_probability_percent": _logistic_percent(logit),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="SAPS II total from pre-scored components with original hospital mortality equation.",
    )


def nutric_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")
    apache_score = number(inputs, "apache_ii_score")
    sofa = number(inputs, "sofa_score")
    comorbidities = _integer_in_range(inputs, "comorbidities", 0, 100)
    days_to_icu = number(inputs, "days_from_hospital_to_icu")
    if age_years < 0 or apache_score < 0 or sofa < 0 or days_to_icu < 0:
        raise ValueError("age, APACHE II, SOFA, and hospital-to-ICU days must be nonnegative")

    if age_years >= 75:
        age_points = 2
    elif age_years >= 50:
        age_points = 1
    else:
        age_points = 0

    if apache_score >= 28:
        apache_points = 3
    elif apache_score >= 20:
        apache_points = 2
    elif apache_score >= 15:
        apache_points = 1
    else:
        apache_points = 0

    if sofa >= 10:
        sofa_points = 2
    elif sofa >= 6:
        sofa_points = 1
    else:
        sofa_points = 0

    comorbidity_points = 1 if comorbidities >= 2 else 0
    hospital_points = 1 if days_to_icu >= 1 else 0
    il6_points = 0
    modified = True
    if "il6_pg_ml" in inputs and inputs["il6_pg_ml"] is not None:
        il6 = number(inputs, "il6_pg_ml")
        if il6 < 0:
            raise ValueError("il6_pg_ml must be nonnegative")
        il6_points = 1 if il6 >= 400 else 0
        modified = False

    score = age_points + apache_points + sofa_points + comorbidity_points + hospital_points + il6_points
    high_risk = score >= (5 if modified else 6)
    value = {
        "score": score,
        "max_score": 9 if modified else 10,
        "modified": modified,
        "high_nutrition_risk": high_risk,
    }
    label = "modified NUTRIC" if modified else "NUTRIC"
    risk = "high nutrition risk" if high_risk else "lower nutrition risk"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"{label} score {score}: {risk}.",
    )


def icdsc_delirium_screening_checklist(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    item_scores = _sequence_of_integer_points(
        inputs,
        "item_scores",
        minimum_items=8,
        allowed_points={0, 1},
    )
    score = sum(item_scores)
    label = "positive delirium screen" if score >= 4 else "below positive delirium screen cutoff"
    return result(metadata, score, "points", f"ICDSC score {score}: {label}.")


def extrip_lithium_ectr_indication(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    lithium = number(inputs, "lithium_mmol_l")
    expected_clearance_hours = number(inputs, "expected_time_to_lithium_below_1_mmol_l_hours")
    if lithium < 0:
        raise ValueError("lithium_mmol_l must be nonnegative")
    if expected_clearance_hours < 0:
        raise ValueError("expected_time_to_lithium_below_1_mmol_l_hours must be nonnegative")

    criteria_met: list[str] = []
    recommended = False
    if _boolean_flag(inputs, "impaired_kidney_function") and lithium > 4:
        recommended = True
        criteria_met.append("impaired_kidney_function_and_lithium_gt_4")
    for key in (
        "decreased_level_of_consciousness",
        "seizure",
        "life_threatening_dysrhythmia",
    ):
        if _boolean_flag(inputs, key):
            recommended = True
            criteria_met.append(key)

    suggested = False
    if lithium > 5:
        suggested = True
        criteria_met.append("lithium_gt_5")
    if _boolean_flag(inputs, "significant_confusion"):
        suggested = True
        criteria_met.append("significant_confusion")
    if expected_clearance_hours > 36:
        suggested = True
        criteria_met.append("expected_clearance_time_gt_36_hours")

    if recommended:
        recommendation = "recommended"
    elif suggested:
        recommendation = "suggested"
    else:
        recommendation = "not indicated by supplied EXTRIP criteria"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"recommendation": recommendation, "criteria_met": criteria_met},
        unit="recommendation",
        interpretation=f"Extracorporeal treatment for lithium poisoning is {recommendation}.",
    )


def dn4_neuropathic_pain_screen(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    item_scores = _sequence_of_integer_points(
        inputs,
        "item_scores",
        minimum_items=10,
        allowed_points={0, 1},
    )
    score = sum(item_scores)
    label = "positive neuropathic pain screen" if score >= 4 else "below positive neuropathic pain cutoff"
    return result(metadata, score, "points", f"DN4 score {score}: {label}.")
