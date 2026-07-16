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


def _lms_z_score(value: float, l_value: float, m_value: float, s_value: float) -> float:
    if l_value == 0:
        return math.log(value / m_value) / s_value
    return ((value / m_value) ** l_value - 1) / (l_value * s_value)


def _normal_percentile(z_score: float) -> float:
    return 100 * (0.5 * (1 + math.erf(z_score / math.sqrt(2))))


def percentile_from_z_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    z_score = number(inputs, "z_score")
    percentile = _normal_percentile(z_score)
    return result(
        metadata,
        percentile,
        "percentile",
        "Percentile converted from the supplied z-score using the standard normal distribution.",
    )


def _growth_lms_z(
    metadata: CalculatorMetadata,
    inputs: dict[str, Any],
    measurement_key: str,
    label: str,
) -> CalculationResult:
    value = _positive(inputs, measurement_key)
    l_value = number(inputs, "l")
    m_value = _positive(inputs, "m")
    s_value = _positive(inputs, "s")
    z_score = _lms_z_score(value, l_value, m_value, s_value)
    return result(metadata, z_score, "z-score", f"{label} z-score from supplied LMS parameters")


def _growth_lms_percentile(
    metadata: CalculatorMetadata,
    inputs: dict[str, Any],
    measurement_key: str,
    label: str,
) -> CalculationResult:
    value = _positive(inputs, measurement_key)
    l_value = number(inputs, "l")
    m_value = _positive(inputs, "m")
    s_value = _positive(inputs, "s")
    z_score = _lms_z_score(value, l_value, m_value, s_value)
    percentile = _normal_percentile(z_score)
    return result(metadata, percentile, "percentile", f"{label} percentile from supplied LMS parameters")


def bedside_schwartz_egfr(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0.413 * _positive(inputs, "height_cm") / _positive(inputs, "serum_creatinine_mg_dl")
    return result(metadata, value, "mL/min/1.73m2", "bedside Schwartz pediatric eGFR")


def neonatal_respiratory_severity_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    fio2 = number(inputs, "fio2")
    if not 0 < fio2 <= 1:
        raise ValueError("fio2 must be a fraction from 0 to 1")
    value = _positive(inputs, "mean_airway_pressure_cm_h2o") * fio2
    return result(metadata, value, "cm H2O", "respiratory support intensity index")


def corrected_csf_wbc_traumatic_tap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "csf_wbc_per_uL") - (
        _positive(inputs, "blood_wbc_10e3_per_uL")
        * number(inputs, "csf_rbc_per_uL")
        / (_positive(inputs, "blood_rbc_10e6_per_uL") * 1_000_000)
    )
    return result(metadata, max(value, 0), "cells/uL", "CSF WBC corrected for traumatic tap blood contamination")


def equivalent_dose_2gy_fractions(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    total_dose = _positive(inputs, "total_dose_gy")
    dose_per_fraction = _positive(inputs, "dose_per_fraction_gy")
    alpha_beta = _positive(inputs, "alpha_beta_gy")
    value = total_dose * ((dose_per_fraction + alpha_beta) / (2 + alpha_beta))
    return result(metadata, value, "Gy", "equivalent dose in 2 Gy fractions using the linear-quadratic model")


def biologically_effective_dose(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    total_dose = _positive(inputs, "total_dose_gy")
    dose_per_fraction = _positive(inputs, "dose_per_fraction_gy")
    alpha_beta = _positive(inputs, "alpha_beta_gy")
    value = total_dose * (1 + dose_per_fraction / alpha_beta)
    return result(metadata, value, "Gy", "biologically effective dose using the linear-quadratic model")


def who_infant_length_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "length_cm", "WHO infant length-for-age")


def who_infant_length_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "length_cm", "WHO infant length-for-age")


def who_infant_weight_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "weight_kg", "WHO infant weight-for-age")


def who_infant_weight_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "weight_kg", "WHO infant weight-for-age")


def who_weight_for_length_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "weight_kg", "WHO weight-for-length")


def who_weight_for_length_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "weight_kg", "WHO weight-for-length")


def who_head_circumference_for_age_z_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "head_circumference_cm", "WHO head circumference-for-age")


def who_head_circumference_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "head_circumference_cm", "WHO head circumference-for-age")


def cdc_girls_bmi_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "bmi", "CDC girls BMI-for-age")


def cdc_girls_bmi_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "bmi", "CDC girls BMI-for-age")


def cdc_boys_bmi_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "bmi", "CDC boys BMI-for-age")


def cdc_boys_bmi_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "bmi", "CDC boys BMI-for-age")


def cdc_girls_weight_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "weight_kg", "CDC girls weight-for-age")


def cdc_girls_weight_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "weight_kg", "CDC girls weight-for-age")


def cdc_boys_weight_for_age_z_from_lms(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _growth_lms_z(metadata, inputs, "weight_kg", "CDC boys weight-for-age")


def cdc_boys_weight_for_age_percentile_from_lms(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    return _growth_lms_percentile(metadata, inputs, "weight_kg", "CDC boys weight-for-age")
