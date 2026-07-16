from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _boolean_flag(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0:
        return False
    if value == 1:
        return True
    raise ValueError(f"{key} must be a boolean or 0/1")


def _clinical_feature(inputs: dict[str, Any]) -> str:
    key = "clinical_feature"
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    allowed = {"unilateral_weakness", "speech_without_weakness", "other"}
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(allowed))}")
    return str(value)


def _integer_score(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
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


def _nonnegative_integer(inputs: dict[str, Any], key: str) -> int:
    if key not in inputs:
        raise KeyError(key)
    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be a nonnegative integer")
    numeric = number(inputs, key)
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"{key} must be a nonnegative integer")
    return int(numeric)


def abcd2_tia_risk(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "age_years") >= 60:
        score += 1
    if number(inputs, "systolic_bp") >= 140 or number(inputs, "diastolic_bp") >= 90:
        score += 1

    feature = _clinical_feature(inputs)
    if feature == "unilateral_weakness":
        score += 2
    elif feature == "speech_without_weakness":
        score += 1

    duration = number(inputs, "duration_minutes")
    if duration >= 60:
        score += 2
    elif duration >= 10:
        score += 1

    if _boolean_flag(inputs, "diabetes"):
        score += 1

    if score <= 3:
        interpretation = "low risk by ABCD2 TIA score"
    elif score <= 5:
        interpretation = "moderate risk by ABCD2 TIA score"
    else:
        interpretation = "high risk by ABCD2 TIA score"

    return result(metadata, score, "points", interpretation)


def ich_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    gcs = _integer_score(inputs, "gcs", 3, 15)

    score = 0
    if gcs <= 4:
        score += 2
    elif gcs <= 12:
        score += 1

    if number(inputs, "age_years") >= 80:
        score += 1
    if number(inputs, "ich_volume_ml") >= 30:
        score += 1
    if _boolean_flag(inputs, "infratentorial_origin"):
        score += 1
    if _boolean_flag(inputs, "intraventricular_hemorrhage"):
        score += 1

    interpretation = "higher ICH score indicates higher 30-day mortality risk"
    return result(metadata, score, "points", interpretation)


def sudep_7_inventory_v2(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """SUDEP-7 Risk Inventory version 2.0 (Novak et al., 2015)."""
    tonic_clonic = _nonnegative_integer(inputs, "tonic_clonic_seizures_last_year")
    all_seizures = _nonnegative_integer(inputs, "seizures_any_type_last_year")
    if all_seizures < tonic_clonic:
        raise ValueError(
            "seizures_any_type_last_year cannot be less than tonic_clonic_seizures_last_year"
        )
    more_than_50_monthly = _boolean_flag(inputs, "more_than_50_seizures_per_month")
    duration = number(inputs, "duration_epilepsy_years")
    if duration < 0:
        raise ValueError("duration_epilepsy_years must be nonnegative")
    medications = _nonnegative_integer(inputs, "concurrent_antiseizure_medications")
    developmental_disability = _boolean_flag(
        inputs, "developmental_disability_or_iq_below_70"
    )

    score = 2 if tonic_clonic > 3 else 1 if tonic_clonic >= 1 else 0
    score += 2 if more_than_50_monthly else 1 if all_seizures >= 1 else 0
    score += 3 if duration > 30 else 0
    score += 1 if medications >= 3 else 0
    score += 2 if developmental_disability else 0

    return result(
        metadata,
        score,
        "points",
        "SUDEP-7 v2.0 risk-factor inventory score (0-10); this is not an individualized "
        "probability and must not replace seizure-control review or SUDEP counseling.",
    )


def perc_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive_criteria = 0
    if number(inputs, "age_years") >= 50:
        positive_criteria += 1
    if number(inputs, "heart_rate") >= 100:
        positive_criteria += 1
    if number(inputs, "oxygen_saturation_percent") < 95:
        positive_criteria += 1

    risk_keys = (
        "unilateral_leg_swelling",
        "hemoptysis",
        "recent_surgery_or_trauma",
        "prior_dvt_pe",
        "hormone_use",
    )
    positive_criteria += sum(1 for key in risk_keys if _boolean_flag(inputs, key))

    if positive_criteria == 0:
        interpretation = "PERC negative; no positive PERC criteria"
    else:
        interpretation = "PERC positive; at least one criterion is present"

    return result(metadata, positive_criteria, "points", interpretation)


def san_francisco_syncope_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive_criteria = 0
    if _boolean_flag(inputs, "history_chf"):
        positive_criteria += 1
    if number(inputs, "hematocrit_percent") < 30:
        positive_criteria += 1
    if _boolean_flag(inputs, "abnormal_ecg"):
        positive_criteria += 1
    if _boolean_flag(inputs, "shortness_of_breath"):
        positive_criteria += 1
    if number(inputs, "systolic_bp") < 90:
        positive_criteria += 1

    if positive_criteria >= 1:
        interpretation = "high risk by San Francisco Syncope Rule"
    else:
        interpretation = "low risk by San Francisco Syncope Rule"

    return result(metadata, positive_criteria, "points", interpretation)
