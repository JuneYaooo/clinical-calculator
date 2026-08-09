from __future__ import annotations

import math
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


def _sex(inputs: dict[str, Any], key: str = "sex") -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in {"male", "female"}:
        raise ValueError(f"{key} must be 'male' or 'female'")
    return value


def _angina_index(inputs: dict[str, Any], key: str = "angina_index") -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be 0, 1, or 2")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be 0, 1, or 2")

    integer_value = int(numeric_value)
    if integer_value not in {0, 1, 2}:
        raise ValueError(f"{key} must be 0, 1, or 2")
    return integer_value


def _point_risk_result(
    metadata: CalculatorMetadata,
    score: int,
    risk_key: str,
    risk_percent: float,
    interpretation: str,
) -> CalculationResult:
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, risk_key: risk_percent},
        unit="points",
        interpretation=interpretation,
    )


def intracranial_hemorrhage_risk_thrombolytic_mi(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age = number(inputs, "age_years")
    sex = _sex(inputs)
    weight = number(inputs, "weight_kg")
    inr = number(inputs, "inr")
    prothrombin_time = number(inputs, "prothrombin_time_seconds")

    score = 0
    if age >= 75:
        score += 1
    if _boolean_flag(inputs, "race_black"):
        score += 1
    if sex == "female":
        score += 1
    if _boolean_flag(inputs, "prior_stroke"):
        score += 1
    if number(inputs, "systolic_bp") >= 160:
        score += 1
    if (sex == "female" and weight <= 65) or (sex == "male" and weight <= 80):
        score += 1
    if inr > 4 or prothrombin_time > 24:
        score += 1
    if _boolean_flag(inputs, "tpa_instead_other_thrombolytic"):
        score += 1

    if score <= 1:
        risk_percent = 0.69
    elif score == 2:
        risk_percent = 1.02
    elif score == 3:
        risk_percent = 1.63
    elif score == 4:
        risk_percent = 2.49
    else:
        risk_percent = 4.11

    return _point_risk_result(
        metadata,
        score,
        "risk_percent",
        risk_percent,
        f"Intracranial hemorrhage risk after thrombolytic therapy for MI: {risk_percent}%.",
    )


def ptca_mortality_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _boolean_flag(inputs, "cardiogenic_shock"):
        score += 4
    if _boolean_flag(inputs, "chf_class_iii_iv"):
        score += 4
    if _boolean_flag(inputs, "left_main_ptca"):
        score += 3
    if _boolean_flag(inputs, "tachycardia"):
        score += 2
    if _boolean_flag(inputs, "chronic_renal_insufficiency"):
        score += 2
    if number(inputs, "age_years") >= 75:
        score += 2
    if _boolean_flag(inputs, "lesion_type_b2_or_c"):
        score += 1
    if _boolean_flag(inputs, "acute_mi"):
        score += 1
    if _boolean_flag(inputs, "unstable_angina"):
        score += 1
    if _boolean_flag(inputs, "stent_placed"):
        score -= 1

    if score <= 1:
        mortality_percent = 0.4
    elif score <= 3:
        mortality_percent = 2.2
    elif score <= 5:
        mortality_percent = 2.7
    elif score <= 7:
        mortality_percent = 16.7
    elif score <= 9:
        mortality_percent = 21.4
    elif score <= 11:
        mortality_percent = 42.3
    else:
        mortality_percent = 76.0

    return _point_risk_result(
        metadata,
        score,
        "mortality_percent",
        mortality_percent,
        f"PTCA mortality risk estimate: {mortality_percent}%.",
    )


def unstable_angina_outcome_prediction(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "age_years") > 65:
        score += 1
    for key in ("prior_cabg", "aspirin_use", "beta_blocker_use", "st_depression"):
        if _boolean_flag(inputs, key):
            score += 1

    if score <= 1:
        risk_percent = 6.5
    elif score == 2:
        risk_percent = 14.6
    elif score == 3:
        risk_percent = 22.7
    else:
        risk_percent = 37.1

    return _point_risk_result(
        metadata,
        score,
        "risk_percent",
        risk_percent,
        f"Unstable angina adverse outcome risk estimate: {risk_percent}%.",
    )


def non_q_wave_mi_prediction(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _boolean_flag(inputs, "no_prior_angioplasty"):
        score += 1
    if number(inputs, "pain_duration_minutes") >= 60:
        score += 1
    if _boolean_flag(inputs, "st_deviation"):
        score += 1
    if _boolean_flag(inputs, "recent_angina"):
        score += 1

    risk_percent = {0: 7.0, 1: 19.6, 2: 24.4, 3: 49.9, 4: 70.6}[score]
    return _point_risk_result(
        metadata,
        score,
        "risk_percent",
        risk_percent,
        f"Non-Q-wave myocardial infarction prediction risk estimate: {risk_percent}%.",
    )


def timi_stemi_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")

    score = 0
    if age_years >= 75:
        score += 3
    elif age_years >= 65:
        score += 2
    if _boolean_flag(inputs, "diabetes_hypertension_or_angina"):
        score += 1
    if number(inputs, "systolic_bp") < 100:
        score += 3
    if number(inputs, "heart_rate") > 100:
        score += 2
    if _boolean_flag(inputs, "killip_class_ii_to_iv"):
        score += 2
    if number(inputs, "weight_kg") < 67:
        score += 1
    if _boolean_flag(inputs, "anterior_st_elevation_or_lbbb"):
        score += 1
    if number(inputs, "time_to_treatment_hours") > 4:
        score += 1

    interpretation = "higher score indicates higher 30-day mortality risk by TIMI STEMI score"
    return result(metadata, score, "points", interpretation)


def timi_ua_nstemi_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "age_years") >= 65:
        score += 1

    risk_keys = (
        "three_or_more_cad_risk_factors",
        "known_cad_stenosis_50_percent",
        "aspirin_past_7_days",
        "severe_angina_24h",
        "st_deviation",
        "positive_cardiac_marker",
    )
    score += sum(1 for key in risk_keys if _boolean_flag(inputs, key))

    interpretation = "higher score indicates higher 14-day adverse event risk by TIMI UA/NSTEMI score"
    return result(metadata, score, "points", interpretation)


def dapt_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")

    score = 0
    if age_years >= 75:
        score -= 2
    elif age_years >= 65:
        score -= 1

    one_point_keys = (
        "current_smoker",
        "diabetes",
        "mi_at_presentation",
        "prior_pci_or_mi",
        "paclitaxel_eluting_stent",
        "stent_diameter_less_3mm",
    )
    score += sum(1 for key in one_point_keys if _boolean_flag(inputs, key))
    score += 2 * int(_boolean_flag(inputs, "chf_or_lvef_less_30"))
    score += 2 * int(_boolean_flag(inputs, "vein_graft_stent"))

    if score >= 2:
        interpretation = "score >=2 favors prolonged DAPT benefit if bleeding risk acceptable"
    else:
        interpretation = "score <2 does not favor prolonged DAPT benefit; individualize bleeding and ischemic risk"
    return result(metadata, score, "points", interpretation)


def duke_treadmill_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        number(inputs, "exercise_time_minutes")
        - (5 * number(inputs, "st_deviation_mm"))
        - (4 * _angina_index(inputs))
    )

    if score >= 5:
        interpretation = "low risk by Duke treadmill score"
    elif score <= -11:
        interpretation = "high risk by Duke treadmill score"
    else:
        interpretation = "moderate risk by Duke treadmill score"
    return result(metadata, score, "points", interpretation)


