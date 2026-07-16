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


def _nonnegative(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return value


def _urea_reduction_ratio(inputs: dict[str, Any]) -> float:
    pre_bun = _positive(inputs, "pre_bun_mg_dl")
    post_bun = _positive(inputs, "post_bun_mg_dl")
    if post_bun >= pre_bun:
        raise ValueError("post_bun_mg_dl must be less than pre_bun_mg_dl")
    return (pre_bun - post_bun) / pre_bun


def hemodialysis_kt_v_lowrie(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = math.log(_positive(inputs, "pre_bun_mg_dl") / _positive(inputs, "post_bun_mg_dl"))
    return result(metadata, value, "Kt/V", "Lowrie urea clearance index")


def hemodialysis_kt_v_keshaviah(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 1.162 * math.log(_positive(inputs, "pre_bun_mg_dl") / _positive(inputs, "post_bun_mg_dl"))
    return result(metadata, value, "Kt/V", "Keshaviah urea clearance index")


def hemodialysis_kt_v_barth(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 3.1 * _urea_reduction_ratio(inputs) - 0.66
    return result(metadata, value, "Kt/V", "Barth urea clearance index")


def hemodialysis_kt_v_basile(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 2.3 * _urea_reduction_ratio(inputs) - 0.284
    return result(metadata, value, "Kt/V", "Basile urea clearance index")


def hemodialysis_kt_v_jindal(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 4 * _urea_reduction_ratio(inputs) - 1.2
    return result(metadata, value, "Kt/V", "Jindal urea clearance index")


def hemodialysis_kt_v_kerr(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 4.2 * _urea_reduction_ratio(inputs) - 1.48
    return result(metadata, value, "Kt/V", "Kerr urea clearance index")


def albumin_corrected_calcium_mg_dl(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "measured_calcium_mg_dl") + 0.8 * (
        number(inputs, "normal_albumin_g_dl") - number(inputs, "albumin_g_dl")
    )
    return result(metadata, value, "mg/dL", "albumin-corrected serum calcium")


def serum_sodium_change_per_liter_infusate(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    total_body_water = number(inputs, "total_body_water_fraction") * _positive(inputs, "weight_kg")
    value = (
        number(inputs, "infusate_sodium_mEq_l")
        + number(inputs, "infusate_potassium_mEq_l")
        - number(inputs, "serum_sodium_mEq_l")
    ) / (total_body_water + 1)
    return result(metadata, value, "mEq/L per L infusate", "Adrogue-Madias predicted sodium change per liter")


def hyponatremia_infusate_rate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    denominator = (
        number(inputs, "infusate_sodium_mEq_l")
        + number(inputs, "infusate_potassium_mEq_l")
        - number(inputs, "serum_sodium_mEq_l")
    )
    if denominator == 0:
        raise ValueError("infusate sodium plus potassium must differ from serum sodium")
    total_body_water = number(inputs, "total_body_water_fraction") * _positive(inputs, "weight_kg")
    value = 1000 * number(inputs, "desired_sodium_change_mEq_l_per_hour") * (total_body_water + 1) / denominator
    return result(metadata, value, "mL/hour", "predicted infusion rate for target serum sodium correction")


def serum_sodium_change_from_hypertriglyceridemia(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = number(inputs, "triglycerides_mg_dl") * 0.002
    return result(metadata, value, "mEq/L", "estimated sodium depression from hypertriglyceridemia")


def serum_sodium_change_from_hyperproteinemia(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = (number(inputs, "serum_protein_g_dl") - 8) * 0.25
    return result(metadata, value, "mEq/L", "estimated sodium depression from hyperproteinemia")


def urine_osmolal_gap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    measured_urine_osmolality = _positive(inputs, "measured_urine_osmolality_mOsm_kg")
    urine_sodium = _nonnegative(inputs, "urine_sodium_mEq_l")
    urine_potassium = _nonnegative(inputs, "urine_potassium_mEq_l")
    urine_urea_nitrogen = _nonnegative(inputs, "urine_urea_nitrogen_mg_dl")
    urine_glucose = _nonnegative(inputs, "urine_glucose_mg_dl")

    calculated_osmolality = 2 * (urine_sodium + urine_potassium) + urine_urea_nitrogen / 2.8 + urine_glucose / 18
    value = measured_urine_osmolality - calculated_osmolality
    return result(metadata, value, "mOsm/kg", "urine osmolal gap")


def estimated_urinary_ammonium(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = urine_osmolal_gap(metadata, inputs).value / 2
    return result(metadata, value, "mEq/L", "estimated urinary ammonium from urine osmolal gap divided by 2")
