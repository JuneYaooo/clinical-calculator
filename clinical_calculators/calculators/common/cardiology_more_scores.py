from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _coded_0_to_2(inputs: dict[str, Any], key: str) -> int:
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


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def _non_negative_integer(inputs: dict[str, Any], key: str) -> int:
    value = _non_negative_number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be a non-negative integer")
    return int(value)


def heart_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _non_negative_number(inputs, "age_years")
    risk_factors_count = _non_negative_integer(inputs, "risk_factors_count")
    troponin_multiple = _non_negative_number(inputs, "troponin_multiple_of_normal_limit")

    score = _coded_0_to_2(inputs, "history") + _coded_0_to_2(inputs, "ecg")

    if age_years >= 65:
        score += 2
    elif age_years >= 45:
        score += 1

    if _boolean_flag(inputs, "known_atherosclerotic_disease") or risk_factors_count >= 3:
        score += 2
    elif risk_factors_count >= 1:
        score += 1

    if troponin_multiple > 3:
        score += 2
    elif troponin_multiple > 1:
        score += 1

    if score <= 3:
        interpretation = "low risk by HEART chest pain score"
    elif score <= 6:
        interpretation = "moderate risk by HEART chest pain score"
    else:
        interpretation = "high risk by HEART chest pain score"
    return result(metadata, score, "points", interpretation)


def romhilt_estes_lvh_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = 0
    if _boolean_flag(inputs, "voltage_criteria"):
        score += 3

    if _boolean_flag(inputs, "st_t_abnormality_without_digitalis"):
        score += 3
    elif _boolean_flag(inputs, "st_t_abnormality_with_digitalis"):
        score += 1

    if _boolean_flag(inputs, "left_atrial_enlargement"):
        score += 3
    if _boolean_flag(inputs, "left_axis_deviation"):
        score += 2
    if _non_negative_number(inputs, "qrs_duration_ms") >= 90:
        score += 1
    if _non_negative_number(inputs, "intrinsicoid_deflection_ms") >= 50:
        score += 1

    if score >= 5:
        interpretation = "definite LVH by Romhilt-Estes criteria"
    elif score == 4:
        interpretation = "probable LVH by Romhilt-Estes criteria"
    else:
        interpretation = "not diagnostic for LVH by Romhilt-Estes criteria"
    return result(metadata, score, "points", interpretation)


