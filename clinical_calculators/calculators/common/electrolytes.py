from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def anion_gap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sodium = number(inputs, "sodium")
    chloride = number(inputs, "chloride")
    bicarbonate = number(inputs, "bicarbonate")
    value = sodium - (chloride + bicarbonate)
    return result(metadata, value, "mEq/L", "interpret against local laboratory reference range and albumin level")


def corrected_sodium_hyperglycemia(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    measured_sodium = number(inputs, "measured_sodium")
    glucose_mg_dl = number(inputs, "glucose_mg_dl")
    value = measured_sodium + 0.016 * (glucose_mg_dl - 100)
    return result(metadata, value, "mEq/L", "corrected sodium estimate for hyperglycemia")


def corrected_calcium_hypoalbuminemia_si(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    calcium_mmol_l = number(inputs, "calcium_mmol_l")
    albumin_g_l = number(inputs, "albumin_g_l")
    # Payne-style corrected calcium convention in SI units.
    value = calcium_mmol_l + 0.02 * (40 - albumin_g_l)
    return result(metadata, value, "mmol/L", "albumin-corrected total calcium estimate")


def estimated_serum_osmolality(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sodium_mmol_l = number(inputs, "sodium_mmol_l")
    glucose_mmol_l = number(inputs, "glucose_mmol_l")
    bun_mmol_l = number(inputs, "bun_mmol_l")
    # Standard clinical chemistry/nephrology SI osmolality estimate.
    value = 2 * sodium_mmol_l + glucose_mmol_l + bun_mmol_l
    return result(metadata, value, "mOsm/kg", "estimated serum osmolality")


def effective_plasma_osmolality(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sodium_mmol_l = number(inputs, "sodium_mmol_l")
    glucose_mmol_l = number(inputs, "glucose_mmol_l")
    # Standard nephrology tonicity formula excludes urea/BUN.
    value = 2 * sodium_mmol_l + glucose_mmol_l
    return result(metadata, value, "mOsm/kg", "effective plasma osmolality estimate")


def osmolal_gap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    measured_osmolality_mosm_kg = number(inputs, "measured_osmolality_mosm_kg")
    estimated_osmolality_mosm_kg = number(inputs, "estimated_osmolality_mosm_kg")
    # Standard osmolal gap: measured osmolality minus calculated estimate.
    value = measured_osmolality_mosm_kg - estimated_osmolality_mosm_kg
    return result(metadata, value, "mOsm/kg", "measured minus estimated serum osmolality")
