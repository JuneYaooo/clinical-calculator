from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{key} must be finite")
    return numeric


def _integer(inputs: dict[str, Any], key: str) -> int:
    value = _number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    return int(value)


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = _integer(inputs, key)
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def _nonnegative_integer(inputs: dict[str, Any], key: str) -> int:
    value = _integer(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return value


def _boolean_flag(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _score_true(inputs: dict[str, Any], key: str, points: int = 1) -> int:
    return points if _boolean_flag(inputs, key) else 0


def _component_points(inputs: dict[str, Any], key: str, allowed: set[int]) -> int:
    value = _integer(inputs, key)
    if value not in allowed:
        allowed_values = ", ".join(str(point) for point in sorted(allowed))
        raise ValueError(f"{key} must be one of: {allowed_values}")
    return value


def pediatric_respiratory_assessment_measure(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = (
        _component_points(inputs, "suprasternal_retractions", {0, 2})
        + _component_points(inputs, "scalene_muscle_contraction", {0, 2})
        + _component_points(inputs, "air_entry", {0, 1, 2, 3})
        + _component_points(inputs, "wheezing", {0, 1, 2, 3})
        + _component_points(inputs, "oxygen_saturation", {0, 1, 2})
    )
    if score <= 3:
        severity = "mild"
    elif score <= 7:
        severity = "moderate"
    else:
        severity = "severe"
    return result(metadata, score, "points", f"PRAM pediatric asthma severity: {severity}.")


def westley_croup_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _component_points(inputs, "level_of_consciousness", {0, 5})
        + _component_points(inputs, "cyanosis", {0, 4, 5})
        + _component_points(inputs, "stridor", {0, 1, 2})
        + _component_points(inputs, "air_entry", {0, 1, 2})
        + _component_points(inputs, "retractions", {0, 1, 2, 3})
    )

    if score <= 2:
        interpretation = "mild croup severity by Westley croup score"
    elif score <= 5:
        interpretation = "moderate croup severity by Westley croup score"
    elif score <= 11:
        interpretation = "severe croup severity by Westley croup score"
    else:
        interpretation = "impending respiratory failure by Westley croup score"

    return result(metadata, score, "points", interpretation)


def pediatric_appendicitis_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _score_true(inputs, "cough_percussion_hopping_tenderness", 2)
        + _score_true(inputs, "anorexia")
        + _score_true(inputs, "fever")
        + _score_true(inputs, "nausea_vomiting")
        + _score_true(inputs, "rlq_tenderness", 2)
        + _score_true(inputs, "leukocytosis")
        + _score_true(inputs, "neutrophilia")
        + _score_true(inputs, "migration_pain")
    )

    if score <= 3:
        interpretation = "low risk by Pediatric Appendicitis Score"
    elif score <= 6:
        interpretation = "equivocal risk by Pediatric Appendicitis Score"
    else:
        interpretation = "high risk by Pediatric Appendicitis Score"

    return result(metadata, score, "points", interpretation)


def duke_infective_endocarditis_criteria(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    major = _integer_in_range(inputs, "major_criteria_count", 0, 2)
    minor = _integer_in_range(inputs, "minor_criteria_count", 0, 5)

    if major >= 2 or (major == 1 and minor >= 3) or minor >= 5:
        classification = "definite"
    elif (major == 1 and minor >= 1) or minor >= 3:
        classification = "possible"
    else:
        classification = "rejected"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"major": major, "minor": minor, "classification": classification},
        unit="",
        interpretation=f"{classification} infective endocarditis by Modified Duke Criteria",
    )


