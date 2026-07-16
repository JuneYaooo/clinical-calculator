from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def delta_delta_gradient(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "delta_gap_mEq_l") - number(inputs, "delta_bicarbonate_mEq_l")
    return result(metadata, value, "mEq/L", "delta-delta gradient for anion gap metabolic acidosis")


def bicarbonate_delta(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 25 - number(inputs, "bicarbonate_mEq_l")
    return result(metadata, value, "mEq/L", "delta bicarbonate from a reference bicarbonate of 25 mEq/L")


def serum_anion_gap_for_delta_delta(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "sodium_mEq_l") - (
        number(inputs, "chloride_mEq_l") + number(inputs, "bicarbonate_mEq_l")
    )
    return result(metadata, value, "mEq/L", "serum anion gap for delta-delta calculation")


def anion_gap_delta(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "anion_gap_mEq_l") - number(inputs, "baseline_anion_gap_mEq_l")
    return result(metadata, value, "mEq/L", "delta anion gap from baseline")


def male_urea_distribution_volume_watson(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (
        2.447
        - 0.09516 * _positive(inputs, "age_years")
        + 0.1074 * _positive(inputs, "height_cm")
        + 0.3362 * _positive(inputs, "weight_kg")
    )
    return result(metadata, value, "L", "male urea distribution volume estimate")


def female_urea_distribution_volume_watson(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0.1069 * _positive(inputs, "height_cm") + 0.2466 * _positive(inputs, "weight_kg") - 2.097
    return result(metadata, value, "L", "female urea distribution volume estimate")
