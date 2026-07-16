from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _bounded_int(inputs: dict[str, Any], key: str, low: int, high: int) -> int:
    value = int(number(inputs, key))
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}")
    return value


def silverman_andersen_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = (
        "chest_abdominal_movement",
        "intercostal_retractions",
        "xiphoid_retractions",
        "nasal_flaring",
        "expiratory_grunt",
    )
    score = sum(_bounded_int(inputs, key, 0, 2) for key in keys)
    if score <= 3:
        interpretation = "mild respiratory distress"
    elif score <= 6:
        interpretation = "moderate respiratory distress"
    else:
        interpretation = "severe respiratory distress"
    return result(metadata, score, "points", interpretation)


def clinical_dehydration_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_bounded_int(inputs, key, 0, 2) for key in ("general_appearance", "eyes", "mucous_membranes", "tears"))
    if score == 0:
        interpretation = "no dehydration"
    elif score <= 4:
        interpretation = "mild/moderate dehydration"
    else:
        interpretation = "severe dehydration"
    return result(metadata, score, "points", interpretation)


def lams_los_angeles_motor_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(bool(inputs.get("facial_droop", False)))
    score += _bounded_int(inputs, "arm_drift", 0, 2)
    score += _bounded_int(inputs, "grip_strength", 0, 2)
    return result(metadata, score, "points", "higher score suggests more severe motor stroke deficit")


def four_coma_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_bounded_int(inputs, key, 0, 4) for key in ("eye", "motor", "brainstem", "respiration"))
    interpretation = "less impaired consciousness" if score >= 13 else "more impaired consciousness"
    return result(metadata, score, "points", interpretation)


def ovarian_malignancy_risk_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "ultrasound_score") * number(inputs, "menopausal_score") * _positive(inputs, "ca125_u_ml")
    interpretation = "higher ovarian malignancy risk" if value >= 200 else "lower ovarian malignancy risk"
    return result(metadata, value, "score", interpretation)


def sflt1_plgf_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _positive(inputs, "sflt1_pg_ml") / _positive(inputs, "plgf_pg_ml")
    return result(metadata, value, "ratio", "sFlt-1 to PlGF ratio")


def pediatric_percent_bmi95(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "bmi") / _positive(inputs, "bmi_95th_percentile") * 100
    if value >= 140:
        interpretation = "class 3 severe obesity range"
    elif value >= 120:
        interpretation = "severe obesity range"
    elif value >= 100:
        interpretation = "at or above obesity threshold"
    else:
        interpretation = "below obesity threshold"
    return result(metadata, value, "% of 95th percentile", interpretation)


def simplified_pesi_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(number(inputs, "age_years") > 80)
    score += int(bool(inputs.get("history_of_cancer", False)))
    score += int(bool(inputs.get("chronic_cardiopulmonary_disease", False)))
    score += int(number(inputs, "heart_rate") >= 110)
    score += int(number(inputs, "systolic_bp") < 100)
    score += int(number(inputs, "oxygen_saturation_percent") < 90)
    interpretation = "low risk" if score == 0 else "high risk"
    return result(metadata, score, "points", interpretation)


def tof_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "t4_amplitude") / _positive(inputs, "t1_amplitude")
    interpretation = "commonly compatible with neuromuscular recovery target" if value >= 0.9 else "below common recovery target"
    return result(metadata, value, "ratio", interpretation)