def mascc_febrile_neutropenia_risk_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    burden_scores = {
        "none_or_mild": 5,
        "moderate": 3,
        "severe": 0,
    }
    if "burden_of_illness" not in inputs:
        raise KeyError("burden_of_illness")

    burden = str(inputs["burden_of_illness"]).strip().lower()
    if burden not in burden_scores:
        raise ValueError("burden_of_illness must be none_or_mild, moderate, or severe")

    score = burden_scores[burden]
    score += _score_true(inputs, "no_hypotension", 5)
    score += _score_true(inputs, "no_copd", 4)
    score += _score_true(inputs, "solid_tumor_or_no_fungal_infection", 4)
    score += _score_true(inputs, "no_dehydration", 3)
    score += _score_true(inputs, "outpatient_status", 3)
    score += _score_true(inputs, "age_less_than_60", 2)

    interpretation = (
        "low risk by MASCC febrile neutropenia risk index"
        if score >= 21
        else "high risk by MASCC febrile neutropenia risk index"
    )
    return result(metadata, score, "points", interpretation)


def covid_4c_mortality_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _number(inputs, "age_years")
    if age < 0:
        raise ValueError("age_years must be nonnegative")

    if age >= 80:
        score = 7
    elif age >= 70:
        score = 6
    elif age >= 60:
        score = 4
    elif age >= 50:
        score = 2
    else:
        score = 0

    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be female or male")
    if sex == "male":
        score += 1

    comorbidity_count = _nonnegative_integer(inputs, "comorbidity_count")
    if comorbidity_count >= 2:
        score += 2
    elif comorbidity_count == 1:
        score += 1

    respiratory_rate = _number(inputs, "respiratory_rate")
    if respiratory_rate < 0:
        raise ValueError("respiratory_rate must be nonnegative")
    if respiratory_rate >= 30:
        score += 2
    elif respiratory_rate >= 20:
        score += 1

    oxygen_saturation = _number(inputs, "oxygen_saturation_percent")
    if oxygen_saturation < 0 or oxygen_saturation > 100:
        raise ValueError("oxygen_saturation_percent must be between 0 and 100")
    if oxygen_saturation < 92:
        score += 2

    gcs = _number(inputs, "gcs")
    if gcs < 3 or gcs > 15:
        raise ValueError("gcs must be between 3 and 15")
    if gcs < 15:
        score += 2

    urea = _number(inputs, "urea_mmol_l")
    if urea < 0:
        raise ValueError("urea_mmol_l must be nonnegative")
    if urea > 14:
        score += 3
    elif urea >= 7:
        score += 1

    crp = _number(inputs, "crp_mg_l")
    if crp < 0:
        raise ValueError("crp_mg_l must be nonnegative")
    if crp >= 100:
        score += 2
    elif crp >= 50:
        score += 1

    if score <= 3:
        interpretation = "low risk by 4C COVID-19 mortality score"
    elif score <= 8:
        interpretation = "intermediate risk by 4C COVID-19 mortality score"
    elif score <= 14:
        interpretation = "high risk by 4C COVID-19 mortality score"
    else:
        interpretation = "very high risk by 4C COVID-19 mortality score"

    return result(metadata, score, "points", interpretation)


def pediatric_early_warning_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "behavior", 0, 3)
        + _integer_in_range(inputs, "cardiovascular", 0, 3)
        + _integer_in_range(inputs, "respiratory", 0, 3)
        + _score_true(inputs, "quarter_hourly_nebulizers")
        + _score_true(inputs, "persistent_postoperative_vomiting")
    )

    if score >= 3:
        interpretation = "higher risk by PEWS; consider escalation of care and increased assessment frequency"
    else:
        interpretation = "lower risk by PEWS; continue routine monitoring unless clinical concern changes"

    return result(metadata, score, "points", interpretation)


def _two_sided_vital_points(
    value: float,
    bands: tuple[tuple[int, float, bool, float, bool], ...],
) -> int:
    """Return the first (most severe) matching high/low source-table band."""
    for points, high, include_high, low, include_low in bands:
        high_match = value >= high if include_high else value > high
        low_match = value <= low if include_low else value < low
        if high_match or low_match:
            return points
    return 0