def orbit_af_bleeding_risk_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    sex = _sex(inputs)
    hemoglobin_g_dl = number(inputs, "hemoglobin_g_dl")

    score = 0
    if number(inputs, "age_years") >= 75:
        score += 1
    if (sex == "male" and hemoglobin_g_dl < 13) or (sex == "female" and hemoglobin_g_dl < 12):
        score += 2
    if _boolean_flag(inputs, "bleeding_history"):
        score += 2
    if number(inputs, "egfr_ml_min_1_73m2") < 60:
        score += 1
    if _boolean_flag(inputs, "antiplatelet_therapy"):
        score += 1

    if score <= 2:
        interpretation = "low bleeding risk by ORBIT AF bleeding risk score"
    elif score == 3:
        interpretation = "medium bleeding risk by ORBIT AF bleeding risk score"
    else:
        interpretation = "high bleeding risk by ORBIT AF bleeding risk score"
    return result(metadata, score, "points", interpretation)


def h2fpef_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if number(inputs, "bmi") > 30:
        score += 2
    if number(inputs, "antihypertensive_medications_count") >= 2:
        score += 1
    if _boolean_flag(inputs, "atrial_fibrillation"):
        score += 3
    if number(inputs, "pulmonary_artery_systolic_pressure_mm_hg") > 35:
        score += 1
    if number(inputs, "age_years") > 60:
        score += 1
    if number(inputs, "e_over_e_prime") > 9:
        score += 1

    if score <= 1:
        probability = "low probability"
    elif score <= 5:
        probability = "intermediate probability"
    else:
        probability = "high probability"
    return result(metadata, score, "points", f"H2FPEF: {probability} of HFpEF.")