def modified_sgarbossa_criteria_lbbb(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    positive_criteria = 0

    if number(inputs, "concordant_st_elevation_mm") >= 1:
        positive_criteria += 1
    if number(inputs, "concordant_st_depression_v1_v3_mm") >= 1:
        positive_criteria += 1

    preceding_s_wave_depth_mm = _non_negative_number(inputs, "preceding_s_wave_depth_mm")
    if preceding_s_wave_depth_mm <= 0:
        raise ValueError("preceding_s_wave_depth_mm must be positive")

    discordant_st_elevation_mm = number(inputs, "discordant_st_elevation_mm")
    if abs(discordant_st_elevation_mm) / preceding_s_wave_depth_mm >= 0.25:
        positive_criteria += 1

    if positive_criteria:
        interpretation = "positive Modified Sgarbossa criteria for MI in LBBB"
    else:
        interpretation = "negative Modified Sgarbossa criteria for MI in LBBB"
    return result(metadata, positive_criteria, "criteria", interpretation)


def heart_pathway_low_risk_chest_pain_rule(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    heart = heart_score(metadata, inputs).value
    serial_troponin_positive = _boolean_flag(inputs, "troponin_0h_positive") or _boolean_flag(
        inputs, "troponin_3h_positive"
    )
    ischemic_ecg = _boolean_flag(inputs, "new_ischemic_ecg_changes")
    known_cad = _boolean_flag(inputs, "known_coronary_artery_disease")

    low_risk = heart <= 3 and not serial_troponin_positive and not ischemic_ecg and not known_cad
    if low_risk:
        interpretation = (
            f"HEART Pathway low risk: HEART score {heart}, negative 0- and 3-hour troponins, "
            "no new ischemic ECG changes, and no known coronary artery disease."
        )
    else:
        interpretation = (
            f"HEART Pathway not low risk: HEART score {heart}; evaluate serial troponins, ECG, "
            "known coronary artery disease, and clinical context."
        )
    return result(metadata, int(low_risk), "classification", interpretation)


def _biomarker_score(inputs: dict[str, Any]) -> int:
    has_bnp = "bnp_pg_ml" in inputs
    has_nt_probnp = "nt_probnp_pg_ml" in inputs
    if has_bnp == has_nt_probnp:
        raise ValueError("provide exactly one of bnp_pg_ml or nt_probnp_pg_ml")

    if has_bnp:
        bnp = _non_negative_number(inputs, "bnp_pg_ml")
        if bnp < 50:
            return -2
        if bnp < 200:
            return 0
        if bnp < 800:
            return 1
        return 2

    nt_probnp = _non_negative_number(inputs, "nt_probnp_pg_ml")
    if nt_probnp < 300:
        return -2
    if nt_probnp < 1100:
        return 0
    return 2


def reveal_2_0_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 6

    if _non_negative_number(inputs, "egfr_ml_min_1_73m2") < 60:
        score += 1

    functional_class = int(_non_negative_integer(inputs, "who_functional_class"))
    if functional_class not in {1, 2, 3, 4}:
        raise ValueError("who_functional_class must be 1, 2, 3, or 4")
    score += {1: -1, 2: 0, 3: 1, 4: 2}[functional_class]

    if number(inputs, "systolic_bp") < 110:
        score += 1
    if _non_negative_number(inputs, "heart_rate") > 96:
        score += 1

    walk_distance = _non_negative_number(inputs, "six_minute_walk_distance_m")
    if walk_distance >= 440:
        score -= 2
    elif walk_distance >= 320:
        score -= 1
    elif walk_distance < 165:
        score += 1

    score += _biomarker_score(inputs)

    etiology = str(inputs.get("etiology", "")).strip().lower()
    etiology_points = {
        "pop_h": 3,
        "portopulmonary": 3,
        "familial": 2,
        "connective_tissue_disease": 1,
        "other": 0,
    }
    if etiology not in etiology_points:
        raise ValueError(
            "etiology must be one of: pop_h, portopulmonary, familial, connective_tissue_disease, other"
        )
    score += etiology_points[etiology]

    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    if sex == "male" and _non_negative_number(inputs, "age_years") > 60:
        score += 2

    if _boolean_flag(inputs, "hospitalization_within_6_months"):
        score += 1
    if _boolean_flag(inputs, "pericardial_effusion"):
        score += 1
    if _non_negative_number(inputs, "dlco_percent_predicted") < 40:
        score += 1
    if _non_negative_number(inputs, "mean_right_atrial_pressure_mm_hg") > 20:
        score += 1
    if _non_negative_number(inputs, "pvr_wood_units") < 5:
        score -= 1

    if score <= 6:
        risk = "low risk"
    elif score <= 8:
        risk = "intermediate risk"
    else:
        risk = "high risk"
    return result(metadata, score, "points", f"REVEAL 2.0: {risk} for PAH survival risk.")


def esc_ers_pah_four_strata_risk_assessment(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    functional_class = int(_non_negative_integer(inputs, "who_functional_class"))
    if functional_class not in {1, 2, 3, 4}:
        raise ValueError("who_functional_class must be 1, 2, 3, or 4")
    fc_points = {1: 1, 2: 1, 3: 3, 4: 4}[functional_class]

    walk_distance = _non_negative_number(inputs, "six_minute_walk_distance_m")
    if walk_distance > 440:
        walk_points = 1
    elif walk_distance >= 320:
        walk_points = 2
    elif walk_distance >= 165:
        walk_points = 3
    else:
        walk_points = 4

    has_bnp = "bnp_pg_ml" in inputs
    has_nt_probnp = "nt_probnp_pg_ml" in inputs
    if has_bnp == has_nt_probnp:
        raise ValueError("provide exactly one of bnp_pg_ml or nt_probnp_pg_ml")
    if has_bnp:
        biomarker = _non_negative_number(inputs, "bnp_pg_ml")
        if biomarker < 50:
            biomarker_points = 1
        elif biomarker < 200:
            biomarker_points = 2
        elif biomarker <= 800:
            biomarker_points = 3
        else:
            biomarker_points = 4
    else:
        biomarker = _non_negative_number(inputs, "nt_probnp_pg_ml")
        if biomarker < 300:
            biomarker_points = 1
        elif biomarker < 650:
            biomarker_points = 2
        elif biomarker <= 1100:
            biomarker_points = 3
        else:
            biomarker_points = 4

    mean_score = round((fc_points + walk_points + biomarker_points) / 3)
    risk = {
        1: "low risk",
        2: "intermediate-low risk",
        3: "intermediate-high risk",
        4: "high risk",
    }[mean_score]
    return result(metadata, mean_score, "mean points", f"ESC/ERS PAH four-strata assessment: {risk}.")


def hfa_peff_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    functional_points = _non_negative_integer(inputs, "functional_domain_points")
    morphological_points = _non_negative_integer(inputs, "morphological_domain_points")
    biomarker_points = _non_negative_integer(inputs, "biomarker_domain_points")

    for key, value in (
        ("functional_domain_points", functional_points),
        ("morphological_domain_points", morphological_points),
        ("biomarker_domain_points", biomarker_points),
    ):
        if value > 2:
            raise ValueError(f"{key} must be 0, 1, or 2")

    score = functional_points + morphological_points + biomarker_points
    if score >= 5:
        interpretation = "HFA-PEFF score diagnostic for HFpEF in the appropriate clinical context."
    elif score >= 2:
        interpretation = "HFA-PEFF score intermediate; functional testing or invasive hemodynamics is typically needed."
    else:
        interpretation = "HFA-PEFF score low; HFpEF is unlikely by this scoring algorithm."
    return result(metadata, score, "points", interpretation)


def brugada_criteria_wide_complex_tachycardia(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if _boolean_flag(inputs, "rs_complex_absent_all_precordial_leads"):
        return result(metadata, 1, "classification", "Brugada criteria step 1 supports VT.")
    if _non_negative_number(inputs, "longest_rs_interval_ms") > 100:
        return result(metadata, 1, "classification", "Brugada criteria step 2 supports VT.")
    if _boolean_flag(inputs, "av_dissociation"):
        return result(metadata, 1, "classification", "Brugada criteria step 3 supports VT.")
    if _boolean_flag(inputs, "vt_morphology_criteria_present"):
        return result(metadata, 1, "classification", "Brugada criteria step 4 supports VT.")
    return result(metadata, 0, "classification", "Brugada criteria support SVT with aberrancy.")


def vereckei_avr_algorithm(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if _boolean_flag(inputs, "initial_r_wave_present"):
        return result(metadata, 1, "classification", "Vereckei aVR algorithm step 1 supports VT.")
    if _non_negative_number(inputs, "initial_r_or_q_duration_ms") > 40:
        return result(metadata, 1, "classification", "Vereckei aVR algorithm step 2 supports VT.")
    if _boolean_flag(inputs, "notching_initial_downstroke"):
        return result(metadata, 1, "classification", "Vereckei aVR algorithm step 3 supports VT.")

    ratio = _non_negative_number(inputs, "initial_to_terminal_activation_velocity_ratio")
    if ratio <= 0:
        raise ValueError("initial_to_terminal_activation_velocity_ratio must be positive")
    if ratio <= 1:
        return result(metadata, 1, "classification", "Vereckei aVR algorithm step 4 supports VT.")
    return result(metadata, 0, "classification", "Vereckei aVR algorithm supports SVT with aberrancy.")
