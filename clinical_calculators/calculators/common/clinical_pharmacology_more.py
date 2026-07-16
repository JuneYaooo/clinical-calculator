from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import boolean, number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def carboplatin_calvert_dose(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    target_auc = _positive(inputs, "target_auc_mg_ml_min")
    gfr = _positive(inputs, "gfr_ml_min")
    dose = target_auc * (gfr + 25)
    return result(metadata, dose, "mg", "carboplatin dose by Calvert formula")


def sodium_bicarbonate_deficit(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight = _positive(inputs, "weight_kg")
    current_bicarbonate = number(inputs, "current_bicarbonate_mEq_l")
    target_bicarbonate = number(inputs, "target_bicarbonate_mEq_l")
    if target_bicarbonate < current_bicarbonate:
        raise ValueError("target_bicarbonate_mEq_l must be greater than or equal to current_bicarbonate_mEq_l")

    deficit = 0.5 * weight * (target_bicarbonate - current_bicarbonate)
    return result(metadata, deficit, "mEq", "estimated sodium bicarbonate deficit")


def levothyroxine_full_replacement_dose(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight = _positive(inputs, "weight_kg")
    factor = float(inputs.get("dose_factor_mcg_kg_day", 1.6))
    if factor <= 0:
        raise ValueError("dose_factor_mcg_kg_day must be positive")
    dose = weight * factor
    return result(metadata, dose, "mcg/day", "estimated full-replacement levothyroxine starting dose")


def morphine_milligram_equivalents(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    dose = _positive(inputs, "dose_mg_per_administration")
    administrations = _positive(inputs, "administrations_per_day")
    conversion_factor = _positive(inputs, "mme_conversion_factor")
    mme_per_day = dose * administrations * conversion_factor
    return result(metadata, mme_per_day, "MME/day", "estimated total daily morphine milligram equivalents")


def vancomycin_auc_mic_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    auc24 = _positive(inputs, "auc24_mg_h_l")
    mic = _positive(inputs, "mic_mg_l")
    auc_mic = auc24 / mic
    return result(metadata, auc_mic, "AUC/MIC", "vancomycin AUC24 divided by MIC")


def corrected_phenytoin_level(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    measured = _positive(inputs, "measured_total_phenytoin_mcg_ml")
    albumin = _positive(inputs, "albumin_g_dl")
    renal_failure = boolean(inputs, "renal_failure", default=False)
    coefficient = 0.2 if renal_failure else 0.275
    corrected = measured / ((coefficient * albumin) + 0.1)
    value = {
        "corrected_total_phenytoin_mcg_ml": round(corrected, 4),
        "coefficient": coefficient,
        "renal_failure": renal_failure,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="mcg/mL",
        interpretation="Corrected total phenytoin concentration using albumin-adjusted Sheiner-Tozer style equation.",
    )


__all__ = [
    "carboplatin_calvert_dose",
    "corrected_phenytoin_level",
    "levothyroxine_full_replacement_dose",
    "morphine_milligram_equivalents",
    "sodium_bicarbonate_deficit",
    "vancomycin_auc_mic_ratio",
]
