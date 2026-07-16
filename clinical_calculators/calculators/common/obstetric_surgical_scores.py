from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _integer_in_set(inputs: dict[str, Any], key: str, accepted_values: set[int]) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")

    integer_value = int(numeric_value)
    if integer_value not in accepted_values:
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")
    return integer_value


def puqe_pregnancy_nausea_vomiting_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "nausea_hours_score", 1, 5)
        + _integer_in_range(inputs, "vomiting_score", 1, 5)
        + _integer_in_range(inputs, "retching_score", 1, 5)
    )

    if score >= 13:
        interpretation = "severe nausea and vomiting of pregnancy by PUQE score"
    elif score >= 7:
        interpretation = "moderate nausea and vomiting of pregnancy by PUQE score"
    else:
        interpretation = "mild nausea and vomiting of pregnancy by PUQE score"

    return result(metadata, score, "points", interpretation)


def biophysical_profile_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_set(inputs, "fetal_breathing", {0, 2})
        + _integer_in_set(inputs, "gross_body_movement", {0, 2})
        + _integer_in_set(inputs, "fetal_tone", {0, 2})
        + _integer_in_set(inputs, "amniotic_fluid", {0, 2})
        + _integer_in_set(inputs, "nonstress_test", {0, 2})
    )

    if score >= 8:
        interpretation = "reassuring fetal biophysical profile"
    elif score == 6:
        interpretation = "equivocal fetal biophysical profile"
    else:
        interpretation = "abnormal fetal biophysical profile"

    return result(metadata, score, "points", interpretation)


def obstetric_shock_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    heart_rate = number(inputs, "heart_rate")
    systolic_bp = number(inputs, "systolic_bp")
    if systolic_bp <= 0:
        raise ValueError("systolic_bp must be greater than 0")

    shock_index = heart_rate / systolic_bp
    if shock_index >= 1.4:
        interpretation = "severe concern for obstetric hemorrhage or shock"
    elif shock_index >= 1:
        interpretation = "concerning obstetric shock index"
    else:
        interpretation = "obstetric shock index below concerning threshold"

    return result(metadata, shock_index, "index", interpretation)


def surgical_apgar_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    estimated_blood_loss_ml = number(inputs, "estimated_blood_loss_ml")
    lowest_mean_arterial_pressure = number(inputs, "lowest_mean_arterial_pressure")
    lowest_heart_rate = number(inputs, "lowest_heart_rate")

    if estimated_blood_loss_ml < 0:
        raise ValueError("estimated_blood_loss_ml must be non-negative")

    if estimated_blood_loss_ml > 1000:
        blood_loss_points = 0
    elif estimated_blood_loss_ml >= 601:
        blood_loss_points = 1
    elif estimated_blood_loss_ml >= 101:
        blood_loss_points = 2
    else:
        blood_loss_points = 3

    if lowest_mean_arterial_pressure < 40:
        map_points = 0
    elif lowest_mean_arterial_pressure <= 54:
        map_points = 1
    elif lowest_mean_arterial_pressure <= 69:
        map_points = 2
    else:
        map_points = 3

    if lowest_heart_rate > 85:
        heart_rate_points = 0
    elif lowest_heart_rate >= 76:
        heart_rate_points = 1
    elif lowest_heart_rate >= 66:
        heart_rate_points = 2
    elif lowest_heart_rate >= 56:
        heart_rate_points = 3
    else:
        heart_rate_points = 4

    score = blood_loss_points + map_points + heart_rate_points
    return result(metadata, score, "points", "Surgical Apgar score; lower score indicates higher postoperative risk.")


def killip_acute_mi_heart_failure_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    killip_class = _integer_in_range(inputs, "class", 1, 4)
    labels = {
        1: "no clinical signs of heart failure",
        2: "S3 gallop, rales, or elevated jugular venous pressure",
        3: "acute pulmonary edema",
        4: "cardiogenic shock",
    }

    return result(metadata, killip_class, "class", f"Killip class {killip_class}: {labels[killip_class]}.")


def nyha_functional_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    nyha_class = _integer_in_range(inputs, "class", 1, 4)
    labels = {
        1: "no limitation of physical activity",
        2: "slight limitation of physical activity",
        3: "marked limitation of physical activity",
        4: "symptoms at rest",
    }

    return result(metadata, nyha_class, "class", f"NYHA class {nyha_class}: {labels[nyha_class]}.")
