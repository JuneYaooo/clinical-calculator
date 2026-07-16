from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


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


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _category_points(inputs: dict[str, Any], key: str, point_map: dict[str, int]) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if value not in point_map:
        allowed = ", ".join(sorted(point_map))
        raise ValueError(f"{key} must be one of: {allowed}")
    return point_map[value]


def _points_from_allowed(inputs: dict[str, Any], key: str, allowed: set[int]) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    points = int(value)
    if points not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
    return points


def apri_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ast = number(inputs, "ast_u_l")
    ast_uln = _positive_number(inputs, "ast_uln_u_l")
    platelets = _positive_number(inputs, "platelets_10e9_l")

    value = (ast / ast_uln) / platelets * 100
    return result(metadata, value, "index", "APRI fibrosis index; interpret using disease-specific thresholds")


def fib_4_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = number(inputs, "age_years")
    ast = number(inputs, "ast_u_l")
    alt = _positive_number(inputs, "alt_u_l")
    platelets = _positive_number(inputs, "platelets_10e9_l")

    value = age * ast / (platelets * math.sqrt(alt))
    if value < 1.3:
        interpretation = "low risk of advanced fibrosis by FIB-4"
    elif value > 2.67:
        interpretation = "high risk of advanced fibrosis by FIB-4"
    else:
        interpretation = "indeterminate risk of advanced fibrosis by FIB-4"

    return result(metadata, value, "index", interpretation)


def maddrey_discriminant_function(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    prothrombin_time = number(inputs, "prothrombin_time_seconds")
    control_prothrombin_time = number(inputs, "control_prothrombin_time_seconds")
    bilirubin = number(inputs, "bilirubin_mg_dl")

    value = 4.6 * (prothrombin_time - control_prothrombin_time) + bilirubin
    if value >= 32:
        interpretation = "meets severe alcoholic hepatitis threshold commonly used for Maddrey DF"
    else:
        interpretation = "below severe alcoholic hepatitis threshold commonly used for Maddrey DF"

    return result(metadata, value, "points", interpretation)


def child_pugh_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bilirubin = number(inputs, "bilirubin_mg_dl")
    albumin = number(inputs, "albumin_g_dl")
    inr = number(inputs, "inr")

    score = 0
    if bilirubin < 2:
        score += 1
    elif bilirubin <= 3:
        score += 2
    else:
        score += 3

    if albumin > 3.5:
        score += 1
    elif albumin >= 2.8:
        score += 2
    else:
        score += 3

    if inr < 1.7:
        score += 1
    elif inr <= 2.3:
        score += 2
    else:
        score += 3

    score += _category_points(
        inputs,
        "ascites",
        {
            "none": 1,
            "mild": 2,
            "moderate_severe": 3,
        },
    )
    score += _category_points(
        inputs,
        "encephalopathy",
        {
            "none": 1,
            "grade_1_2": 2,
            "grade_3_4": 3,
        },
    )

    if score <= 6:
        child_pugh_class = "Class A"
    elif score <= 9:
        child_pugh_class = "Class B"
    else:
        child_pugh_class = "Class C"

    return result(metadata, score, "points", f"Child-Pugh {child_pugh_class}")


def bisap_acute_pancreatitis_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "bun_mg_dl") > 25:
        score += 1
    if _boolean_flag(inputs, "impaired_mental_status"):
        score += 1
    if _boolean_flag(inputs, "sirs"):
        score += 1
    if number(inputs, "age_years") > 60:
        score += 1
    if _boolean_flag(inputs, "pleural_effusion"):
        score += 1

    return result(metadata, score, "points", "BISAP acute pancreatitis severity score")


def lille_model_alcoholic_hepatitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _non_negative_number(inputs, "age_years")
    albumin = _non_negative_number(inputs, "albumin_g_l")
    bilirubin_day0 = _non_negative_number(inputs, "bilirubin_day0_umol_l")
    bilirubin_day7 = _non_negative_number(inputs, "bilirubin_day7_umol_l")
    prothrombin_time = _non_negative_number(inputs, "prothrombin_time_seconds")
    renal_insufficiency = 1 if _boolean_flag(inputs, "renal_insufficiency") else 0

    r_value = (
        3.19
        - 0.101 * age
        + 0.147 * albumin
        + 0.0165 * (bilirubin_day0 - bilirubin_day7)
        - 0.206 * renal_insufficiency
        - 0.0065 * bilirubin_day0
        - 0.0096 * prothrombin_time
    )
    value = math.exp(-r_value) / (1 + math.exp(-r_value))
    interpretation = (
        "likely corticosteroid responder by Lille model"
        if value < 0.45
        else "likely corticosteroid non-responder by Lille model"
    )
    return result(metadata, value, "probability", interpretation)


def autoimmune_hepatitis_simplified_diagnostic_criteria(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = (
        _points_from_allowed(inputs, "autoantibodies", {0, 1, 2})
        + _points_from_allowed(inputs, "igg", {0, 1, 2})
        + _points_from_allowed(inputs, "liver_histology", {0, 1, 2})
        + _points_from_allowed(inputs, "viral_hepatitis_absent", {0, 2})
    )
    probable = score >= 6
    definite = score >= 7
    value = {
        "score": score,
        "probable_autoimmune_hepatitis": probable,
        "definite_autoimmune_hepatitis": definite,
    }
    if definite:
        classification = "definite autoimmune hepatitis"
    elif probable:
        classification = "probable autoimmune hepatitis"
    else:
        classification = "below simplified autoimmune hepatitis threshold"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"Simplified autoimmune hepatitis score {score}: {classification}.",
    )
