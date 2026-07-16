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


def predicted_peak_expiratory_flow(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs["sex"]).strip().lower()
    age = _positive(inputs, "age_years")
    height = _positive(inputs, "height_cm")

    if sex == "female":
        pef = math.exp((0.376 * math.log(age)) - (0.012 * age) - (58.8 / height) + 5.63)
    elif sex == "male":
        pef = math.exp((0.544 * math.log(age)) - (0.0151 * age) - (74.7 / height) + 5.48)
    else:
        raise ValueError("sex must be 'male' or 'female'")

    return result(metadata, pef, "L/min", "predicted peak expiratory flow")


def rapid_shallow_breathing_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    respiratory_rate = _positive(inputs, "respiratory_rate_bpm")
    if "tidal_volume_l" in inputs:
        tidal_volume_l = _positive(inputs, "tidal_volume_l")
    elif "tidal_volume_ml" in inputs:
        tidal_volume_l = _positive(inputs, "tidal_volume_ml") / 1000
    else:
        raise KeyError("tidal_volume_l")

    value = respiratory_rate / tidal_volume_l
    interpretation = (
        "RSBI is more favorable for spontaneous breathing trial success."
        if value <= 105
        else "RSBI is less favorable for spontaneous breathing trial success."
    )
    return result(metadata, value, "breaths/min/L", interpretation)


def female_pediatric_predicted_fev1(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _positive(inputs, "age_years")
    height = _positive(inputs, "height_m")
    value = math.exp(((1.5016 + (0.0119 * age)) * height) - 1.5974)
    return result(metadata, value, "L", "female pediatric predicted FEV1")


def female_pediatric_predicted_fvc(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _positive(inputs, "age_years")
    height = _positive(inputs, "height_m")
    value = math.exp(((1.48 + (0.0127 * age)) * height) - 1.4057)
    return result(metadata, value, "L", "female pediatric predicted FVC")


def male_pediatric_predicted_fev1(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _positive(inputs, "age_years")
    height = _positive(inputs, "height_m")
    value = math.exp(((1.2669 + (0.0174 * age)) * height) - 1.2933)
    return result(metadata, value, "L", "male pediatric predicted FEV1")


def male_pediatric_predicted_fvc(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _positive(inputs, "age_years")
    height = _positive(inputs, "height_m")
    value = math.exp(((1.3731 + (0.0164 * age)) * height) - 1.2782)
    return result(metadata, value, "L", "male pediatric predicted FVC")


def male_adjusted_predicted_fev1(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    height = _positive(inputs, "height_cm")
    age = _positive(inputs, "age_years")
    race_factor = _positive(inputs, "race_factor")
    value = race_factor * 1.08 * ((0.043 * height) - (0.029 * age) - 2.49)
    return result(metadata, value, "L", "male adjusted predicted FEV1")


def male_adjusted_predicted_fvc(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    height = _positive(inputs, "height_cm")
    age = _positive(inputs, "age_years")
    race_factor = _positive(inputs, "race_factor")
    value = race_factor * 1.1 * ((0.0576 * height) - (0.0269 * age) - 4.34)
    return result(metadata, value, "L", "male adjusted predicted FVC")


def estimated_pneumothorax_size(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    lung_diameter = _positive(inputs, "lung_diameter_cm")
    hemithorax_diameter = _positive(inputs, "hemithorax_diameter_cm")
    if lung_diameter > hemithorax_diameter:
        raise ValueError("lung_diameter_cm must be less than or equal to hemithorax_diameter_cm")

    pneumothorax_size = 100 * (1 - (lung_diameter**3 / hemithorax_diameter**3))
    return result(metadata, pneumothorax_size, "%", "estimated pneumothorax size by cubed diameter ratio")


def residual_volume_to_total_lung_capacity_ratio(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    residual_volume = _nonnegative(inputs, "residual_volume_l")
    total_lung_capacity = _positive(inputs, "total_lung_capacity_l")

    ratio = 100 * residual_volume / total_lung_capacity
    return result(metadata, ratio, "%", "residual volume to total lung capacity ratio")


def inspiratory_capacity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    inspiratory_reserve_volume = _nonnegative(inputs, "inspiratory_reserve_volume_l")
    tidal_volume = _nonnegative(inputs, "tidal_volume_l")

    capacity = inspiratory_reserve_volume + tidal_volume
    return result(metadata, capacity, "L", "inspiratory capacity")


def vital_capacity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    inspiratory_reserve_volume = _nonnegative(inputs, "inspiratory_reserve_volume_l")
    tidal_volume = _nonnegative(inputs, "tidal_volume_l")
    expiratory_reserve_volume = _nonnegative(inputs, "expiratory_reserve_volume_l")

    capacity = inspiratory_reserve_volume + tidal_volume + expiratory_reserve_volume
    return result(metadata, capacity, "L", "vital capacity")


def total_lung_capacity_from_volumes(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    inspiratory_reserve_volume = _nonnegative(inputs, "inspiratory_reserve_volume_l")
    tidal_volume = _nonnegative(inputs, "tidal_volume_l")
    expiratory_reserve_volume = _nonnegative(inputs, "expiratory_reserve_volume_l")
    residual_volume = _nonnegative(inputs, "residual_volume_l")

    capacity = inspiratory_reserve_volume + tidal_volume + expiratory_reserve_volume + residual_volume
    return result(metadata, capacity, "L", "total lung capacity from component volumes")


def functional_residual_capacity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    expiratory_reserve_volume = _nonnegative(inputs, "expiratory_reserve_volume_l")
    residual_volume = _nonnegative(inputs, "residual_volume_l")

    capacity = expiratory_reserve_volume + residual_volume
    return result(metadata, capacity, "L", "functional residual capacity")


def closing_capacity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    closing_volume = _nonnegative(inputs, "closing_volume_l")
    residual_volume = _nonnegative(inputs, "residual_volume_l")

    capacity = closing_volume + residual_volume
    return result(metadata, capacity, "L", "closing capacity")


def closing_volume_to_vital_capacity_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    closing_volume = _nonnegative(inputs, "closing_volume_l")
    vital_capacity_l = _positive(inputs, "vital_capacity_l")

    ratio = 100 * closing_volume / vital_capacity_l
    return result(metadata, ratio, "%", "closing volume to vital capacity ratio")


def closing_capacity_to_total_lung_capacity_ratio(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    closing_capacity_l = _nonnegative(inputs, "closing_capacity_l")
    total_lung_capacity_l = _positive(inputs, "total_lung_capacity_l")

    ratio = 100 * closing_capacity_l / total_lung_capacity_l
    return result(metadata, ratio, "%", "closing capacity to total lung capacity ratio")


__all__ = [
    "closing_capacity",
    "closing_capacity_to_total_lung_capacity_ratio",
    "closing_volume_to_vital_capacity_ratio",
    "estimated_pneumothorax_size",
    "female_pediatric_predicted_fev1",
    "female_pediatric_predicted_fvc",
    "functional_residual_capacity",
    "inspiratory_capacity",
    "male_adjusted_predicted_fev1",
    "male_adjusted_predicted_fvc",
    "male_pediatric_predicted_fev1",
    "male_pediatric_predicted_fvc",
    "predicted_peak_expiratory_flow",
    "rapid_shallow_breathing_index",
    "residual_volume_to_total_lung_capacity_ratio",
    "total_lung_capacity_from_volumes",
    "vital_capacity",
]
