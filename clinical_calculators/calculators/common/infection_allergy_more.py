from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _nonnegative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def _bool_input(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0 or value == 1:
        return bool(value)
    raise ValueError(f"{key} must be a bool or 0/1")


def _text_choice(inputs: dict[str, Any], key: str, choices: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{key} must be one of: {allowed}")
    return value


def lrinec_necrotizing_soft_tissue_infection_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    crp = _nonnegative_number(inputs, "crp_mg_l")
    wbc = _nonnegative_number(inputs, "wbc_10e9_l")
    hemoglobin = _positive_number(inputs, "hemoglobin_g_dl")
    sodium = _positive_number(inputs, "sodium_mEq_l")
    creatinine = _positive_number(inputs, "creatinine_mg_dl")
    glucose = _positive_number(inputs, "glucose_mg_dl")

    score = 0
    if crp >= 150:
        score += 4
    if wbc > 25:
        score += 2
    elif wbc >= 15:
        score += 1
    if hemoglobin < 11:
        score += 2
    elif hemoglobin <= 13.5:
        score += 1
    if sodium < 135:
        score += 2
    if creatinine > 1.6:
        score += 2
    if glucose > 180:
        score += 1

    if score >= 8:
        risk = "high risk"
    elif score >= 6:
        risk = "intermediate risk"
    else:
        risk = "low risk"
    return result(metadata, score, "points", f"LRINEC necrotizing soft tissue infection screen: {risk}.")


def pen_fast_penicillin_allergy_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _bool_input(inputs, "reaction_within_5_years"):
        score += 2
    if _bool_input(inputs, "anaphylaxis_or_angioedema") or _bool_input(inputs, "severe_cutaneous_adverse_reaction"):
        score += 2
    if _bool_input(inputs, "treatment_required"):
        score += 1

    interpretation = (
        "PEN-FAST low risk for positive penicillin allergy test."
        if score < 3
        else "PEN-FAST not low risk for positive penicillin allergy test."
    )
    return result(metadata, score, "points", interpretation)


def tuberculin_skin_test_interpretation(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    induration_mm = _nonnegative_number(inputs, "induration_mm")
    threshold_mm = int(_nonnegative_number(inputs, "risk_threshold_mm"))
    if threshold_mm not in {5, 10, 15}:
        raise ValueError("risk_threshold_mm must be 5, 10, or 15")

    is_positive = induration_mm >= threshold_mm
    interpretation = (
        f"TST positive: induration {induration_mm:g} mm meets the selected {threshold_mm} mm threshold."
        if is_positive
        else f"TST negative: induration {induration_mm:g} mm is below the selected {threshold_mm} mm threshold."
    )

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "induration_mm": round(induration_mm, 4),
            "risk_threshold_mm": threshold_mm,
            "positive": is_positive,
        },
        unit="mm",
        interpretation=interpretation,
    )


def clostridioides_difficile_infection_severity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    wbc = _nonnegative_number(inputs, "wbc_10e9_l")
    creatinine = _nonnegative_number(inputs, "creatinine_mg_dl")
    fulminant = any(
        _bool_input(inputs, key)
        for key in ("hypotension_or_shock", "ileus", "megacolon")
    )

    if fulminant:
        severity = "fulminant"
        interpretation = "C. difficile infection severity: fulminant feature present."
    elif wbc >= 15 or creatinine > 1.5:
        severity = "severe"
        interpretation = "C. difficile infection severity: severe by WBC or serum creatinine criterion."
    else:
        severity = "non-severe"
        interpretation = "C. difficile infection severity: non-severe by WBC and serum creatinine criteria."

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=severity,
        unit="category",
        interpretation=interpretation,
    )


