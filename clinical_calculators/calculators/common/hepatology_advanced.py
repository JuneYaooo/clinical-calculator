from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _boolean_flag(inputs: dict[str, Any], key: str, default: bool | None = None) -> bool:
    if key not in inputs:
        if default is not None:
            return default
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0:
        return False
    if value == 1:
        return True
    raise ValueError(f"{key} must be a boolean or 0/1")


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _integer_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    integer = int(value)
    if integer < minimum or integer > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer


def _log_floor(value: float) -> float:
    return max(value, 1.0)


def meld_na_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bilirubin = _log_floor(number(inputs, "bilirubin_mg_dl"))
    inr = _log_floor(number(inputs, "inr"))
    creatinine = _log_floor(number(inputs, "creatinine_mg_dl"))
    if _boolean_flag(inputs, "dialysis_twice_in_last_week", default=False):
        creatinine = 4.0
    creatinine = min(creatinine, 4.0)

    meld = 3.78 * math.log(bilirubin) + 11.2 * math.log(inr) + 9.57 * math.log(creatinine) + 6.43

    sodium = min(max(number(inputs, "sodium_mEq_l"), 125), 137)
    sodium_delta = 137 - sodium
    meld_na = meld + 1.32 * sodium_delta - 0.033 * meld * sodium_delta

    return result(
        metadata,
        meld_na,
        "points",
        "adult MELD-Na estimate for end-stage liver disease; not for patients younger than 12 years",
    )


def meld_3_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bilirubin = _log_floor(number(inputs, "bilirubin_mg_dl"))
    inr = _log_floor(number(inputs, "inr"))
    creatinine = _log_floor(number(inputs, "creatinine_mg_dl"))
    if _boolean_flag(inputs, "dialysis_twice_in_last_week", default=False):
        creatinine = 3.0
    creatinine = min(creatinine, 3.0)

    sodium = min(max(number(inputs, "sodium_mEq_l"), 125), 137)
    albumin = min(max(number(inputs, "albumin_g_dl"), 1.5), 3.5)
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")

    sodium_delta = 137 - sodium
    albumin_delta = 3.5 - albumin
    female = 1 if sex == "female" else 0
    value = (
        1.33 * female
        + 4.56 * math.log(bilirubin)
        + 0.82 * sodium_delta
        - 0.24 * sodium_delta * math.log(bilirubin)
        + 9.09 * math.log(inr)
        + 11.14 * math.log(creatinine)
        + 1.85 * albumin_delta
        - 1.83 * albumin_delta * math.log(creatinine)
        + 6
    )
    return result(metadata, value, "points", "MELD 3.0 score; higher score indicates higher short-term mortality risk")


def peld_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = number(inputs, "age_years")
    albumin = _log_floor(number(inputs, "albumin_g_dl"))
    bilirubin = _log_floor(number(inputs, "bilirubin_mg_dl"))
    inr = _log_floor(number(inputs, "inr"))
    growth_failure = _boolean_flag(inputs, "growth_failure")

    value = (
        0.480 * math.log(bilirubin)
        + 1.857 * math.log(inr)
        - 0.687 * math.log(albumin)
        + 0.436 * int(age < 1)
        + 0.667 * int(growth_failure)
    ) * 10

    return result(metadata, value, "points", "pediatric liver disease score")


def ranson_acute_pancreatitis_criteria(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(
        [
            number(inputs, "age_years") > 55,
            number(inputs, "wbc_10e9_l") > 16,
            number(inputs, "glucose_mg_dl") > 200,
            number(inputs, "ast_u_l") > 250,
            number(inputs, "ldh_u_l") > 350,
            number(inputs, "hematocrit_fall_percent") > 10,
            number(inputs, "bun_increase_mg_dl") > 5,
            number(inputs, "calcium_mg_dl") < 8,
            number(inputs, "pao2_mm_hg") < 60,
            number(inputs, "base_deficit_mEq_l") > 4,
            number(inputs, "fluid_sequestration_l") > 6,
        ]
    )

    return result(
        metadata,
        score,
        "points",
        "Ranson acute pancreatitis criteria; higher score indicates worse prognosis",
    )


def clif_c_aclf_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    clif_c_of = _integer_range(inputs, "clif_c_of_score", 6, 18)
    age = _non_negative_number(inputs, "age_years")
    wbc = _positive_number(inputs, "wbc_10e9_l")

    score = 10 * (0.33 * clif_c_of + 0.04 * age + 0.63 * math.log(wbc) - 2)
    return result(
        metadata,
        score,
        "points",
        "CLIF-C ACLF score for short-term mortality risk in acute-on-chronic liver failure",
    )


def clif_c_ad_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _non_negative_number(inputs, "age_years")
    creatinine = _positive_number(inputs, "creatinine_mg_dl")
    inr = _positive_number(inputs, "inr")
    wbc = _positive_number(inputs, "wbc_10e9_l")
    sodium = _positive_number(inputs, "sodium_mEq_l")

    score = 10 * (
        0.03 * age
        + 0.66 * math.log(creatinine)
        + 1.71 * math.log(inr)
        + 0.88 * math.log(wbc)
        - 0.05 * sodium
        + 8
    )
    return result(
        metadata,
        score,
        "points",
        "CLIF-C acute decompensation score for short-term mortality risk in cirrhosis without ACLF",
    )


def baveno_vi_varices_risk_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    liver_stiffness = _positive_number(inputs, "liver_stiffness_kpa")
    platelets = _positive_number(inputs, "platelets_10e9_l")
    can_avoid = liver_stiffness < 20 and platelets > 150
    value = {
        "can_avoid_screening_endoscopy": can_avoid,
        "liver_stiffness_below_20_kpa": liver_stiffness < 20,
        "platelets_above_150_10e9_l": platelets > 150,
    }
    interpretation = (
        "Baveno VI low risk for varices needing treatment; screening endoscopy can be avoided."
        if can_avoid
        else "Baveno VI low-risk criteria not met; screening endoscopy should not be avoided by this rule alone."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=interpretation,
    )
