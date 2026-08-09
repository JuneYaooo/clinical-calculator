from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _lok_interpretation(value: float) -> str:
    if value < 0.2:
        return "cirrhosis less likely"
    if value <= 0.5:
        return "indeterminate cirrhosis probability"
    return "cirrhosis likely"


def lok_index_hepatitis_c_cirrhosis_probability(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    log_odds = (
        1.26 * _positive(inputs, "ast_u_l") / _positive(inputs, "alt_u_l")
        + 5.27 * number(inputs, "inr")
        - 0.0089 * _positive(inputs, "platelets_10e9_l")
        - 5.56
    )
    value = math.exp(log_odds) / (1 + math.exp(log_odds))
    return result(metadata, value, "probability", _lok_interpretation(value))


def guci_for_hepatitis_c_cirrhosis_probability(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = (_positive(inputs, "ast_u_l") / _positive(inputs, "ast_uln_u_l")) * number(inputs, "inr") * 100
    value /= _positive(inputs, "platelets_10e9_l")
    interpretation = "cirrhosis less likely" if value < 1 else "cirrhosis likely"
    return result(metadata, value, "score", interpretation)


def apri_for_hepatitis_c_cirrhosis_probability(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = (_positive(inputs, "ast_u_l") / _positive(inputs, "ast_uln_u_l")) * (
        100 / _positive(inputs, "platelets_10e9_l")
    )
    if value <= 0.5:
        interpretation = "significant fibrosis or cirrhosis less likely"
    elif value <= 1:
        interpretation = "significant fibrosis indeterminate; cirrhosis less likely"
    elif value <= 1.5:
        interpretation = "significant fibrosis likely; cirrhosis indeterminate"
    elif value <= 2:
        interpretation = "significant fibrosis likely; cirrhosis possible"
    else:
        interpretation = "significant fibrosis and cirrhosis likely"
    return result(metadata, value, "score", interpretation)


def fib4_for_hepatitis_c_cirrhosis_probability(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = number(inputs, "age_years") * _positive(inputs, "ast_u_l")
    value /= _positive(inputs, "platelets_10e9_l") * math.sqrt(_positive(inputs, "alt_u_l"))
    if value < 1.45:
        interpretation = "cirrhosis less likely"
    elif value <= 3.25:
        interpretation = "indeterminate cirrhosis probability"
    else:
        interpretation = "cirrhosis likely"
    return result(metadata, value, "score", interpretation)


def cirrhosis_discriminant_score_hepatitis_c(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    platelets = _positive(inputs, "platelets_10e9_l")
    alt_ast_ratio = _positive(inputs, "alt_u_l") / _positive(inputs, "ast_u_l")
    inr = number(inputs, "inr")
    if inr <= 0:
        raise ValueError("inr must be positive")

    if platelets > 340:
        platelet_points = 0
    elif platelets >= 280:
        platelet_points = 1
    elif platelets >= 220:
        platelet_points = 2
    elif platelets >= 160:
        platelet_points = 3
    elif platelets >= 100:
        platelet_points = 4
    elif platelets >= 40:
        platelet_points = 5
    else:
        platelet_points = 6

    if alt_ast_ratio > 1.7:
        ratio_points = 0
    elif alt_ast_ratio >= 1.2:
        ratio_points = 1
    elif alt_ast_ratio >= 0.6:
        ratio_points = 2
    else:
        ratio_points = 3

    if inr < 1.1:
        inr_points = 0
    elif inr <= 1.4:
        inr_points = 1
    else:
        inr_points = 2

    total_score = platelet_points + ratio_points + inr_points
    interpretation = "cirrhosis less likely" if total_score <= 7 else "cirrhosis likely"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total_score,
            "platelet_points": platelet_points,
            "alt_ast_ratio_points": ratio_points,
            "inr_points": inr_points,
        },
        unit="points",
        interpretation=f"Bonacini cirrhosis discriminant score: {interpretation}.",
    )
