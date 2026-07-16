from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _bool_input(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0 or value == 1:
        return bool(value)
    raise ValueError(f"{key} must be a bool or 0/1")


def _nonnegative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _choice_input(inputs: dict[str, Any], key: str, allowed: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)
    value = str(inputs[key]).strip().lower()
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
    return value


def wells_dvt_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    risk_item_keys = (
        "active_cancer",
        "paralysis_paresis_or_recent_cast",
        "recent_bedridden_or_major_surgery",
        "localized_tenderness",
        "entire_leg_swollen",
        "calf_swelling_3cm",
        "pitting_edema",
        "collateral_superficial_veins",
        "previous_dvt",
    )
    value = sum(1 for key in risk_item_keys if _bool_input(inputs, key))
    if _bool_input(inputs, "alternative_diagnosis_at_least_as_likely"):
        value -= 2

    category = "DVT likely" if value >= 2 else "DVT unlikely"
    interpretation = (
        f"Two-level Wells DVT: {category}. Original low/moderate/high probability categories can vary by source "
        "and should be interpreted with the clinical context."
    )
    return result(metadata, value, "points", interpretation)


def wells_pe_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0.0
    if _bool_input(inputs, "clinical_signs_dvt"):
        value += 3
    if _bool_input(inputs, "pe_most_likely"):
        value += 3
    if number(inputs, "heart_rate") > 100:
        value += 1.5
    if _bool_input(inputs, "immobilization_or_surgery"):
        value += 1.5
    if _bool_input(inputs, "previous_dvt_pe"):
        value += 1.5
    if _bool_input(inputs, "hemoptysis"):
        value += 1
    if _bool_input(inputs, "malignancy"):
        value += 1

    category = "PE likely" if value > 4 else "PE unlikely"
    interpretation = f"Two-level Wells PE: {category}. Interpret alongside pretest probability and clinical context."
    return result(metadata, value, "points", interpretation)


def improve_vte_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0
    if _bool_input(inputs, "previous_vte"):
        value += 3
    if _bool_input(inputs, "known_thrombophilia"):
        value += 2
    if _bool_input(inputs, "lower_limb_paralysis"):
        value += 2
    if _bool_input(inputs, "current_cancer"):
        value += 2
    if _bool_input(inputs, "immobilized_7_days"):
        value += 1
    if _bool_input(inputs, "icu_or_ccu_stay"):
        value += 1
    if number(inputs, "age_years") > 60:
        value += 1

    interpretation = (
        "IMPROVE VTE: high venous thromboembolism risk."
        if value >= 4
        else "IMPROVE VTE: lower venous thromboembolism risk."
    )
    return result(metadata, value, "points", interpretation)


def improve_bleeding_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    platelets = number(inputs, "platelets_10e9_l")
    if platelets <= 0:
        raise ValueError("platelets_10e9_l must be greater than 0")
    age = number(inputs, "age_years")
    if age < 0:
        raise ValueError("age_years must be greater than or equal to 0")
    gfr = number(inputs, "gfr_ml_min")
    if gfr < 0:
        raise ValueError("gfr_ml_min must be greater than or equal to 0")
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")

    value = 0.0
    if _bool_input(inputs, "active_gastroduodenal_ulcer"):
        value += 4.5
    if _bool_input(inputs, "bleeding_within_3_months"):
        value += 4
    if platelets < 50:
        value += 4
    if age >= 85:
        value += 3.5
    elif age >= 40:
        value += 1.5
    if _bool_input(inputs, "hepatic_failure_inr_gt_1_5"):
        value += 2.5
    if gfr < 30:
        value += 2.5
    elif gfr < 60:
        value += 1
    if _bool_input(inputs, "icu_or_ccu_stay"):
        value += 2.5
    if _bool_input(inputs, "central_venous_catheter"):
        value += 2
    if _bool_input(inputs, "rheumatic_disease"):
        value += 2
    if _bool_input(inputs, "current_cancer"):
        value += 2
    if sex == "male":
        value += 1

    interpretation = (
        "IMPROVE Bleeding: high bleeding risk."
        if value >= 7
        else "IMPROVE Bleeding: lower bleeding risk."
    )
    return result(metadata, value, "points", interpretation)


def khorana_cancer_vte_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    site = str(inputs.get("cancer_site", "")).strip().lower()
    site_points = {"very_high_risk": 2, "high_risk": 1, "other": 0}
    if site not in site_points:
        raise ValueError("cancer_site must be one of: very_high_risk, high_risk, other")

    value = site_points[site]
    if _nonnegative_number(inputs, "platelets_10e9_l") >= 350:
        value += 1
    if _nonnegative_number(inputs, "hemoglobin_g_dl") < 10 or _bool_input(inputs, "using_esa"):
        value += 1
    if _nonnegative_number(inputs, "wbc_10e9_l") > 11:
        value += 1
    if _nonnegative_number(inputs, "bmi") >= 35:
        value += 1

    if value >= 3:
        risk = "high"
    elif value >= 1:
        risk = "intermediate"
    else:
        risk = "low"
    return result(metadata, value, "points", f"Khorana cancer-associated VTE risk: {risk}.")


def vte_bleed_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0.0
    if _bool_input(inputs, "active_cancer"):
        value += 2
    if _bool_input(inputs, "male_with_uncontrolled_hypertension"):
        value += 1
    if _bool_input(inputs, "anemia"):
        value += 1.5
    if _bool_input(inputs, "history_of_bleeding"):
        value += 1.5
    if number(inputs, "age_years") >= 60:
        value += 1.5
    if _bool_input(inputs, "renal_dysfunction"):
        value += 1.5

    risk = "high bleeding risk" if value >= 2 else "low bleeding risk"
    return result(metadata, value, "points", f"VTE-BLEED: {risk} during anticoagulation.")


def bova_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 0
    systolic_bp = number(inputs, "systolic_bp")
    if systolic_bp < 90:
        raise ValueError("Bova Score applies to hemodynamically stable PE with systolic_bp >= 90")
    if 90 <= systolic_bp <= 100:
        value += 2
    if _bool_input(inputs, "elevated_troponin"):
        value += 2
    if _bool_input(inputs, "right_ventricular_dysfunction"):
        value += 2
    if number(inputs, "heart_rate") >= 110:
        value += 1

    if value <= 2:
        stage = "stage I"
    elif value <= 4:
        stage = "stage II"
    else:
        stage = "stage III"
    return result(metadata, value, "points", f"Bova Score: {stage} PE complication risk.")


def riete_bleeding_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = number(inputs, "age_years")
    if age < 0:
        raise ValueError("age_years must be greater than or equal to 0")

    value = 0.0
    if _bool_input(inputs, "recent_major_bleeding"):
        value += 2
    if _bool_input(inputs, "creatinine_abnormal"):
        value += 1.5
    if _bool_input(inputs, "anemia"):
        value += 1.5
    if _bool_input(inputs, "active_cancer"):
        value += 1
    if _bool_input(inputs, "clinically_overt_pulmonary_embolism"):
        value += 1
    if age > 75:
        value += 1

    if value == 0:
        risk = "low bleeding risk"
    elif value <= 4:
        risk = "intermediate bleeding risk"
    else:
        risk = "high bleeding risk"

    return result(metadata, value, "points", f"RIETE bleeding score: {risk}.")


def dash_vte_recurrence_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _nonnegative_number(inputs, "age_years")
    sex = _choice_input(inputs, "sex", {"male", "female"})

    score = 0
    if _bool_input(inputs, "abnormal_d_dimer_after_anticoagulation"):
        score += 2
    if age <= 50:
        score += 1
    if sex == "male":
        score += 1
    if sex == "female" and _bool_input(inputs, "hormone_associated_vte"):
        score -= 2
    elif sex == "male" and _bool_input(inputs, "hormone_associated_vte"):
        raise ValueError("hormone_associated_vte applies only when sex is female")

    if score <= 1:
        risk = "low recurrence risk"
        annual_risk = "3.1% annual recurrence risk"
    elif score == 2:
        risk = "increased recurrence risk"
        annual_risk = "6.4% annual recurrence risk"
    else:
        risk = "high recurrence risk"
        annual_risk = "12.3% annual recurrence risk"

    return result(metadata, score, "points", f"DASH recurrent VTE score: {risk} ({annual_risk}).")


def herdoo2_vte_recurrence_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = _choice_input(inputs, "sex", {"male", "female"})
    age = _nonnegative_number(inputs, "age_years")
    d_dimer = _nonnegative_number(inputs, "d_dimer_ug_l")
    bmi = _nonnegative_number(inputs, "bmi")

    if sex == "male":
        value = {"score": None, "high_recurrence_risk": True, "sex": sex}
        return CalculationResult(
            calculator_id=metadata.id,
            status="implemented",
            message="calculation completed",
            value=value,
            unit="points",
            interpretation="Men are not classified as low recurrence risk by the Men and HERDOO2 rule.",
        )

    score = 0
    if _bool_input(inputs, "leg_hyperpigmentation_edema_or_redness"):
        score += 1
    if d_dimer >= 250:
        score += 1
    if bmi >= 30:
        score += 1
    if age >= 65:
        score += 1

    high_risk = score >= 2
    risk = "high recurrence risk" if high_risk else "low recurrence risk"
    value = {"score": score, "high_recurrence_risk": high_risk, "sex": sex}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"HERDOO2 score {score}: {risk} for women with unprovoked VTE.",
    )