def bedside_pediatric_early_warning_system(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Original seven-item Bedside PEWS (Parshuram et al., 2009)."""
    age_months = _number(inputs, "age_months")
    if age_months < 0 or age_months >= 216:
        raise ValueError("age_months must be from 0 up to but not including 216")

    heart_rate = _number(inputs, "heart_rate_bpm")
    systolic_bp = _number(inputs, "systolic_bp_mm_hg")
    capillary_refill = _number(inputs, "capillary_refill_seconds")
    respiratory_rate = _number(inputs, "respiratory_rate_breaths_min")
    oxygen_saturation = _number(inputs, "oxygen_saturation_percent")
    for key, value in (
        ("heart_rate_bpm", heart_rate),
        ("systolic_bp_mm_hg", systolic_bp),
        ("capillary_refill_seconds", capillary_refill),
        ("respiratory_rate_breaths_min", respiratory_rate),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")
    if oxygen_saturation < 0 or oxygen_saturation > 100:
        raise ValueError("oxygen_saturation_percent must be between 0 and 100")

    # Published age labels are operationalized as half-open bands: 0–<3,
    # 3–<12, 12–<48, 48–<144, and 144–<216 months.
    if age_months < 3:
        heart_bands = (
            (4, 190, True, 80, True),
            (2, 180, True, 90, True),
            (1, 150, True, 110, True),
        )
        bp_bands = (
            (4, 130, True, 45, True),
            (2, 100, True, 50, True),
            (1, 80, True, 60, True),
        )
        respiratory_bands = (
            (4, 91, True, 15, True),
            (2, 81, True, 19, True),
            (1, 61, True, 29, True),
        )
    elif age_months < 12:
        heart_bands = (
            (4, 180, True, 70, True),
            (2, 170, True, 80, True),
            (1, 150, True, 100, True),
        )
        bp_bands = (
            (4, 150, True, 60, True),
            (2, 120, True, 70, True),
            (1, 100, True, 80, True),
        )
        respiratory_bands = (
            (4, 81, True, 15, True),
            (2, 71, True, 19, True),
            (1, 51, True, 24, True),
        )
    elif age_months < 48:
        heart_bands = (
            (4, 170, True, 60, True),
            (2, 150, True, 70, True),
            (1, 120, True, 90, True),
        )
        bp_bands = (
            (4, 160, True, 65, True),
            (2, 125, True, 75, True),
            (1, 110, True, 90, True),
        )
        respiratory_bands = (
            (4, 71, True, 12, True),
            (2, 61, True, 15, True),
            (1, 41, True, 19, True),
        )
    elif age_months < 144:
        heart_bands = (
            (4, 150, False, 50, True),
            (2, 130, True, 60, True),
            (1, 110, True, 70, True),
        )
        bp_bands = (
            (4, 170, True, 70, True),
            (2, 140, True, 80, True),
            (1, 120, True, 90, True),
        )
        respiratory_bands = (
            (4, 51, True, 10, True),
            (2, 41, True, 14, True),
            (1, 31, True, 19, True),
        )
    else:
        heart_bands = (
            (4, 140, True, 40, True),
            (2, 120, True, 50, False),
            (1, 100, True, 60, True),
        )
        bp_bands = (
            (4, 190, True, 75, True),
            (2, 150, True, 85, True),
            (1, 130, True, 100, True),
        )
        respiratory_bands = (
            (4, 30, True, 9, True),
            (2, 23, True, 10, True),
            (1, 17, True, 11, True),
        )

    respiratory_effort = inputs.get("respiratory_effort")
    respiratory_effort_points = {
        "normal": 0,
        "mild": 1,
        "moderate": 2,
        "severe_or_apnea": 4,
    }
    if respiratory_effort not in respiratory_effort_points:
        raise ValueError(
            "respiratory_effort must be normal, mild, moderate, or severe_or_apnea"
        )
    oxygen_therapy = inputs.get("oxygen_therapy")
    oxygen_therapy_points = {"room_air": 0, "low": 2, "high": 4}
    if oxygen_therapy not in oxygen_therapy_points:
        raise ValueError("oxygen_therapy must be room_air, low, or high")

    score = (
        _two_sided_vital_points(heart_rate, heart_bands)
        + _two_sided_vital_points(systolic_bp, bp_bands)
        + (4 if capillary_refill >= 3 else 0)
        + _two_sided_vital_points(respiratory_rate, respiratory_bands)
        + respiratory_effort_points[respiratory_effort]
        + (0 if oxygen_saturation > 94 else 1 if oxygen_saturation >= 91 else 2)
        + oxygen_therapy_points[oxygen_therapy]
    )
    interpretation = (
        "Bedside PEWS at or above 8, the original validation threshold associated with "
        "82% sensitivity and 93% specificity for urgent PICU admission."
        if score >= 8
        else "Bedside PEWS below 8; continue clinical assessment because a lower score does "
        "not exclude deterioration."
    )
    return result(metadata, score, "points", interpretation)


def rochester_criteria_febrile_infant(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_days = _number(inputs, "age_days")
    if age_days < 0 or age_days > 60:
        raise ValueError("age_days must be between 0 and 60")

    wbc = _number(inputs, "wbc_10e9_l")
    bands = _number(inputs, "absolute_band_count_10e9_l")
    urine_wbc = _number(inputs, "urine_wbc_per_hpf")
    stool_wbc = _number(inputs, "stool_wbc_per_hpf")
    for key, value in (
        ("wbc_10e9_l", wbc),
        ("absolute_band_count_10e9_l", bands),
        ("urine_wbc_per_hpf", urine_wbc),
        ("stool_wbc_per_hpf", stool_wbc),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")

    failed = 0
    failed += 0 if _boolean_flag(inputs, "well_appearing") else 1
    failed += 0 if _boolean_flag(inputs, "previously_healthy") else 1
    failed += 0 if 5 <= wbc <= 15 else 1
    failed += 0 if bands <= 1.5 else 1
    failed += 0 if urine_wbc <= 10 else 1
    if _boolean_flag(inputs, "diarrhea") and stool_wbc > 5:
        failed += 1

    low_risk = failed == 0
    interpretation = (
        "Rochester criteria low risk for serious bacterial infection."
        if low_risk
        else "Rochester criteria not low risk for serious bacterial infection."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"low_risk": low_risk, "criteria_failed": failed},
        unit="criteria",
        interpretation=interpretation,
    )


def philadelphia_criteria_febrile_infant(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_days = _number(inputs, "age_days")
    if age_days < 29 or age_days > 60:
        raise ValueError("age_days must be between 29 and 60")

    wbc = _number(inputs, "wbc_10e9_l")
    band_ratio = _number(inputs, "band_to_neutrophil_ratio")
    urine_wbc = _number(inputs, "urine_wbc_per_hpf")
    csf_wbc = _number(inputs, "csf_wbc_per_uL")
    stool_wbc = _number(inputs, "stool_wbc_per_hpf")
    for key, value in (
        ("wbc_10e9_l", wbc),
        ("band_to_neutrophil_ratio", band_ratio),
        ("urine_wbc_per_hpf", urine_wbc),
        ("csf_wbc_per_uL", csf_wbc),
        ("stool_wbc_per_hpf", stool_wbc),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")

    failed = 0
    failed += 0 if _boolean_flag(inputs, "well_appearing") else 1
    failed += 0 if 5 <= wbc <= 15 else 1
    failed += 0 if band_ratio < 0.2 else 1
    failed += 0 if urine_wbc < 10 else 1
    failed += 0 if csf_wbc < 8 else 1
    failed += 1 if _boolean_flag(inputs, "csf_gram_stain_positive") else 0
    failed += 1 if _boolean_flag(inputs, "chest_radiograph_infiltrate") else 0
    if _boolean_flag(inputs, "diarrhea") and stool_wbc >= 5:
        failed += 1

    low_risk = failed == 0
    interpretation = (
        "Philadelphia criteria low risk for serious bacterial infection."
        if low_risk
        else "Philadelphia criteria not low risk for serious bacterial infection."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"low_risk": low_risk, "criteria_failed": failed},
        unit="criteria",
        interpretation=interpretation,
    )


def bacterial_meningitis_score_children(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    csf_anc = _number(inputs, "csf_anc_cells_per_uL")
    csf_protein = _number(inputs, "csf_protein_mg_dl")
    peripheral_anc = _number(inputs, "peripheral_anc_cells_per_uL")
    for key, value in (
        ("csf_anc_cells_per_uL", csf_anc),
        ("csf_protein_mg_dl", csf_protein),
        ("peripheral_anc_cells_per_uL", peripheral_anc),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")

    score = (
        _score_true(inputs, "positive_csf_gram_stain", 2)
        + (1 if csf_anc >= 1000 else 0)
        + (1 if csf_protein >= 80 else 0)
        + (1 if peripheral_anc >= 10000 else 0)
        + _score_true(inputs, "seizure_at_or_before_presentation")
    )
    interpretation = (
        "Bacterial Meningitis Score very low risk when no predictors are present."
        if score == 0
        else "Bacterial Meningitis Score not very low risk; one or more predictors are present."
    )
    return result(metadata, score, "criteria", interpretation)


def kobayashi_kawasaki_ivig_resistance_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    sodium = _number(inputs, "sodium_mmol_l")
    ast = _number(inputs, "ast_iu_l")
    illness_days = _number(inputs, "days_of_illness_at_initial_treatment")
    neutrophils = _number(inputs, "neutrophils_percent")
    crp = _number(inputs, "crp_mg_dl")
    age_months = _number(inputs, "age_months")
    platelets = _number(inputs, "platelets_10e3_per_uL")
    for key, value in (
        ("sodium_mmol_l", sodium),
        ("ast_iu_l", ast),
        ("days_of_illness_at_initial_treatment", illness_days),
        ("neutrophils_percent", neutrophils),
        ("crp_mg_dl", crp),
        ("age_months", age_months),
        ("platelets_10e3_per_uL", platelets),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")

    component_points = {
        "sodium_at_or_below_133": 2 if sodium <= 133 else 0,
        "ast_at_or_above_100": 2 if ast >= 100 else 0,
        "illness_day_at_or_before_4": 2 if illness_days <= 4 else 0,
        "neutrophils_at_or_above_80_percent": 2 if neutrophils >= 80 else 0,
        "crp_at_or_above_10_mg_dl": 1 if crp >= 10 else 0,
        "age_at_or_below_12_months": 1 if age_months <= 12 else 0,
        "platelets_at_or_below_300k": 1 if platelets <= 300 else 0,
    }
    score = sum(component_points.values())
    high_risk = score >= 4
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "component_points": component_points, "high_risk": high_risk},
        unit="points",
        interpretation=(
            "high risk of IVIG resistance by Kobayashi score"
            if high_risk
            else "lower risk of IVIG resistance by Kobayashi score"
        ),
    )


def harada_kawasaki_coronary_aneurysm_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    wbc = _number(inputs, "wbc_per_uL")
    platelets = _number(inputs, "platelets_10e3_per_uL")
    crp = _number(inputs, "crp_mg_dl")
    hematocrit = _number(inputs, "hematocrit_percent")
    albumin = _number(inputs, "albumin_g_dl")
    age_months = _number(inputs, "age_months")
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be female or male")
    for key, value in (
        ("wbc_per_uL", wbc),
        ("platelets_10e3_per_uL", platelets),
        ("crp_mg_dl", crp),
        ("hematocrit_percent", hematocrit),
        ("albumin_g_dl", albumin),
        ("age_months", age_months),
    ):
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")

    component_points = {
        "wbc_above_12000": 1 if wbc > 12000 else 0,
        "platelets_below_350k": 1 if platelets < 350 else 0,
        "crp_above_3_mg_dl": 1 if crp > 3 else 0,
        "hematocrit_below_35_percent": 1 if hematocrit < 35 else 0,
        "albumin_below_3_5_g_dl": 1 if albumin < 3.5 else 0,
        "age_at_or_below_12_months": 1 if age_months <= 12 else 0,
        "male": 1 if sex == "male" else 0,
    }
    score = sum(component_points.values())
    high_risk = score >= 4
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "component_points": component_points, "high_risk": high_risk},
        unit="points",
        interpretation=(
            "high risk of coronary artery aneurysm by Harada score"
            if high_risk
            else "lower risk of coronary artery aneurysm by Harada score"
        ),
    )


def who_dengue_warning_signs(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    warning_keys = (
        "abdominal_pain_or_tenderness",
        "persistent_vomiting",
        "clinical_fluid_accumulation",
        "mucosal_bleeding",
        "lethargy_or_restlessness",
        "liver_enlargement_gt_2cm",
        "hematocrit_increase_with_rapid_platelet_decrease",
    )
    present = [key for key in warning_keys if _boolean_flag(inputs, key)]
    has_warning_signs = bool(present)
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"warning_signs_present": has_warning_signs, "warning_sign_count": len(present), "warning_signs": present},
        unit="warning signs",
        interpretation=(
            "Dengue with warning signs by WHO classification."
            if has_warning_signs
            else "Dengue without warning signs by WHO classification."
        ),
    )


def who_rabies_exposure_category(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    category_iii = any(
        _boolean_flag(inputs, key)
        for key in (
            "transdermal_bite_or_scratch",
            "mucous_membrane_saliva_contact",
            "lick_on_broken_skin",
            "bat_exposure",
        )
    )
    category_ii = any(
        _boolean_flag(inputs, key)
        for key in (
            "nibbling_uncovered_skin",
            "minor_scratch_or_abrasion_without_bleeding",
        )
    )
    category_i = any(
        _boolean_flag(inputs, key)
        for key in (
            "touching_or_feeding_animals",
            "licks_on_intact_skin",
        )
    )

    if category_iii:
        category = 3
        exposure = "severe exposure"
        interpretation = "WHO rabies category III exposure; prompt wound care, vaccination, and rabies immunoglobulin are indicated."
    elif category_ii:
        category = 2
        exposure = "exposure"
        interpretation = "WHO rabies category II exposure; prompt wound care and rabies vaccination are indicated."
    elif category_i:
        category = 1
        exposure = "no exposure"
        interpretation = "WHO rabies category I contact; no post-exposure prophylaxis is indicated if history is reliable."
    else:
        category = 0
        exposure = "no recognized exposure"
        interpretation = "No WHO rabies exposure category criterion is present from the supplied inputs."

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"category": category, "exposure": exposure},
        unit="category",
        interpretation=interpretation,
    )


def cdc_severe_malaria_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    parasitemia = _number(inputs, "parasitemia_percent")
    hemoglobin = _number(inputs, "hemoglobin_g_dl")
    if parasitemia < 0:
        raise ValueError("parasitemia_percent must be nonnegative")
    if hemoglobin < 0:
        raise ValueError("hemoglobin_g_dl must be nonnegative")

    criteria_met: list[str] = []
    if parasitemia >= 5:
        criteria_met.append("high_parasitemia")
    if hemoglobin < 7:
        criteria_met.append("severe_anemia")

    for key in (
        "impaired_consciousness",
        "seizures",
        "shock",
        "pulmonary_edema_or_ards",
        "acidosis",
        "acute_kidney_injury",
        "abnormal_bleeding_or_dic",
    ):
        if _boolean_flag(inputs, key):
            criteria_met.append(key)

    jaundice = _boolean_flag(inputs, "jaundice")
    if jaundice and criteria_met:
        criteria_met.append("jaundice_with_other_severe_malaria_sign")

    severe = bool(criteria_met)
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"severe_malaria": severe, "criteria_met": criteria_met},
        unit="criteria",
        interpretation=(
            "CDC severe malaria criteria met."
            if severe
            else "CDC severe malaria criteria not met from supplied inputs."
        ),
    )
