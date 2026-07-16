from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = _number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def _boolean_flag(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _fio2_fraction(inputs: dict[str, Any], key: str) -> float:
    value = _positive_number(inputs, key)
    if value <= 1:
        return value
    if value <= 100:
        return value / 100
    raise ValueError(f"{key} must be a fraction from 0 to 1 or a percent from 1 to 100")


def _count_true(inputs: dict[str, Any], keys: tuple[str, ...]) -> int:
    return sum(1 for key in keys if _boolean_flag(inputs, key))


def pao2_fio2_ratio_mods(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ratio = _positive_number(inputs, "pao2_mm_hg") / _fio2_fraction(inputs, "fio2")

    if ratio <= 100:
        interpretation = "severe ARDS oxygenation threshold"
    elif ratio <= 200:
        interpretation = "moderate ARDS oxygenation threshold"
    elif ratio <= 300:
        interpretation = "mild ARDS oxygenation threshold"
    else:
        interpretation = "no ARDS oxygenation threshold"

    return result(metadata, ratio, "ratio", interpretation)


def mean_arterial_pressure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    systolic = _number(inputs, "systolic_pressure_mm_hg")
    diastolic = _number(inputs, "diastolic_pressure_mm_hg")
    map_value = (systolic + 2 * diastolic) / 3

    return result(metadata, map_value, "mm Hg", "mean vascular pressure")


def shock_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    index = _positive_number(inputs, "heart_rate") / _positive_number(inputs, "systolic_bp")
    interpretation = "elevated shock index" if index >= 0.9 else "shock index not elevated"

    return result(metadata, index, "", interpretation)


def sirs_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    temperature = _number(inputs, "temperature_c")
    heart_rate = _number(inputs, "heart_rate")
    respiratory_rate = _number(inputs, "respiratory_rate")
    paco2 = _number(inputs, "paco2_mm_hg")
    wbc = _number(inputs, "wbc_10e9_l")
    bands = _number(inputs, "bands_percent")

    score = 0
    if temperature > 38 or temperature < 36:
        score += 1
    if heart_rate > 90:
        score += 1
    if respiratory_rate > 20 or paco2 < 32:
        score += 1
    if wbc > 12 or wbc < 4 or bands > 10:
        score += 1

    interpretation = "SIRS met" if score >= 2 else "SIRS not met"
    return result(metadata, score, "points", interpretation)


def nexus_c_spine_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    criteria = (
        "midline_cervical_tenderness",
        "focal_neurologic_deficit",
        "altered_level_of_alertness",
        "intoxication",
        "distracting_injury",
    )
    score = _count_true(inputs, criteria)
    interpretation = (
        "positive NEXUS c-spine rule; imaging indicated"
        if score > 0
        else "low risk by NEXUS c-spine rule"
    )

    return result(metadata, score, "criteria", interpretation)


def canadian_ct_head_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _count_true(
        inputs,
        (
            "gcs_less_than_15_at_2_hours",
            "suspected_open_or_depressed_skull_fracture",
            "signs_basal_skull_fracture",
            "vomiting_two_or_more",
            "dangerous_mechanism",
        ),
    )

    if _number(inputs, "age_years") >= 65:
        score += 1
    if _number(inputs, "amnesia_before_impact_minutes") >= 30:
        score += 1

    interpretation = (
        "Canadian CT head rule positive; CT recommended"
        if score > 0
        else "Canadian CT head rule negative; CT not recommended by this rule"
    )

    return result(metadata, score, "criteria", interpretation)


def pediatric_endotracheal_tube_size(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _number(inputs, "age_years")
    if age_years < 1 or age_years > 8:
        raise ValueError("age_years must be between 1 and 8")

    cuffed = _boolean_flag(inputs, "cuffed")
    tube_size = (age_years / 4) + (3.5 if cuffed else 4)
    interpretation = (
        "cuffed pediatric endotracheal tube size"
        if cuffed
        else "uncuffed pediatric endotracheal tube size"
    )

    return result(metadata, tube_size, "mm internal diameter", interpretation)