def same_tt2r2_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _sex(inputs) == "female":
        score += 1
    if number(inputs, "age_years") < 60:
        score += 1
    if _boolean_flag(inputs, "two_or_more_comorbidities"):
        score += 1
    if _boolean_flag(inputs, "interacting_drugs"):
        score += 1
    if _boolean_flag(inputs, "tobacco_use_within_2_years"):
        score += 2
    if _boolean_flag(inputs, "non_caucasian_race"):
        score += 2

    if score > 2:
        interpretation = "higher risk of poor warfarin control; consider closer INR support or alternatives"
    else:
        interpretation = "lower risk of poor warfarin control by SAMe-TT2R2"
    return result(metadata, score, "points", interpretation)


def canadian_syncope_risk_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    ed_diagnosis = str(inputs.get("ed_diagnosis", "")).strip().lower()
    if ed_diagnosis not in {"vasovagal", "cardiac", "other"}:
        raise ValueError("ed_diagnosis must be one of: vasovagal, cardiac, other")

    score = 0
    if _boolean_flag(inputs, "predisposition_to_vasovagal_syncope"):
        score -= 1
    if _boolean_flag(inputs, "history_of_heart_disease"):
        score += 1
    if _boolean_flag(inputs, "any_systolic_bp_less_90_or_greater_180"):
        score += 2
    if _boolean_flag(inputs, "elevated_troponin"):
        score += 2
    if _boolean_flag(inputs, "abnormal_qrs_axis"):
        score += 1
    if _boolean_flag(inputs, "qrs_duration_gt_130_ms"):
        score += 1
    if _boolean_flag(inputs, "qtc_gt_480_ms"):
        score += 2
    if ed_diagnosis == "vasovagal":
        score -= 2
    elif ed_diagnosis == "cardiac":
        score += 2

    if score <= -2:
        risk = "very low risk"
    elif score <= 0:
        risk = "low risk"
    elif score <= 3:
        risk = "medium risk"
    elif score <= 5:
        risk = "high risk"
    else:
        risk = "very high risk"
    return result(metadata, score, "points", f"Canadian Syncope Risk Score: {risk}.")


