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


def _truthy(inputs: dict[str, Any], key: str) -> bool:
    return bool(inputs.get(key, False))


def revised_baux_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "age_years") + number(inputs, "tbsa_burn_percent")
    if _truthy(inputs, "inhalation_injury"):
        value += 17
    return result(metadata, value, "points", "higher score indicates higher burn mortality risk")


def abc_massive_transfusion_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(_truthy(inputs, "penetrating_mechanism"))
    score += int(_truthy(inputs, "positive_fast"))
    score += int(number(inputs, "systolic_bp") <= 90)
    score += int(number(inputs, "heart_rate") >= 120)
    interpretation = "higher likelihood of massive transfusion" if score >= 2 else "lower likelihood of massive transfusion"
    return result(metadata, score, "points", interpretation)


def obesity_surgery_mortality_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(number(inputs, "bmi") >= 50)
    score += int(_truthy(inputs, "male"))
    score += int(_truthy(inputs, "hypertension"))
    score += int(_truthy(inputs, "pulmonary_embolism_risk"))
    score += int(number(inputs, "age_years") >= 45)
    if score <= 1:
        risk_class = "class A"
    elif score <= 3:
        risk_class = "class B"
    else:
        risk_class = "class C"
    return result(metadata, score, "points", f"{risk_class} obesity surgery mortality risk")


def albi_grade(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0.66 * math.log10(_positive(inputs, "bilirubin_umol_l")) - 0.085 * number(inputs, "albumin_g_l")
    if value <= -2.60:
        grade = "grade 1"
    elif value <= -1.39:
        grade = "grade 2"
    else:
        grade = "grade 3"
    return result(metadata, value, "score", f"ALBI {grade}")


def palbi_grade(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bilirubin_log = math.log10(_positive(inputs, "bilirubin_umol_l"))
    platelet_log = math.log10(_positive(inputs, "platelets_10e9_l"))
    value = (
        2.02 * bilirubin_log
        - 0.37 * bilirubin_log**2
        - 0.04 * number(inputs, "albumin_g_l")
        - 3.48 * platelet_log
        + 1.01 * platelet_log**2
    )
    if value <= -2.53:
        grade = "grade 1"
    elif value <= -2.09:
        grade = "grade 2"
    else:
        grade = "grade 3"
    return result(metadata, value, "score", f"PALBI {grade}")


def nafld_fibrosis_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (
        -1.675
        + 0.037 * number(inputs, "age_years")
        + 0.094 * number(inputs, "bmi")
        + 1.13 * int(_truthy(inputs, "impaired_fasting_glucose_or_diabetes"))
        + 0.99 * (_positive(inputs, "ast_u_l") / _positive(inputs, "alt_u_l"))
        - 0.013 * _positive(inputs, "platelets_10e9_l")
        - 0.66 * number(inputs, "albumin_g_dl")
    )
    if value < -1.455:
        interpretation = "advanced fibrosis less likely"
    elif value <= 0.676:
        interpretation = "indeterminate advanced fibrosis risk"
    else:
        interpretation = "advanced fibrosis more likely"
    return result(metadata, value, "score", interpretation)


def bard_nafld_fibrosis_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = int(number(inputs, "bmi") >= 28)
    score += 2 * int(_positive(inputs, "ast_u_l") / _positive(inputs, "alt_u_l") >= 0.8)
    score += int(_truthy(inputs, "diabetes"))
    interpretation = "higher risk of advanced fibrosis" if score >= 2 else "lower risk of advanced fibrosis"
    return result(metadata, score, "points", interpretation)
