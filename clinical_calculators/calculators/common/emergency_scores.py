from __future__ import annotations

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


def _boolean_flag(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0:
        return False
    if value == 1:
        return True
    raise ValueError(f"{key} must be a boolean or 0/1")


def glasgow_coma_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    eye = _integer_in_range(inputs, "eye", 1, 4)
    verbal = _integer_in_range(inputs, "verbal", 1, 5)
    motor = _integer_in_range(inputs, "motor", 1, 6)

    score = eye + verbal + motor
    if score <= 8:
        interpretation = "severe coma severity by Glasgow Coma Scale"
    elif score <= 12:
        interpretation = "moderate coma severity by Glasgow Coma Scale"
    else:
        interpretation = "mild coma severity by Glasgow Coma Scale"

    return result(metadata, score, "points", interpretation)


def qsofa_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "respiratory_rate") >= 22:
        score += 1
    if number(inputs, "systolic_bp") <= 100:
        score += 1
    if _boolean_flag(inputs, "altered_mentation"):
        score += 1

    if score >= 2:
        interpretation = "higher risk; prompt sepsis evaluation is indicated"
    else:
        interpretation = "lower qSOFA risk; continue clinical assessment"

    return result(metadata, score, "points", interpretation)


def curb_65(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _boolean_flag(inputs, "confusion"):
        score += 1
    if number(inputs, "urea_mmol_l") > 7:
        score += 1
    if number(inputs, "respiratory_rate") >= 30:
        score += 1
    if number(inputs, "systolic_bp") < 90 or number(inputs, "diastolic_bp") <= 60:
        score += 1
    if number(inputs, "age_years") >= 65:
        score += 1

    if score <= 1:
        interpretation = "low risk by CURB-65"
    elif score == 2:
        interpretation = "moderate risk by CURB-65"
    else:
        interpretation = "severe/high risk by CURB-65"

    return result(metadata, score, "points", interpretation)