def additive_euroscore(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")
    if age_years < 0:
        raise ValueError("age_years must be non-negative")

    score = min(8, max(0, (age_years - 55) // 5))
    if _sex(inputs) == "female":
        score += 1

    point_items = (
        ("chronic_pulmonary_disease", 1),
        ("extracardiac_arteriopathy", 2),
        ("neurologic_dysfunction", 2),
        ("previous_cardiac_surgery", 3),
        ("serum_creatinine_gt_200_umol_l", 2),
        ("active_endocarditis", 3),
        ("critical_preoperative_state", 3),
        ("unstable_angina_iv_nitrates", 2),
        ("recent_mi_90_days", 2),
        ("pulmonary_hypertension", 2),
        ("emergency_operation", 2),
        ("other_than_isolated_cabg", 2),
        ("thoracic_aorta_surgery", 3),
        ("postinfarct_septal_rupture", 4),
    )
    for key, points in point_items:
        if _boolean_flag(inputs, key):
            score += points

    lv_function = str(inputs.get("left_ventricular_function", "")).strip().lower()
    lv_points = {"good": 0, "moderate": 1, "poor": 3}
    if lv_function not in lv_points:
        raise ValueError("left_ventricular_function must be one of: good, moderate, poor")
    score += lv_points[lv_function]

    if score <= 2:
        risk = "low operative risk"
    elif score <= 5:
        risk = "medium operative risk"
    else:
        risk = "high operative risk"
    return result(metadata, score, "points", f"Additive EuroSCORE: {risk}.")


def _points_from_ranges(value: float, ranges: tuple[tuple[float, float, int], ...], key: str) -> int:
    for lower, upper, points in ranges:
        if lower <= value <= upper:
            return points
    raise ValueError(f"{key} is outside the supported scoring range")


def grace_acs_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_points = _points_from_ranges(
        number(inputs, "age_years"),
        (
            (0, 29, 0),
            (30, 39, 8),
            (40, 49, 25),
            (50, 59, 41),
            (60, 69, 58),
            (70, 79, 75),
            (80, 89, 91),
            (90, 200, 100),
        ),
        "age_years",
    )
    heart_rate_points = _points_from_ranges(
        number(inputs, "heart_rate"),
        (
            (0, 49, 0),
            (50, 69, 3),
            (70, 89, 9),
            (90, 109, 15),
            (110, 149, 24),
            (150, 199, 38),
            (200, 400, 46),
        ),
        "heart_rate",
    )
    systolic_bp_points = _points_from_ranges(
        number(inputs, "systolic_bp"),
        (
            (0, 79, 58),
            (80, 99, 53),
            (100, 119, 43),
            (120, 139, 34),
            (140, 159, 24),
            (160, 199, 10),
            (200, 400, 0),
        ),
        "systolic_bp",
    )
    creatinine_points = _points_from_ranges(
        number(inputs, "creatinine_mg_dl"),
        (
            (0, 0.39, 1),
            (0.4, 0.79, 4),
            (0.8, 1.19, 7),
            (1.2, 1.59, 10),
            (1.6, 1.99, 13),
            (2.0, 3.99, 21),
            (4.0, 20.0, 28),
        ),
        "creatinine_mg_dl",
    )

    killip_class = int(number(inputs, "killip_class"))
    if killip_class not in {1, 2, 3, 4}:
        raise ValueError("killip_class must be 1, 2, 3, or 4")
    killip_points = {1: 0, 2: 20, 3: 39, 4: 59}[killip_class]

    score = age_points + heart_rate_points + systolic_bp_points + creatinine_points + killip_points
    score += 39 * int(_boolean_flag(inputs, "cardiac_arrest_at_admission"))
    score += 28 * int(_boolean_flag(inputs, "st_segment_deviation"))
    score += 14 * int(_boolean_flag(inputs, "elevated_cardiac_markers"))

    if score <= 108:
        risk = "low risk"
    elif score <= 140:
        risk = "intermediate risk"
    else:
        risk = "high risk"
    return result(metadata, score, "points", f"GRACE ACS Risk Score: {risk}.")
