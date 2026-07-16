from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


EGFR_UNIT = "mL/min/1.73m^2"
MDRD_INTERPRETATION = (
    "estimated GFR by MDRD equation; race coefficient is retained only for legacy MDRD when supplied"
)


def _adult_age(inputs: dict[str, Any]) -> float:
    age = number(inputs, "age_years")
    if age < 18 or age > 120:
        raise ValueError("age_years must be between 18 and 120 for this adult equation")
    return age


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _sex(inputs: dict[str, Any]) -> str:
    if "sex" not in inputs:
        raise KeyError("sex")

    sex = str(inputs["sex"]).strip().lower()
    if sex in {"male", "female"}:
        return sex
    raise ValueError("sex must be 'male' or 'female'")


def _black(inputs: dict[str, Any]) -> bool:
    value = inputs.get("black", False)
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ValueError("black must be bool or 0/1")


def _mdrd_value(age_years: float, serum_creatinine_mg_dl: float, sex: str, black: bool) -> float:
    value = 175 * serum_creatinine_mg_dl**-1.154 * age_years**-0.203
    if sex == "female":
        value *= 0.742
    if black:
        value *= 1.212
    return value


def mdrd_egfr(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _adult_age(inputs)
    serum_creatinine_mg_dl = _positive_number(inputs, "serum_creatinine_mg_dl")
    sex = _sex(inputs)
    black = _black(inputs)

    value = _mdrd_value(age_years, serum_creatinine_mg_dl, sex, black)
    return result(metadata, value, EGFR_UNIT, MDRD_INTERPRETATION)


def mdrd_egfr_si(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _adult_age(inputs)
    serum_creatinine_umol_l = _positive_number(inputs, "serum_creatinine_umol_l")
    sex = _sex(inputs)
    black = _black(inputs)

    serum_creatinine_mg_dl = serum_creatinine_umol_l / 88.4
    value = _mdrd_value(age_years, serum_creatinine_mg_dl, sex, black)
    return result(metadata, value, EGFR_UNIT, MDRD_INTERPRETATION)


def ckd_epi_2021_egfr_creatinine(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _adult_age(inputs)
    serum_creatinine_mg_dl = _positive_number(inputs, "serum_creatinine_mg_dl")
    sex = _sex(inputs)

    if sex == "female":
        k = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        k = 0.9
        alpha = -0.302
        sex_factor = 1.0

    scr_ratio = serum_creatinine_mg_dl / k
    value = (
        142
        * min(scr_ratio, 1) ** alpha
        * max(scr_ratio, 1) ** -1.200
        * 0.9938**age_years
        * sex_factor
    )
    return result(metadata, value, EGFR_UNIT, "estimated GFR by 2021 CKD-EPI creatinine equation")


def urine_protein_creatinine_ratio(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    urine_protein_mg_dl = number(inputs, "urine_protein_mg_dl")
    urine_creatinine_mg_dl = _positive_number(inputs, "urine_creatinine_mg_dl")

    value = urine_protein_mg_dl / urine_creatinine_mg_dl * 1000
    return result(metadata, value, "mg/g", "urine protein-to-creatinine ratio")
