from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import boolean, number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def risk_percent_from_log_odds(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    log_odds = number(inputs, "log_odds")
    value = 100 * (math.exp(log_odds) / (1 + math.exp(log_odds)))
    return result(metadata, value, "%", "risk converted from log odds")


def bang_diabetes_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    """Bang et al. self-assessment score for undiagnosed diabetes in US adults."""
    age_years = number(inputs, "age_years")
    if age_years < 20:
        raise ValueError("age_years must be at least 20 for the validated adult population")

    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")

    bmi = _positive(inputs, "bmi")
    if age_years < 40:
        age_points = 0
    elif age_years < 50:
        age_points = 1
    elif age_years < 60:
        age_points = 2
    else:
        age_points = 3

    if bmi < 25:
        bmi_points = 0
    elif bmi < 30:
        bmi_points = 1
    elif bmi < 40:
        bmi_points = 2
    else:
        bmi_points = 3

    score = age_points + bmi_points
    score += int(sex == "male")
    score += int(boolean(inputs, "family_history_diabetes"))
    score += int(boolean(inputs, "hypertension"))
    score -= int(boolean(inputs, "physically_active"))

    if score >= 5:
        interpretation = (
            "High risk for undiagnosed diabetes at the original selected cutoff (score >=5); "
            "offer diagnostic testing. This screening score does not diagnose diabetes."
        )
    else:
        interpretation = (
            "Below the original selected high-risk cutoff of 5; this does not exclude diabetes "
            "or override guideline-based testing."
        )
    return result(metadata, score, "points", interpretation)


def corrected_csf_protein_traumatic_tap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    correction = (
        number(inputs, "serum_protein_g_dl")
        * 1000
        * (1 - number(inputs, "hematocrit_percent") / 100)
        * number(inputs, "csf_rbc_per_uL")
        / (_positive(inputs, "blood_rbc_10e6_per_uL") * 1_000_000)
    )
    value = number(inputs, "csf_protein_mg_dl") - correction
    return result(metadata, max(value, 0), "mg/dL", "CSF protein corrected for traumatic tap blood contamination")


def pet_total_lesion_glycolysis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "mtv_ml") * number(inputs, "suv_mean")
    return result(metadata, value, "SUV*ml", "total lesion glycolysis")


def platelet_corrected_count_increment(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (
        number(inputs, "platelet_increment_10e9_l")
        * number(inputs, "body_surface_area_m2")
        / _positive(inputs, "platelets_transfused_10e11")
    )
    return result(metadata, value, "CCI", "platelet corrected count increment")


def mifflin_st_jeor_resting_energy_expenditure(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    value = 10 * number(inputs, "weight_kg") + 6.25 * number(inputs, "height_cm") - 5 * number(inputs, "age_years")
    value += 5 if sex == "male" else -161
    return result(metadata, value, "kcal/day", "Mifflin-St Jeor resting energy expenditure")


def age_adjusted_mac(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _positive(inputs, "mac_at_40") * (10 ** (-0.00269 * (number(inputs, "age_years") - 40)))
    value *= number(inputs, "target_mac_fraction")
    return result(metadata, value, "MAC", "age-adjusted minimum alveolar concentration")
