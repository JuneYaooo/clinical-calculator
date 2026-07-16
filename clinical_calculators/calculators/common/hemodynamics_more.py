from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def arterial_oxygen_content(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    hemoglobin = _positive(inputs, "hemoglobin_g_dl")
    saturation = number(inputs, "oxygen_saturation_percent")
    pao2 = number(inputs, "pao2_mm_hg")
    value = (hemoglobin * 13.4 * saturation / 100) + (pao2 * 0.031)
    return result(metadata, value, "mL O2/L blood", "arterial oxygen content")


def venous_oxygen_content(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    hemoglobin = _positive(inputs, "hemoglobin_g_dl")
    saturation = number(inputs, "venous_oxygen_saturation_percent")
    pvo2 = number(inputs, "pvo2_mm_hg")
    value = (hemoglobin * 13.4 * saturation / 100) + (pvo2 * 0.031)
    return result(metadata, value, "mL O2/L blood", "venous oxygen content")


def fick_cardiac_output_from_contents(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    av_difference = number(inputs, "arterial_oxygen_content_ml_dl") - number(inputs, "venous_oxygen_content_ml_dl")
    if av_difference <= 0:
        raise ValueError("arterial_oxygen_content_ml_dl must exceed venous_oxygen_content_ml_dl")
    value = number(inputs, "oxygen_consumption_ml_min") / av_difference
    return result(metadata, value, "dL/min", "Fick cardiac output from oxygen consumption and content difference")


def cardiac_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "cardiac_output_l_min") / _positive(inputs, "bsa_m2")
    return result(metadata, value, "L/min/m2", "cardiac output indexed to body surface area")


def stroke_volume(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 1000 * number(inputs, "cardiac_output_l_min") / _positive(inputs, "heart_rate_bpm")
    return result(metadata, value, "mL/beat", "stroke volume from cardiac output and heart rate")


def stroke_volume_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "stroke_volume_ml") / _positive(inputs, "bsa_m2")
    return result(metadata, value, "mL/beat/m2", "stroke volume indexed to body surface area")


def body_surface_area_du_bois_for_hemodynamics(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = 0.007184 * (_positive(inputs, "height_cm") ** 0.725) * (_positive(inputs, "weight_kg") ** 0.425)
    return result(metadata, value, "m2", "Du Bois body surface area")