def hypothermia_staging(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    mental_status = _text_choice(inputs, "mental_status", {"alert", "impaired", "unconscious"})
    shivering = _bool_input(inputs, "shivering")
    vital_signs_present = _bool_input(inputs, "vital_signs_present")

    if not vital_signs_present:
        stage = "HT IV"
        temperature_range = "<24 C"
        description = "apparent death/no vital signs"
    elif mental_status == "unconscious":
        stage = "HT III"
        temperature_range = "24-28 C"
        description = "unconscious with vital signs present"
    elif mental_status == "impaired":
        stage = "HT II"
        temperature_range = "28-32 C"
        description = "impaired consciousness"
    else:
        stage = "HT I"
        temperature_range = "32-35 C"
        description = "conscious"

    shivering_text = "shivering present" if shivering else "shivering absent"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "stage": stage,
            "typical_core_temperature_c": temperature_range,
        },
        unit="stage",
        interpretation=f"Swiss hypothermia stage {stage}: {description}; {shivering_text}.",
    )


def thwaites_diagnostic_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _nonnegative_number(inputs, "age_years")
    illness_duration = _nonnegative_number(inputs, "illness_duration_days")
    blood_wbc = _nonnegative_number(inputs, "blood_wbc_10e9_l")
    csf_wbc = _nonnegative_number(inputs, "csf_wbc_cells_per_uL")
    csf_neutrophils = _nonnegative_number(inputs, "csf_neutrophils_percent")
    if csf_neutrophils > 100:
        raise ValueError("csf_neutrophils_percent must be between 0 and 100")

    score = 0
    if age >= 36:
        score += 2
    if blood_wbc >= 15:
        score += 4
    if illness_duration >= 6:
        score -= 5
    if csf_wbc >= 900:
        score += 3
    if csf_neutrophils >= 75:
        score += 4

    interpretation = (
        "Thwaites score favors tuberculous meningitis."
        if score <= 4
        else "Thwaites score favors bacterial meningitis."
    )
    return result(metadata, score, "points", interpretation)


def predict_ie_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    acquisition = _text_choice(inputs, "acquisition", {"community", "healthcare", "nosocomial"})

    day1_score = 0
    if _bool_input(inputs, "implantable_cardioverter_defibrillator"):
        day1_score += 2
    if _bool_input(inputs, "permanent_pacemaker"):
        day1_score += 3
    if acquisition == "community":
        day1_score += 2
    elif acquisition == "healthcare":
        day1_score += 1

    day5_score = day1_score
    if _bool_input(inputs, "positive_blood_culture_after_48h"):
        day5_score += 3
    if _bool_input(inputs, "positive_blood_culture_after_72h"):
        day5_score += 2

    interpretation = (
        "higher PREDICT IE risk by day 5 score"
        if day5_score >= 2
        else "lower PREDICT IE risk by day 5 score"
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"day1_score": day1_score, "day5_score": day5_score},
        unit="points",
        interpretation=interpretation,
    )


def virsta_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    score += 5 if _bool_input(inputs, "cerebral_or_peripheral_emboli") else 0
    score += 5 if _bool_input(inputs, "meningitis") else 0
    score += 4 if _bool_input(inputs, "permanent_intracardiac_device_or_previous_ie") else 0
    score += 3 if _bool_input(inputs, "pre_existing_native_valve_disease") else 0
    score += 4 if _bool_input(inputs, "intravenous_drug_use") else 0
    score += 3 if _bool_input(inputs, "persistent_bacteremia_48h") else 0
    score += 2 if _bool_input(inputs, "vertebral_osteomyelitis") else 0
    score += 2 if _bool_input(inputs, "community_or_non_nosocomial_acquisition") else 0
    score += 1 if _bool_input(inputs, "severe_sepsis_or_shock") else 0
    score += 1 if _bool_input(inputs, "crp_greater_than_190_mg_l") else 0

    interpretation = (
        "VIRSTA low risk for infective endocarditis in S. aureus bacteremia."
        if score < 3
        else "VIRSTA high risk for infective endocarditis in S. aureus bacteremia."
    )
    return result(metadata, score, "points", interpretation)
