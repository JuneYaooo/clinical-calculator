from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def serum_ascites_albumin_gradient(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    serum_albumin_g_dl = number(inputs, "serum_albumin_g_dl")
    ascites_albumin_g_dl = number(inputs, "ascites_albumin_g_dl")

    value = serum_albumin_g_dl - ascites_albumin_g_dl
    if value >= 1.1:
        interpretation = "SAAG >= 1.1 g/dL suggests a portal hypertension pattern"
    else:
        interpretation = "SAAG < 1.1 g/dL is below the common portal hypertension pattern threshold"

    return result(metadata, value, "g/dL", interpretation)


def total_body_water_estimate_by_weight(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight_kg = number(inputs, "weight_kg")
    fraction = float(inputs.get("fraction", 0.6))

    value = weight_kg * fraction
    return result(metadata, value, "L", "estimated total body water from weight fraction")


def female_total_body_water_watson_formula(
    metadata: CalculatorMetadata,
    inputs: dict[str, Any],
) -> CalculationResult:
    height_cm = number(inputs, "height_cm")
    weight_kg = number(inputs, "weight_kg")
    number(inputs, "age_years")

    value = -2.097 + 0.1069 * height_cm + 0.2466 * weight_kg
    return result(metadata, value, "L", "estimated total body water by Watson female equation")


def male_total_body_water_watson_formula(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    height_cm = number(inputs, "height_cm")
    weight_kg = number(inputs, "weight_kg")
    age_years = number(inputs, "age_years")

    value = 2.447 - 0.09516 * age_years + 0.1074 * height_cm + 0.3362 * weight_kg
    return result(metadata, value, "L", "estimated total body water by Watson male equation")


def free_water_deficit_hypernatremia(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight_kg = number(inputs, "weight_kg")
    current_sodium_mEq_l = number(inputs, "current_sodium_mEq_l")
    target_sodium_mEq_l = _positive_number(inputs, "target_sodium_mEq_l")
    total_body_water_fraction = float(inputs.get("total_body_water_fraction", 0.6))

    total_body_water = weight_kg * total_body_water_fraction
    value = total_body_water * (current_sodium_mEq_l / target_sodium_mEq_l - 1)
    return result(
        metadata,
        value,
        "L",
        "estimate only; correction requires clinical monitoring",
    )


def _body_mass_index(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return weight_kg / (height_m * height_m)


def lean_body_weight_female_janmahasatian(
    metadata: CalculatorMetadata,
    inputs: dict[str, Any],
) -> CalculationResult:
    height_cm = _positive_number(inputs, "height_cm")
    weight_kg = number(inputs, "weight_kg")

    bmi = _body_mass_index(weight_kg, height_cm)
    value = 9270 * weight_kg / (8780 + 244 * bmi)
    return result(metadata, value, "kg", "estimated lean body weight by Janmahasatian female equation")


def lean_body_weight_male_janmahasatian(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    height_cm = _positive_number(inputs, "height_cm")
    weight_kg = number(inputs, "weight_kg")

    bmi = _body_mass_index(weight_kg, height_cm)
    value = 9270 * weight_kg / (6680 + 216 * bmi)
    return result(metadata, value, "kg", "estimated lean body weight by Janmahasatian male equation")
