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


def left_ventricular_ejection_fraction(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    edv = _positive(inputs, "end_diastolic_volume_ml")
    esv = number(inputs, "end_systolic_volume_ml")
    if esv < 0 or esv > edv:
        raise ValueError("end_systolic_volume_ml must be between 0 and end_diastolic_volume_ml")

    ejection_fraction = (edv - esv) / edv * 100
    if ejection_fraction >= 50:
        interpretation = "preserved left ventricular ejection fraction range"
    elif ejection_fraction >= 40:
        interpretation = "mildly reduced left ventricular ejection fraction range"
    else:
        interpretation = "reduced left ventricular ejection fraction range"
    return result(metadata, ejection_fraction, "%", interpretation)


def henderson_hasselbalch_ph(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bicarbonate = _positive(inputs, "bicarbonate_mmol_l")
    paco2 = _positive(inputs, "paco2_mm_hg")
    ph = 6.1 + math.log10(bicarbonate / (0.03 * paco2))

    if ph < 7.35:
        interpretation = "acidic pH estimate by Henderson-Hasselbalch equation"
    elif ph <= 7.45:
        interpretation = "usual arterial pH range by Henderson-Hasselbalch equation"
    else:
        interpretation = "alkalemic pH estimate by Henderson-Hasselbalch equation"
    return result(metadata, ph, "pH", interpretation)


def albumin_corrected_anion_gap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    anion_gap = number(inputs, "anion_gap_mEq_l")
    observed_albumin = number(inputs, "albumin_g_dl") if "albumin_g_dl" in inputs else number(inputs, "observed_albumin_g_dl")
    normal_albumin = number(inputs, "normal_albumin_g_dl") if "normal_albumin_g_dl" in inputs else 4.0
    corrected_gap = anion_gap + 2.5 * (normal_albumin - observed_albumin)

    if corrected_gap > 12:
        interpretation = "elevated albumin-corrected anion gap"
    else:
        interpretation = "not elevated by a common albumin-corrected anion gap threshold"
    return result(metadata, corrected_gap, "mEq/L", interpretation)


def urine_anion_gap(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_gap = (
        number(inputs, "urine_sodium_mEq_l")
        + number(inputs, "urine_potassium_mEq_l")
        - number(inputs, "urine_chloride_mEq_l")
    )
    if urine_gap < 0:
        interpretation = "negative urine anion gap; suggests higher urinary ammonium excretion"
    else:
        interpretation = "positive urine anion gap; suggests lower urinary ammonium excretion"
    return result(metadata, urine_gap, "mEq/L", interpretation)


def estimated_average_glucose_from_hba1c(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    hba1c = number(inputs, "hba1c_percent")
    estimated_glucose = 28.7 * hba1c - 46.7
    return result(metadata, estimated_glucose, "mg/dL", "estimated average glucose by ADAG equation")


def transferrin_saturation(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    serum_iron = number(inputs, "serum_iron_ug_dl")
    tibc = _positive(inputs, "tibc_ug_dl")
    saturation = serum_iron / tibc * 100

    if saturation < 20:
        interpretation = "low transferrin saturation"
    elif saturation <= 50:
        interpretation = "usual transferrin saturation range"
    else:
        interpretation = "high transferrin saturation"
    return result(metadata, saturation, "%", interpretation)


def pediatric_maintenance_fluid_holliday_segar(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight = _positive(inputs, "weight_kg")
    if weight <= 10:
        daily_fluid = 100 * weight
    elif weight <= 20:
        daily_fluid = 1000 + 50 * (weight - 10)
    else:
        daily_fluid = 1500 + 20 * (weight - 20)
    return result(metadata, daily_fluid, "mL/day", "daily pediatric maintenance fluid by Holliday-Segar 100-50-20 rule")


def pediatric_maintenance_fluid_hourly_rate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    daily_fluid = _positive(inputs, "daily_fluid_ml")
    hourly_rate = daily_fluid / 24
    return result(metadata, hourly_rate, "mL/hour", "hourly pediatric maintenance fluid rate from daily fluid volume")


def basal_energy_expenditure_harris_benedict(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs["sex"]).strip().lower()
    weight = _positive(inputs, "weight_kg")
    height = _positive(inputs, "height_cm")
    age = _positive(inputs, "age_years")

    if sex == "male":
        bee = 66.47 + 13.75 * weight + 5.003 * height - 6.755 * age
    elif sex == "female":
        bee = 655.1 + 9.563 * weight + 1.85 * height - 4.676 * age
    else:
        raise ValueError("sex must be 'male' or 'female'")
    return result(metadata, bee, "kcal/day", "basal energy expenditure by original Harris-Benedict equation")


def penn_state_energy_expenditure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs["sex"]).strip().lower()
    weight = _positive(inputs, "weight_kg")
    height = _positive(inputs, "height_cm")
    age = _positive(inputs, "age_years")
    max_temperature_c = _positive(inputs, "max_temperature_c")
    minute_ventilation = _positive(inputs, "minute_ventilation_l_min")

    if sex == "male":
        mifflin = 10 * weight + 6.25 * height - 5 * age + 5
    elif sex == "female":
        mifflin = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("sex must be 'male' or 'female'")

    value = 0.96 * mifflin + 167 * max_temperature_c + 31 * minute_ventilation - 6212
    return result(metadata, value, "kcal/day", "Penn State critical care energy expenditure estimate.")


def ireton_jones_energy_expenditure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ventilation = str(inputs["ventilation"]).strip().lower()
    age = _positive(inputs, "age_years")
    weight = _positive(inputs, "weight_kg")

    if ventilation == "ventilated":
        sex = str(inputs["sex"]).strip().lower()
        if sex not in {"male", "female"}:
            raise ValueError("sex must be 'male' or 'female'")
        male = 1 if sex == "male" else 0
        trauma = 1 if bool(inputs.get("trauma", False)) else 0
        burn = 1 if bool(inputs.get("burn", False)) else 0
        value = 1925 - 10 * age + 5 * weight + 302 * male + 292 * trauma + 851 * burn
    elif ventilation == "spontaneous":
        obesity = 1 if bool(inputs.get("obesity", False)) else 0
        value = 629 - 11 * age + 25 * weight - 609 * obesity
    else:
        raise ValueError("ventilation must be 'ventilated' or 'spontaneous'")

    return result(metadata, value, "kcal/day", "Ireton-Jones energy expenditure estimate.")
