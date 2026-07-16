from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _sex_factor(inputs: dict[str, Any]) -> float:
    if "sex" not in inputs:
        raise KeyError("sex")

    sex = str(inputs["sex"]).strip().lower()
    if sex == "male":
        return 1.0
    if sex == "female":
        return 0.85
    raise ValueError("sex must be 'male' or 'female'")


def cockcroft_gault_creatinine_clearance(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")
    weight_kg = number(inputs, "weight_kg")
    serum_creatinine_mg_dl = number(inputs, "serum_creatinine_mg_dl")
    sex_factor = _sex_factor(inputs)

    # Cockcroft-Gault 1976 creatinine clearance estimate.
    value = ((140 - age_years) * weight_kg) / (72 * serum_creatinine_mg_dl) * sex_factor
    return result(metadata, value, "mL/min", "estimated creatinine clearance by Cockcroft-Gault equation")


def cockcroft_gault_creatinine_clearance_si(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")
    weight_kg = number(inputs, "weight_kg")
    serum_creatinine_umol_l = number(inputs, "serum_creatinine_umol_l")
    sex_factor = _sex_factor(inputs)

    serum_creatinine_mg_dl = serum_creatinine_umol_l / 88.4
    # Cockcroft-Gault 1976 creatinine clearance estimate; SI creatinine converted to mg/dL.
    value = ((140 - age_years) * weight_kg) / (72 * serum_creatinine_mg_dl) * sex_factor
    return result(metadata, value, "mL/min", "estimated creatinine clearance by Cockcroft-Gault equation")


def measured_creatinine_clearance(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_creatinine_mg_dl = number(inputs, "urine_creatinine_mg_dl")
    urine_volume_ml = number(inputs, "urine_volume_ml")
    serum_creatinine_mg_dl = number(inputs, "serum_creatinine_mg_dl")
    collection_minutes = number(inputs, "collection_minutes")

    # Measured CrCl standard clearance equation: urine concentration * flow / serum concentration.
    value = urine_creatinine_mg_dl * urine_volume_ml / (serum_creatinine_mg_dl * collection_minutes)
    return result(metadata, value, "mL/min", "measured creatinine clearance from timed urine collection")


def measured_creatinine_clearance_si(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_creatinine_mmol_l = number(inputs, "urine_creatinine_mmol_l")
    urine_volume_ml = number(inputs, "urine_volume_ml")
    serum_creatinine_umol_l = number(inputs, "serum_creatinine_umol_l")
    collection_minutes = number(inputs, "collection_minutes")

    urine_creatinine_umol_l = urine_creatinine_mmol_l * 1000
    # Measured CrCl standard clearance equation with urine creatinine converted from mmol/L to umol/L.
    value = urine_creatinine_umol_l * urine_volume_ml / (serum_creatinine_umol_l * collection_minutes)
    return result(metadata, value, "mL/min", "measured creatinine clearance from timed urine collection")


def fractional_excretion_sodium(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_sodium_mEq_l = number(inputs, "urine_sodium_mEq_l")
    serum_sodium_mEq_l = number(inputs, "serum_sodium_mEq_l")
    urine_creatinine_mg_dl = number(inputs, "urine_creatinine_mg_dl")
    serum_creatinine_mg_dl = number(inputs, "serum_creatinine_mg_dl")

    value = (urine_sodium_mEq_l * serum_creatinine_mg_dl) / (
        serum_sodium_mEq_l * urine_creatinine_mg_dl
    ) * 100
    return result(metadata, value, "%", "fractional excretion of sodium by concentration-ratio formula")


def fractional_excretion_sodium_si(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_sodium_mmol_l = number(inputs, "urine_sodium_mmol_l")
    serum_sodium_mmol_l = number(inputs, "serum_sodium_mmol_l")
    urine_creatinine_umol_l = number(inputs, "urine_creatinine_umol_l")
    serum_creatinine_umol_l = number(inputs, "serum_creatinine_umol_l")

    value = (urine_sodium_mmol_l * serum_creatinine_umol_l) / (
        serum_sodium_mmol_l * urine_creatinine_umol_l
    ) * 100
    return result(metadata, value, "%", "fractional excretion of sodium by concentration-ratio formula")


def fractional_excretion_urea(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_urea_mg_dl = number(inputs, "urine_urea_mg_dl")
    serum_urea_mg_dl = number(inputs, "serum_urea_mg_dl")
    urine_creatinine_mg_dl = number(inputs, "urine_creatinine_mg_dl")
    serum_creatinine_mg_dl = number(inputs, "serum_creatinine_mg_dl")

    value = (urine_urea_mg_dl * serum_creatinine_mg_dl) / (
        serum_urea_mg_dl * urine_creatinine_mg_dl
    ) * 100
    return result(metadata, value, "%", "fractional excretion of urea by concentration-ratio formula")


def sodium_deficit_hyponatremia(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight_kg = number(inputs, "weight_kg")
    current_sodium_mEq_l = number(inputs, "current_sodium_mEq_l")
    target_sodium_mEq_l = number(inputs, "target_sodium_mEq_l")
    total_body_water_fraction = float(inputs.get("total_body_water_fraction", 0.6))

    value = (target_sodium_mEq_l - current_sodium_mEq_l) * total_body_water_fraction * weight_kg
    return result(
        metadata,
        value,
        "mEq",
        "estimate only; sodium correction rate must be clinically supervised",
    )


def parkland_formula_adult(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight_kg = number(inputs, "weight_kg")
    tbsa_burn_percent = number(inputs, "tbsa_burn_percent")

    value = 4 * weight_kg * tbsa_burn_percent
    return result(
        metadata,
        value,
        "mL",
        "total lactated Ringer's for first 24h; "
        "give half in first 8h from burn time, remainder over next 16h",
    )
