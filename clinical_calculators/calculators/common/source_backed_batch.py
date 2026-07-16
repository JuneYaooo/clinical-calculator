"""Source-backed implementations promoted from the pending calculator inventory."""

from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import boolean, number
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def four_point_clock_drawing_test(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Four-point clock drawing screen represented in CALC-0285 metadata."""
    criteria = {
        "closed_circle": boolean(inputs, "closed_circle"),
        "numbers_in_correct_positions": boolean(inputs, "numbers_in_correct_positions"),
        "all_twelve_numbers_present": boolean(inputs, "all_twelve_numbers_present"),
        "hands_show_requested_time": boolean(inputs, "hands_show_requested_time"),
    }
    score = sum(criteria.values())
    classification = "normal screen" if score == 4 else "abnormal screen"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "classification": classification, "criteria": criteria},
        unit="points",
        interpretation=(
            f"Four-point clock drawing screen: {score}/4 ({classification}). "
            "An abnormal screen is not a diagnosis and requires contextual cognitive assessment."
        ),
    )


def dutch_lipid_clinic_network_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """DLCN adult FH criteria from EAS consensus Table 1 (2013).

    Source: https://europepmc.org/articles/PMC3844152
    Only the highest applicable score within each criteria group is counted.
    """
    family_points = 0
    if boolean(inputs, "family_premature_chd_or_ldl_above_95th"):
        family_points = max(family_points, 1)
    if boolean(inputs, "family_xanthoma_arcus_or_child_ldl_above_95th"):
        family_points = max(family_points, 2)

    clinical_points = 0
    if boolean(inputs, "personal_premature_chd"):
        clinical_points = max(clinical_points, 2)
    if boolean(inputs, "personal_premature_cerebral_or_peripheral_vascular_disease"):
        clinical_points = max(clinical_points, 1)

    physical_points = 0
    if boolean(inputs, "tendon_xanthoma"):
        physical_points = max(physical_points, 6)
    if boolean(inputs, "corneal_arcus_under_45"):
        physical_points = max(physical_points, 4)

    ldl_mg_dl = number(inputs, "ldl_mg_dl")
    if ldl_mg_dl < 0:
        raise ValueError("ldl_mg_dl must be nonnegative")
    if ldl_mg_dl > 325:
        ldl_points = 8
    elif ldl_mg_dl >= 251:
        ldl_points = 5
    elif ldl_mg_dl >= 191:
        ldl_points = 3
    elif ldl_mg_dl >= 155:
        ldl_points = 1
    else:
        ldl_points = 0

    genetic_points = 8 if boolean(inputs, "causative_ldlr_apob_pcsk9_mutation") else 0
    total = family_points + clinical_points + physical_points + ldl_points + genetic_points

    if total > 8:
        classification = "definite familial hypercholesterolemia"
    elif total >= 6:
        classification = "probable familial hypercholesterolemia"
    elif total >= 3:
        classification = "possible familial hypercholesterolemia"
    else:
        classification = "unlikely familial hypercholesterolemia"

    components = {
        "family_history": family_points,
        "clinical_history": clinical_points,
        "physical_examination": physical_points,
        "ldl_cholesterol": ldl_points,
        "genetic_testing": genetic_points,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": total, "classification": classification, "components": components},
        unit="points",
        interpretation=(
            f"DLCN score {total}: {classification}. Apply to adults after considering secondary "
            "causes of elevated LDL cholesterol; this classification does not replace specialist evaluation."
        ),
    )


def guys_stone_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    """Guy's Stone Score from the published four-grade table.

    Source table: https://europepmc.org/articles/PMC12004994
    """
    stone_count = str(inputs["stone_count"]).strip().lower()
    location = str(inputs["location"]).strip().lower()
    anatomy = str(inputs["anatomy"]).strip().lower()
    staghorn = str(inputs["staghorn"]).strip().lower()

    if stone_count not in {"solitary", "multiple"}:
        raise ValueError("stone_count must be 'solitary' or 'multiple'")
    if location not in {"mid_lower", "pelvis", "upper", "calyceal_diverticulum", "other"}:
        raise ValueError(
            "location must be 'mid_lower', 'pelvis', 'upper', 'calyceal_diverticulum', or 'other'"
        )
    if anatomy not in {"simple", "abnormal", "spina_bifida_or_spinal_injury"}:
        raise ValueError("anatomy must be 'simple', 'abnormal', or 'spina_bifida_or_spinal_injury'")
    if staghorn not in {"none", "partial", "complete"}:
        raise ValueError("staghorn must be 'none', 'partial', or 'complete'")

    if anatomy == "spina_bifida_or_spinal_injury" or staghorn == "complete":
        grade = 4
    elif staghorn == "partial" or location == "calyceal_diverticulum":
        grade = 3
    elif stone_count == "multiple" and anatomy == "abnormal":
        grade = 3
    elif (
        (stone_count == "solitary" and location == "upper" and anatomy == "simple")
        or (stone_count == "multiple" and anatomy == "simple")
        or (stone_count == "solitary" and anatomy == "abnormal")
    ):
        grade = 2
    elif stone_count == "solitary" and location in {"mid_lower", "pelvis"} and anatomy == "simple":
        grade = 1
    else:
        raise ValueError("the supplied stone/anatomy combination is not represented in the source table")

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="classification completed",
        value={"grade": grade},
        unit="grade",
        interpretation=(
            f"Guy's Stone Score grade {grade}; higher grades represent more complex PCNL anatomy. "
            "The score supports procedural planning and does not itself select treatment."
        ),
    )


def hendrich_ii_fall_risk_model(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Hendrich II inpatient fall-risk model with the standard >=5 threshold.

    Open validation and item table: https://europepmc.org/articles/PMC11895638
    """
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    get_up_and_go = str(inputs["get_up_and_go"]).strip().lower()
    gait_points = {
        "single_movement": 0,
        "pushes_up_one_attempt": 1,
        "multiple_attempts": 3,
        "unable_without_assistance": 4,
    }
    if get_up_and_go not in gait_points:
        raise ValueError(f"get_up_and_go must be one of: {', '.join(gait_points)}")

    components = {
        "confusion_disorientation_impulsivity": (
            4 if boolean(inputs, "confusion_disorientation_impulsivity") else 0
        ),
        "symptomatic_depression": 2 if boolean(inputs, "symptomatic_depression") else 0,
        "altered_elimination": 1 if boolean(inputs, "altered_elimination") else 0,
        "dizziness_or_vertigo": 1 if boolean(inputs, "dizziness_or_vertigo") else 0,
        "male_sex": 1 if sex == "male" else 0,
        "antiepileptics": 2 if boolean(inputs, "antiepileptics") else 0,
        "benzodiazepines": 1 if boolean(inputs, "benzodiazepines") else 0,
        "get_up_and_go": gait_points[get_up_and_go],
    }
    total = sum(components.values())
    high_risk = total >= 5
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": total, "high_fall_risk": high_risk, "components": components},
        unit="points",
        interpretation=(
            f"Hendrich II score {total}: {'high' if high_risk else 'not high'} inpatient fall risk "
            "by the standard >=5 threshold. Local validation and fall-prevention policy should govern action."
        ),
    )


def chokai_ureteral_stone_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """CHOKAI ureteral-stone score from the published 0-13 point table.

    Open item table and 2026 prospective validation:
    https://europepmc.org/articles/PMC12818773
    The validation cohort's optimal cutoff was >=8; it is not a universal imaging rule.
    """
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    age_years = number(inputs, "age_years")
    if not 18 <= age_years <= 130:
        raise ValueError("age_years must be between 18 and 130")

    components = {
        "nausea_or_vomiting": 1 if boolean(inputs, "has_nausea_or_vomiting") else 0,
        "hydronephrosis": 4 if boolean(inputs, "has_hydronephrosis") else 0,
        "occult_blood_in_urine": 3 if boolean(inputs, "has_occult_blood_in_urine") else 0,
        "kidney_stone_history": 1 if boolean(inputs, "history_kidney_stone") else 0,
        "male_sex": 1 if sex == "male" else 0,
        "age_under_60": 1 if age_years < 60 else 0,
        "pain_reduced_within_6_hours": (
            2 if boolean(inputs, "has_pain_reduction_within_6h") else 0
        ),
    }
    total = sum(components.values())
    meets_validation_cutoff = total >= 8
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": total,
            "meets_2026_validation_cutoff": meets_validation_cutoff,
            "components": components,
        },
        unit="points",
        interpretation=(
            f"CHOKAI score {total}/13. In one 2026 prospective validation cohort, >=8 was the "
            "optimal threshold (88% sensitivity, 80% specificity). This score does not exclude "
            "alternative causes of flank pain or independently determine imaging."
        ),
    )


def _restricted_cubic_spline_basis(value: float, knots: tuple[float, ...]) -> tuple[float, ...]:
    """Return rms-compatible restricted cubic spline nonlinear basis terms."""
    first, penultimate, last = knots[0], knots[-2], knots[-1]
    scale = (last - first) ** 2
    terms = []
    for knot in knots[:-2]:
        term = (
            max(value - knot, 0) ** 3
            - max(value - penultimate, 0) ** 3 * (last - knot) / (last - penultimate)
            + max(value - last, 0) ** 3 * (penultimate - knot) / (last - penultimate)
        ) / scale
        terms.append(term)
    return tuple(terms)


def _four_c_continuous_term(
    value: float,
    coefficients: tuple[float, float, float],
    knots: tuple[float, float, float, float],
) -> float:
    spline_1, spline_2 = _restricted_cubic_spline_basis(value, knots)
    linear, coefficient_1, coefficient_2 = coefficients
    return linear * value + coefficient_1 * spline_1 + coefficient_2 * spline_2


def isaric_4c_deterioration_probability(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Original ISARIC 4C in-hospital deterioration logistic model.

    Model coefficients and restricted cubic spline knots are from supplementary Table 3:
    https://europepmc.org/articles/PMC7832571
    """
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")

    values = {
        "age": number(inputs, "age_years"),
        "respiratory_rate": number(inputs, "respiratory_rate_breaths_min"),
        "oxygen_saturation": number(inputs, "oxygen_saturation_percent"),
        "urea": number(inputs, "urea_mmol_l"),
        "crp": number(inputs, "crp_mg_l"),
        "lymphocytes": number(inputs, "lymphocytes_10e9_l"),
    }
    observed_ranges = {
        "age": (18, 110),
        "respiratory_rate": (0, 150),
        "oxygen_saturation": (50, 100),
        "urea": (0, 100),
        "crp": (0, 750),
        "lymphocytes": (0, 40),
    }
    for name, value in values.items():
        lower, upper = observed_ranges[name]
        if not lower <= value <= upper:
            raise ValueError(
                f"{name} must be within the official calculator's observed range {lower}-{upper}"
            )

    linear_predictor = 4.033
    linear_predictor += 0.2690 if sex == "male" else 0
    linear_predictor += 0.2439 if boolean(inputs, "nosocomial") else 0
    linear_predictor += 0.3252 if boolean(inputs, "has_radiographic_infiltrates") else 0
    linear_predictor += 0.7450 if boolean(inputs, "on_oxygen_therapy") else 0
    linear_predictor += 0.6028 if boolean(inputs, "has_gcs_below_15") else 0
    linear_predictor += _four_c_continuous_term(
        values["age"], (0.0159, -0.0129, 0.1265), (38.5, 67.7, 81.1, 92.9)
    )
    linear_predictor += _four_c_continuous_term(
        values["respiratory_rate"], (-0.0145, 0.5992, -1.078), (16, 19, 24, 37)
    )
    linear_predictor += _four_c_continuous_term(
        values["oxygen_saturation"], (-0.0707, -0.0248, 1.024), (84, 94, 96, 100)
    )
    linear_predictor += _four_c_continuous_term(
        values["urea"], (0.0508, 0.4446, -1.035), (2.9, 5.7, 9.2, 25.5)
    )
    linear_predictor += _four_c_continuous_term(
        values["crp"], (0.0097, -0.0395, 0.0588), (5, 45, 113, 297)
    )
    linear_predictor += _four_c_continuous_term(
        values["lymphocytes"], (-0.4564, 0.7309, -0.8113), (0.3, 0.7, 1.1, 2.4)
    )
    probability = 1 / (1 + math.exp(-linear_predictor))
    risk_percent = round(probability * 100, 4)
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "risk_percent": risk_percent,
            "probability": round(probability, 6),
            "linear_predictor": round(linear_predictor, 6),
        },
        unit="%",
        interpretation=(
            f"Estimated in-hospital clinical deterioration risk: {risk_percent}%. The original "
            "outcome was ventilatory support, critical-care admission, or death among adults "
            "hospitalised with COVID-19. Validate calibration before use outside the source setting."
        ),
    )


def kidney_failure_risk_equation_4_variable(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Four-variable KFRE with 2016 North American/non-North American calibration.

    The coefficients and baseline survivals are published by the equation authors' calculator:
    https://kidneyfailurerisk.com/assets/js/kidney-app.js
    The site cites Tangri et al., JAMA 2016, doi:10.1001/jama.2015.18202.
    """
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    age_years = number(inputs, "age_years")
    egfr = number(inputs, "egfr_ml_min_1_73m2")
    acr_mg_g = number(inputs, "urine_acr_mg_g")
    if not 18 <= age_years <= 110:
        raise ValueError("age_years must be between 18 and 110")
    if not 0 < egfr < 60:
        raise ValueError("egfr_ml_min_1_73m2 must be greater than 0 and below 60 for validated use")
    if acr_mg_g <= 0:
        raise ValueError("urine_acr_mg_g must be greater than 0 because the equation uses log(ACR)")

    male = 1 if sex == "male" else 0
    linear_predictor = (
        -0.2201 * (age_years / 10 - 7.036)
        + 0.2467 * (male - 0.5642)
        - 0.5567 * (egfr / 5 - 7.222)
        + 0.451 * (math.log(acr_mg_g) - 5.137)
    )
    north_america = boolean(inputs, "north_america")
    baseline_2_year = 0.975 if north_america else 0.9832
    baseline_5_year = 0.924 if north_america else 0.9365
    relative_risk = math.exp(linear_predictor)
    risk_2_year = 1 - baseline_2_year**relative_risk
    risk_5_year = 1 - baseline_5_year**relative_risk
    risk_2_percent = round(risk_2_year * 100, 4)
    risk_5_percent = round(risk_5_year * 100, 4)
    region = "North American" if north_america else "non-North American"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "risk_2_year_percent": risk_2_percent,
            "risk_5_year_percent": risk_5_percent,
            "linear_predictor": round(linear_predictor, 6),
            "calibration": region,
        },
        unit="%",
        interpretation=(
            f"Four-variable KFRE ({region} calibration): {risk_2_percent}% at 2 years and "
            f"{risk_5_percent}% at 5 years. It predicts treated kidney failure in CKD G3-G5 "
            "and should be interpreted with local referral and treatment-planning guidance."
        ),
    )


def eortc_2006_nmibc_risk_table(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """EORTC 2006 Ta/T1 NMIBC recurrence and progression risk tables.

    Sources:
    - EORTC calculator: https://www.eortc.be/tools/bladdercalculator/
    - EAU guideline model context: https://uroweb.org/guidelines/non-muscle-invasive-bladder-cancer/chapter/predicting-disease-recurrence-and-progression
    - Original study: PMID 16442208, doi:10.1016/j.eururo.2005.12.031
    """
    tumor_count = str(inputs["tumor_count_category"]).strip().lower()
    tumor_size = str(inputs["tumor_size_category"]).strip().lower()
    prior_recurrence = str(inputs["prior_recurrence_rate"]).strip().lower()
    t_category = str(inputs["t_category"]).strip().lower()
    grade = str(inputs["who_1973_grade"]).strip().lower()

    tumor_count_points = {
        "single": (0, 0),
        "two_to_seven": (3, 3),
        "eight_or_more": (6, 3),
    }
    tumor_size_points = {"under_3_cm": (0, 0), "at_least_3_cm": (3, 3)}
    prior_recurrence_points = {
        "primary": (0, 0),
        "at_most_one_per_year": (2, 2),
        "more_than_one_per_year": (4, 2),
    }
    t_category_points = {"ta": (0, 0), "t1": (1, 4)}
    grade_points = {"g1": (0, 0), "g2": (1, 0), "g3": (2, 5)}
    for value, mapping, name in (
        (tumor_count, tumor_count_points, "tumor_count_category"),
        (tumor_size, tumor_size_points, "tumor_size_category"),
        (prior_recurrence, prior_recurrence_points, "prior_recurrence_rate"),
        (t_category, t_category_points, "t_category"),
        (grade, grade_points, "who_1973_grade"),
    ):
        if value not in mapping:
            raise ValueError(f"{name} must be one of: {', '.join(mapping)}")

    cis_points = (1, 6) if boolean(inputs, "concomitant_cis") else (0, 0)
    pairs = (
        tumor_count_points[tumor_count],
        tumor_size_points[tumor_size],
        prior_recurrence_points[prior_recurrence],
        t_category_points[t_category],
        cis_points,
        grade_points[grade],
    )
    recurrence_score = sum(pair[0] for pair in pairs)
    progression_score = sum(pair[1] for pair in pairs)

    if recurrence_score == 0:
        recurrence_risk = (15.0, 31.0)
    elif recurrence_score <= 4:
        recurrence_risk = (24.0, 46.0)
    elif recurrence_score <= 9:
        recurrence_risk = (38.0, 62.0)
    else:
        recurrence_risk = (61.0, 78.0)

    if progression_score == 0:
        progression_risk = (0.2, 0.8)
    elif progression_score <= 6:
        progression_risk = (1.0, 6.0)
    elif progression_score <= 13:
        progression_risk = (5.0, 17.0)
    else:
        progression_risk = (17.0, 45.0)

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "recurrence_score": recurrence_score,
            "progression_score": progression_score,
            "recurrence_risk_1_year_percent": recurrence_risk[0],
            "recurrence_risk_5_year_percent": recurrence_risk[1],
            "progression_risk_1_year_percent": progression_risk[0],
            "progression_risk_5_year_percent": progression_risk[1],
        },
        unit="%",
        interpretation=(
            f"EORTC 2006 recurrence score {recurrence_score}/17: {recurrence_risk[0]}% at "
            f"1 year and {recurrence_risk[1]}% at 5 years. Progression score "
            f"{progression_score}/23: {progression_risk[0]}% at 1 year and "
            f"{progression_risk[1]}% at 5 years. The source cohort largely predates current "
            "BCG practice and may overestimate contemporary risk."
        ),
    )


def revised_risk_analysis_index_clinical(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Prospective clinical revised Risk Analysis Index (RAI-C-rev), 0-81.

    Complete scoring table: Arya et al., Ann Surg 2020, Table 3.
    https://europepmc.org/articles/PMC8785437
    """
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    age_years = number(inputs, "age_years")
    if not 0 <= age_years <= 130:
        raise ValueError("age_years must be between 0 and 130")

    adl_values = []
    for name in (
        "mobility_adl_0_to_4",
        "eating_adl_0_to_4",
        "toileting_adl_0_to_4",
        "hygiene_adl_0_to_4",
    ):
        value = number(inputs, name)
        if not value.is_integer() or not 0 <= value <= 4:
            raise ValueError(f"{name} must be an integer from 0 to 4")
        adl_values.append(int(value))
    adl_total = sum(adl_values)

    age_without_cancer = (0, 1, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34)
    age_with_cancer = (28, 29, 29, 30, 30, 31, 31, 32, 32, 33, 34, 34, 35, 35, 36, 36, 37, 37)
    age_index = 0 if age_years <= 19 else min(int((age_years - 20) // 5) + 1, 17)
    has_cancer = boolean(inputs, "has_disseminated_cancer")
    age_cancer_points = (
        age_with_cancer[age_index] if has_cancer else age_without_cancer[age_index]
    )

    adl_without_cognitive_decline = (0, 1, 2, 3, 4, 4, 5, 6, 7, 8, 9, 10, 11, 11, 12, 13, 14)
    adl_with_cognitive_decline = (5, 6, 6, 7, 8, 8, 9, 10, 11, 11, 12, 13, 13, 14, 15, 15, 16)
    cognitive_decline = boolean(inputs, "has_cognitive_decline")
    adl_cognitive_points = (
        adl_with_cognitive_decline[adl_total]
        if cognitive_decline
        else adl_without_cognitive_decline[adl_total]
    )

    components = {
        "male_sex": 3 if sex == "male" else 0,
        "age_and_disseminated_cancer": age_cancer_points,
        "unintentional_weight_loss": (
            4 if boolean(inputs, "has_unintentional_weight_loss") else 0
        ),
        "poor_appetite": 4 if boolean(inputs, "has_poor_appetite") else 0,
        "renal_failure": 8 if boolean(inputs, "has_renal_failure") else 0,
        "chronic_or_congestive_heart_failure": (
            5 if boolean(inputs, "has_chronic_or_congestive_heart_failure") else 0
        ),
        "shortness_of_breath": 3 if boolean(inputs, "has_shortness_of_breath") else 0,
        "residence_outside_independent_living": (
            1 if boolean(inputs, "has_non_independent_residence") else 0
        ),
        "adl_and_cognitive_decline": adl_cognitive_points,
    }
    total = sum(components.values())
    if total >= 45:
        frailty_band = "very high frailty signal"
    elif total >= 37:
        frailty_band = "high frailty signal"
    elif total >= 30:
        frailty_band = "potential frailty signal"
    else:
        frailty_band = "below commonly studied screening thresholds"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": total,
            "frailty_band": frailty_band,
            "adl_total": adl_total,
            "components": components,
        },
        unit="points",
        interpretation=(
            f"RAI-C-rev {total}/81: {frailty_band}. Published screening thresholds vary by "
            "resource setting; the score identifies patients who may need further geriatric "
            "assessment and does not itself determine operative eligibility."
        ),
    )


def plcom2012_six_year_lung_cancer_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """PLCOm2012 six-year lung-cancer risk for current and former smokers.

    All coefficients, centering values, and the smoking-intensity transformation are from
    Tammemägi et al., NEJM 2013, Table 2: https://europepmc.org/articles/PMC3929969
    """
    age_years = number(inputs, "age_years")
    education = number(inputs, "education_level_1_to_6")
    bmi = number(inputs, "bmi")
    cigarettes_per_day = number(inputs, "smoking_intensity_cigarettes_day")
    smoking_duration = number(inputs, "smoking_duration_years")
    quit_time = number(inputs, "quit_time_years")
    if not 55 <= age_years <= 74:
        raise ValueError("age_years must be 55-74, the source study enrollment range")
    if not education.is_integer() or not 1 <= education <= 6:
        raise ValueError("education_level_1_to_6 must be an integer from 1 to 6")
    if not 10 <= bmi <= 80:
        raise ValueError("bmi must be between 10 and 80 kg/m^2")
    if not 0 < cigarettes_per_day <= 200:
        raise ValueError("smoking_intensity_cigarettes_day must be greater than 0 and at most 200")
    if not 0 < smoking_duration <= age_years:
        raise ValueError("smoking_duration_years must be greater than 0 and no greater than age")
    if not 0 <= quit_time <= age_years:
        raise ValueError("quit_time_years must be between 0 and age")
    current_smoker = boolean(inputs, "current_smoker")
    if current_smoker and quit_time != 0:
        raise ValueError("quit_time_years must be 0 for a current smoker")

    race = str(inputs["race_ethnicity_plco"]).strip().lower()
    race_coefficients = {
        "white": 0.0,
        "black": 0.3944778,
        "hispanic": -0.7434744,
        "asian": -0.466585,
        "american_indian_or_alaska_native": 0.0,
        "native_hawaiian_or_pacific_islander": 1.027152,
    }
    if race not in race_coefficients:
        raise ValueError(f"race_ethnicity_plco must be one of: {', '.join(race_coefficients)}")

    linear_predictor = -4.532506
    linear_predictor += 0.0778868 * (age_years - 62)
    linear_predictor += race_coefficients[race]
    linear_predictor += -0.0812744 * (education - 4)
    linear_predictor += -0.0274194 * (bmi - 27)
    linear_predictor += 0.3553063 if boolean(inputs, "has_copd") else 0
    linear_predictor += 0.4589971 if boolean(inputs, "history_personal_cancer") else 0
    linear_predictor += 0.587185 if boolean(inputs, "history_family_lung_cancer") else 0
    linear_predictor += 0.2597431 if current_smoker else 0
    linear_predictor += -1.822606 * ((cigarettes_per_day / 10) ** -1 - 0.4021541613)
    linear_predictor += 0.0317321 * (smoking_duration - 27)
    linear_predictor += -0.0308572 * (quit_time - 10)
    probability = 1 / (1 + math.exp(-linear_predictor))
    risk_percent = round(probability * 100, 4)
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "risk_6_year_percent": risk_percent,
            "probability": round(probability, 6),
            "linear_predictor": round(linear_predictor, 6),
        },
        unit="%",
        interpretation=(
            f"PLCOm2012 estimated six-year lung-cancer risk: {risk_percent}%. The model was "
            "developed for current or former smokers aged 55-74. Screening eligibility must "
            "follow the applicable current guideline rather than a historical study cutoff."
        ),
    )


def ohts_egps_five_year_poag_point_system(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Simplified OHTS-EGPS five-year POAG risk point system.

    The published point table and risk bands are in Table 6 of Gordon et al.,
    Ophthalmology 2007: https://pmc.ncbi.nlm.nih.gov/articles/PMC1995665/
    Measurement protocol and source-population ranges are also documented by OHTS:
    https://ohts.wustl.edu/risk/
    """
    age_years = number(inputs, "age_years")
    mean_iop_mm_hg = number(inputs, "mean_iop_mm_hg")
    mean_cct_micrometers = number(inputs, "mean_cct_micrometers")
    mean_vertical_cup_disc_ratio = number(inputs, "mean_vertical_cup_disc_ratio")
    mean_pattern_standard_deviation_db = number(
        inputs, "mean_pattern_standard_deviation_db"
    )

    if not 30 <= age_years <= 80:
        raise ValueError("age_years must be 30-80, the OHTS/EGPS source-population range")
    if not 20 <= mean_iop_mm_hg <= 32:
        raise ValueError("mean_iop_mm_hg must be 20-32, the untreated source-population range")
    if not 475 <= mean_cct_micrometers <= 650:
        raise ValueError(
            "mean_cct_micrometers must be 475-650, the source-population range"
        )
    if not 0 <= mean_vertical_cup_disc_ratio <= 1:
        raise ValueError("mean_vertical_cup_disc_ratio must be between 0 and 1")
    if mean_pattern_standard_deviation_db < 0:
        raise ValueError("mean_pattern_standard_deviation_db must be nonnegative")

    if age_years < 45:
        age_points = 0
    elif age_years < 55:
        age_points = 1
    elif age_years < 65:
        age_points = 2
    elif age_years < 75:
        age_points = 3
    else:
        age_points = 4

    if mean_iop_mm_hg < 22:
        iop_points = 0
    elif mean_iop_mm_hg < 24:
        iop_points = 1
    elif mean_iop_mm_hg < 26:
        iop_points = 2
    elif mean_iop_mm_hg < 28:
        iop_points = 3
    else:
        iop_points = 4

    if mean_cct_micrometers >= 600:
        cct_points = 0
    elif mean_cct_micrometers >= 576:
        cct_points = 1
    elif mean_cct_micrometers >= 551:
        cct_points = 2
    elif mean_cct_micrometers >= 526:
        cct_points = 3
    else:
        cct_points = 4

    if mean_vertical_cup_disc_ratio < 0.3:
        cup_disc_points = 0
    elif mean_vertical_cup_disc_ratio < 0.4:
        cup_disc_points = 1
    elif mean_vertical_cup_disc_ratio < 0.5:
        cup_disc_points = 2
    elif mean_vertical_cup_disc_ratio < 0.6:
        cup_disc_points = 3
    else:
        cup_disc_points = 4

    if mean_pattern_standard_deviation_db < 1.8:
        psd_points = 0
    elif mean_pattern_standard_deviation_db < 2.0:
        psd_points = 1
    elif mean_pattern_standard_deviation_db < 2.4:
        psd_points = 2
    elif mean_pattern_standard_deviation_db < 2.8:
        psd_points = 3
    else:
        psd_points = 4

    components = {
        "age": age_points,
        "mean_untreated_iop": iop_points,
        "mean_central_corneal_thickness": cct_points,
        "mean_vertical_cup_disc_ratio": cup_disc_points,
        "mean_pattern_standard_deviation": psd_points,
    }
    total = sum(components.values())
    if total <= 6:
        risk_band = "at_most_4_percent"
        risk_display = "≤4%"
    elif total <= 8:
        risk_band = "10_percent"
        risk_display = "10%"
    elif total <= 10:
        risk_band = "15_percent"
        risk_display = "15%"
    elif total <= 12:
        risk_band = "20_percent"
        risk_display = "20%"
    else:
        risk_band = "at_least_33_percent"
        risk_display = "≥33%"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": total,
            "risk_5_year_band": risk_band,
            "risk_5_year_display": risk_display,
            "components": components,
            "method": "OHTS-EGPS simplified point system",
        },
        unit="%",
        interpretation=(
            f"OHTS-EGPS simplified score {total}/20: estimated five-year POAG risk "
            f"{risk_display}. This is the published point-system risk band, not the continuous "
            "equation. It applies to ocular-hypertension patients measured using the source "
            "protocol and does not predict progression of established glaucoma."
        ),
    )


def thoracoscore_in_hospital_mortality(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Original Thoracoscore in-hospital mortality logistic model.

    The SFAR calculator publishes every category coefficient, the -7.3737 intercept,
    and the logistic transformation:
    https://sfar.org/scores2/thoracoscore2.php
    Original model: Falcoz et al., J Thorac Cardiovasc Surg 2007,
    doi:10.1016/j.jtcvs.2006.09.020.
    """
    age_years = number(inputs, "age_years")
    asa_class = number(inputs, "asa_class")
    performance_status = number(inputs, "ecog_performance_status")
    dyspnea_grade = number(inputs, "mrc_dyspnea_grade")
    comorbidity_count = number(inputs, "comorbidity_count")
    sex = str(inputs["sex"]).strip().lower()

    if not 18 <= age_years <= 120:
        raise ValueError("age_years must be between 18 and 120")
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    for value, key, minimum, maximum in (
        (asa_class, "asa_class", 1, 5),
        (performance_status, "ecog_performance_status", 0, 4),
        (dyspnea_grade, "mrc_dyspnea_grade", 0, 5),
        (comorbidity_count, "comorbidity_count", 0, 100),
    ):
        if not value.is_integer() or not minimum <= value <= maximum:
            raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    if age_years < 55:
        age_coefficient = 0.0
    elif age_years <= 65:
        age_coefficient = 0.7679
    else:
        age_coefficient = 1.0073

    components = {
        "age": age_coefficient,
        "male_sex": 0.4505 if sex == "male" else 0.0,
        "asa_class_at_least_3": 0.6057 if asa_class >= 3 else 0.0,
        "performance_status_at_least_3": 0.689 if performance_status >= 3 else 0.0,
        "dyspnea_grade_at_least_3": 0.9075 if dyspnea_grade >= 3 else 0.0,
        "urgent_or_emergency_surgery": (
            0.8443 if boolean(inputs, "urgent_or_emergency_surgery") else 0.0
        ),
        "pneumonectomy": 1.2176 if boolean(inputs, "pneumonectomy") else 0.0,
        "malignant_diagnosis": (
            1.2423 if boolean(inputs, "malignant_diagnosis") else 0.0
        ),
        "comorbidity_count": (
            0.0 if comorbidity_count == 0 else 0.7447 if comorbidity_count <= 2 else 0.9065
        ),
    }
    linear_predictor = -7.3737 + sum(components.values())
    probability = 1 / (1 + math.exp(-linear_predictor))
    risk_percent = round(probability * 100, 4)
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "in_hospital_mortality_percent": risk_percent,
            "probability": round(probability, 6),
            "linear_predictor": round(linear_predictor, 6),
            "components": components,
        },
        unit="%",
        interpretation=(
            f"Original Thoracoscore estimated in-hospital mortality: {risk_percent}%. "
            "External studies have reported population-dependent miscalibration, so this "
            "estimate should support—not replace—local thoracic-surgery assessment."
        ),
    )


def maggic_heart_failure_mortality_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """MAGGIC integer score with published one- and three-year mortality table.

    Primary model: Pocock et al., Eur Heart J 2013, doi:10.1093/eurheartj/ehs337.
    The complete point table is published on the model author's MDCalc page:
    https://www.mdcalc.com/calc/3803/maggic-risk-calculator-heart-failure
    Every score-to-risk row from 0 through 50 was cross-checked against the public
    calculation endpoint on 2026-07-15. Scores 51-57 are reported as greater than
    the score-50 risks, matching the source calculator rather than extrapolating.
    """
    age_years = number(inputs, "age_years")
    ef = number(inputs, "ejection_fraction_percent")
    systolic_bp = number(inputs, "systolic_bp_mm_hg")
    bmi = number(inputs, "bmi")
    creatinine = number(inputs, "serum_creatinine_umol_l")
    nyha_class = number(inputs, "nyha_class")
    sex = str(inputs["sex"]).strip().lower()
    if not 18 <= age_years <= 110:
        raise ValueError("age_years must be between 18 and 110")
    if not 0 <= ef <= 100:
        raise ValueError("ejection_fraction_percent must be between 0 and 100")
    if not 30 <= systolic_bp <= 300:
        raise ValueError("systolic_bp_mm_hg must be between 30 and 300")
    if not 0 < bmi <= 50:
        raise ValueError("bmi must be greater than 0 and at most 50")
    if not 0.884 <= creatinine <= 3536:
        raise ValueError("serum_creatinine_umol_l must be between 0.884 and 3536")
    if not nyha_class.is_integer() or not 1 <= nyha_class <= 4:
        raise ValueError("nyha_class must be an integer from 1 to 4")
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")

    if ef < 20:
        ef_points = 7
    elif ef < 25:
        ef_points = 6
    elif ef < 30:
        ef_points = 5
    elif ef < 35:
        ef_points = 3
    elif ef < 40:
        ef_points = 2
    else:
        ef_points = 0

    age_index = (
        0
        if age_years < 55
        else 1
        if age_years < 60
        else 2
        if age_years < 65
        else 3
        if age_years < 70
        else 4
        if age_years < 75
        else 5
        if age_years < 80
        else 6
    )
    age_points_by_ef = (
        (0, 1, 2, 4, 6, 8, 10)
        if ef < 30
        else (0, 2, 4, 6, 8, 10, 13)
        if ef < 40
        else (0, 3, 5, 7, 9, 12, 15)
    )
    age_points = age_points_by_ef[age_index]

    sbp_index = (
        0
        if systolic_bp < 110
        else 1
        if systolic_bp < 120
        else 2
        if systolic_bp < 130
        else 3
        if systolic_bp < 140
        else 4
        if systolic_bp < 150
        else 5
    )
    sbp_points_by_ef = (
        (5, 4, 3, 2, 1, 0)
        if ef < 30
        else (3, 2, 1, 1, 0, 0)
        if ef < 40
        else (2, 1, 1, 0, 0, 0)
    )
    sbp_points = sbp_points_by_ef[sbp_index]

    bmi_points = 6 if bmi < 15 else 5 if bmi < 20 else 3 if bmi < 25 else 2 if bmi < 30 else 0
    creatinine_points = (
        0
        if creatinine < 90
        else 1
        if creatinine < 110
        else 2
        if creatinine < 130
        else 3
        if creatinine < 150
        else 4
        if creatinine < 170
        else 5
        if creatinine < 210
        else 6
        if creatinine < 250
        else 8
    )
    nyha_points = {1: 0, 2: 2, 3: 6, 4: 8}[int(nyha_class)]
    components = {
        "ejection_fraction": ef_points,
        "age_by_ejection_fraction": age_points,
        "systolic_bp_by_ejection_fraction": sbp_points,
        "bmi": bmi_points,
        "serum_creatinine": creatinine_points,
        "nyha_class": nyha_points,
        "male_sex": 1 if sex == "male" else 0,
        "current_smoker": 1 if boolean(inputs, "current_smoker") else 0,
        "diabetes": 3 if boolean(inputs, "diabetes") else 0,
        "copd": 2 if boolean(inputs, "copd") else 0,
        "heart_failure_diagnosed_at_least_18_months": (
            2 if boolean(inputs, "heart_failure_diagnosed_at_least_18_months") else 0
        ),
        "not_on_beta_blocker": 0 if boolean(inputs, "on_beta_blocker") else 3,
        "not_on_acei_or_arb": 0 if boolean(inputs, "on_acei_or_arb") else 1,
    }
    score = sum(components.values())
    risk_1_year = (
        1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 2.9, 3.2, 3.6,
        3.9, 4.3, 4.8, 5.2, 5.8, 6.3, 7.0, 7.7, 8.4, 9.3,
        10.2, 11.1, 12.2, 13.4, 14.7, 16.0, 17.5, 19.1, 20.9, 22.7,
        24.8, 26.9, 29.2, 31.6, 34.2, 36.9, 39.8, 42.7, 45.8, 49.0,
        52.3, 55.7, 59.1, 62.5, 65.9, 69.2, 72.5, 75.7, 78.7, 81.6, 84.2,
    )
    risk_3_year = (
        3.9, 4.3, 4.8, 5.2, 5.8, 6.3, 7.0, 7.7, 8.4, 9.2,
        10.2, 11.1, 12.2, 13.4, 14.6, 16.0, 17.5, 19.1, 20.9, 22.7,
        24.7, 26.9, 29.2, 31.6, 34.2, 36.9, 39.7, 42.7, 45.8, 49.0,
        52.3, 55.6, 59.0, 62.5, 65.8, 69.2, 72.5, 75.6, 78.7, 81.5,
        84.2, 86.6, 88.9, 90.8, 92.6, 94.1, 95.3, 96.4, 97.3, 98.0, 98.5,
    )
    if score <= 50:
        one_year = risk_1_year[score]
        three_year = risk_3_year[score]
        one_year_display = f"{one_year:g}%"
        three_year_display = f"{three_year:g}%"
        capped = False
    else:
        one_year = risk_1_year[50]
        three_year = risk_3_year[50]
        one_year_display = ">84.2%"
        three_year_display = ">98.5%"
        capped = True
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "score": score,
            "risk_1_year_percent_lower_bound": one_year,
            "risk_3_year_percent_lower_bound": three_year,
            "risk_1_year_display": one_year_display,
            "risk_3_year_display": three_year_display,
            "risk_table_capped_above_50": capped,
            "components": components,
        },
        unit="%",
        interpretation=(
            f"MAGGIC score {score}/57: one-year mortality {one_year_display}; "
            f"three-year mortality {three_year_display}. This population model supports "
            "risk communication and should not determine treatment by itself."
        ),
    )


def fullpiers_48_hour_adverse_maternal_outcome_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Original fullPIERS 48-hour adverse maternal-outcome model.

    The complete published equation is reproduced in Table 1 of Ukah et al.,
    BMC Pregnancy and Childbirth 2020 (doi:10.1186/s12884-020-03332-w):
    https://pmc.ncbi.nlm.nih.gov/articles/PMC7643272/
    An independent external-validation paper reproduces the same equation and
    documents the pre-eclampsia population, 48-hour horizon, worst values before
    an outcome, and the original SpO2=97% missing-value convention:
    https://pmc.ncbi.nlm.nih.gov/articles/PMC5865495/
    Original development study: doi:10.1016/S0140-6736(10)61351-7.
    """
    gestational_age_weeks = number(inputs, "gestational_age_weeks")
    creatinine_umol_l = number(inputs, "serum_creatinine_umol_l")
    platelets_10e9_l = number(inputs, "platelets_10e9_l")
    ast_u_l = number(inputs, "ast_u_l")
    oxygen_saturation_percent = number(inputs, "oxygen_saturation_percent")

    if not 20 <= gestational_age_weeks <= 43:
        raise ValueError(
            "gestational_age_weeks must be 20-43; fullPIERS applies after eligibility "
            "for pre-eclampsia, not as an antepartum screening model"
        )
    if not 0 < creatinine_umol_l <= 2000:
        raise ValueError("serum_creatinine_umol_l must be greater than 0 and at most 2000")
    if not 0 < platelets_10e9_l <= 1500:
        raise ValueError("platelets_10e9_l must be greater than 0 and at most 1500")
    if not 0 <= ast_u_l <= 10000:
        raise ValueError("ast_u_l must be between 0 and 10000")
    if not 50 <= oxygen_saturation_percent <= 100:
        raise ValueError("oxygen_saturation_percent must be between 50 and 100")

    chest_pain_or_dyspnea = boolean(inputs, "has_chest_pain_or_dyspnea")
    components = {
        "intercept": 2.68,
        "gestational_age": -5.41e-2 * gestational_age_weeks,
        "chest_pain_or_dyspnea": 1.23 if chest_pain_or_dyspnea else 0.0,
        "creatinine": -2.71e-2 * creatinine_umol_l,
        "platelets": 2.07e-1 * platelets_10e9_l,
        "platelets_squared": 4.00e-5 * platelets_10e9_l**2,
        "ast": 1.01e-2 * ast_u_l,
        "ast_squared": -3.05e-6 * ast_u_l**2,
        "creatinine_by_platelets": 2.50e-4 * creatinine_umol_l * platelets_10e9_l,
        "platelets_by_ast": -6.99e-5 * platelets_10e9_l * ast_u_l,
        "platelets_by_oxygen_saturation": (
            -2.56e-3 * platelets_10e9_l * oxygen_saturation_percent
        ),
    }
    linear_predictor = sum(components.values())
    probability = 1 / (1 + math.exp(-linear_predictor))
    risk_percent = round(probability * 100, 4)

    if risk_percent < 2.5:
        risk_group = "below_2_5_percent"
    elif risk_percent < 5:
        risk_group = "2_5_to_below_5_percent"
    elif risk_percent < 10:
        risk_group = "5_to_below_10_percent"
    elif risk_percent < 20:
        risk_group = "10_to_below_20_percent"
    elif risk_percent < 30:
        risk_group = "20_to_below_30_percent"
    else:
        risk_group = "at_least_30_percent"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "risk_48_hour_percent": risk_percent,
            "probability": round(probability, 6),
            "linear_predictor": round(linear_predictor, 6),
            "risk_group": risk_group,
            "components": {key: round(value, 8) for key, value in components.items()},
        },
        unit="%",
        interpretation=(
            f"Original fullPIERS estimated risk of a serious adverse maternal outcome "
            f"within 48 hours: {risk_percent}%. It applies to women admitted with confirmed "
            "pre-eclampsia and uses the most abnormal predictor values measured before an "
            "outcome. It is not a pre-eclampsia diagnostic or antenatal screening test and "
            "must not delay escalation, transfer, monitoring, or delivery decisions."
        ),
    )


def hcm_risk_scd_2014_five_year_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """Original adult HCM Risk-SCD five-year model and 2014 ESC bands.

    The public QxMD model page publishes the complete prognostic-index equation,
    input ranges, exclusions, source references, and 2014 ESC risk bands:
    https://qxmd.com/calculate/calculator_303/hcm-risk-scd
    Original model: O'Mahony et al., Eur Heart J 2014,
    doi:10.1093/eurheartj/eht439; PMID 24126876.
    """
    age_years = number(inputs, "age_years")
    maximal_wall_thickness_mm = number(inputs, "maximal_wall_thickness_mm")
    left_atrial_diameter_mm = number(inputs, "left_atrial_diameter_mm")
    maximal_lvot_gradient_mm_hg = number(inputs, "maximal_lvot_gradient_mm_hg")

    for value, key, minimum, maximum in (
        (age_years, "age_years", 16, 80),
        (maximal_wall_thickness_mm, "maximal_wall_thickness_mm", 10, 35),
        (left_atrial_diameter_mm, "left_atrial_diameter_mm", 28, 67),
        (maximal_lvot_gradient_mm_hg, "maximal_lvot_gradient_mm_hg", 2, 154),
    ):
        if not minimum <= value <= maximum:
            raise ValueError(f"{key} must be within the published model range {minimum}-{maximum}")

    family_history_scd = boolean(inputs, "family_history_sudden_cardiac_death")
    nonsustained_vt = boolean(inputs, "nonsustained_ventricular_tachycardia")
    unexplained_syncope = boolean(inputs, "unexplained_syncope")

    components = {
        "maximal_wall_thickness": 0.15939858 * maximal_wall_thickness_mm,
        "maximal_wall_thickness_squared": (
            -0.00294271 * maximal_wall_thickness_mm**2
        ),
        "left_atrial_diameter": 0.0259082 * left_atrial_diameter_mm,
        "maximal_lvot_gradient": 0.00446131 * maximal_lvot_gradient_mm_hg,
        "family_history_sudden_cardiac_death": 0.4583082 if family_history_scd else 0.0,
        "nonsustained_ventricular_tachycardia": 0.82639195 if nonsustained_vt else 0.0,
        "unexplained_syncope": 0.71650361 if unexplained_syncope else 0.0,
        "age": -0.01799934 * age_years,
    }
    prognostic_index = sum(components.values())
    probability = 1 - 0.998 ** math.exp(prognostic_index)
    risk_percent = round(probability * 100, 2)

    if risk_percent >= 6:
        risk_band = "at_least_6_percent"
        esc_2014_icd_text = "ICD should be considered"
    elif risk_percent >= 4:
        risk_band = "4_to_below_6_percent"
        esc_2014_icd_text = "ICD may be considered"
    else:
        risk_band = "below_4_percent"
        esc_2014_icd_text = "ICD generally not indicated by this risk estimate alone"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "risk_5_year_sudden_cardiac_death_percent": risk_percent,
            "probability": round(probability, 6),
            "prognostic_index": round(prognostic_index, 8),
            "risk_band": risk_band,
            "esc_2014_icd_text": esc_2014_icd_text,
            "components": {key: round(value, 8) for key, value in components.items()},
            "version": "original model / 2014 ESC bands",
        },
        unit="%",
        interpretation=(
            f"Original HCM Risk-SCD estimated five-year sudden-cardiac-death risk: "
            f"{risk_percent}% ({esc_2014_icd_text}, using the 2014 ESC bands). Do not use "
            "for patients under 16, elite/competitive athletes, phenocopies or syndromic HCM, "
            "prior aborted SCD or sustained ventricular arrhythmia, or without caution after "
            "septal reduction therapy. Current ICD decisions require the applicable current "
            "guideline, clinical modifiers, shared decision-making, and specialist review."
        ),
    )


def garfield_af_integrated_risk_2017(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    """GARFIELD-AF mortality, stroke/SE, and major-bleeding scenario model.

    The public QxMD calculator publishes the full 16-input implementation,
    coefficients, baseline survival values, and 6/12/24-month treatment scenarios:
    https://qxmd.com/calculate/calculator_685/garfield-af-risk-calculator
    Development and external validation: Fox et al., BMJ Open 2017,
    doi:10.1136/bmjopen-2017-017157; PMID 29273652; PMC5778339.
    """
    age_years = number(inputs, "age_years")
    weight_kg = number(inputs, "weight_kg")
    pulse_bpm = number(inputs, "pulse_bpm")
    diastolic_bp_mm_hg = number(inputs, "diastolic_bp_mm_hg")
    if not 18 <= age_years <= 110:
        raise ValueError("age_years must be between 18 and 110; the model was derived in adults")
    if not 20 <= weight_kg <= 350:
        raise ValueError("weight_kg must be between 20 and 350")
    if not 20 <= pulse_bpm <= 250:
        raise ValueError("pulse_bpm must be between 20 and 250")
    if not 20 <= diastolic_bp_mm_hg <= 180:
        raise ValueError("diastolic_bp_mm_hg must be between 20 and 180")

    race = str(inputs["race_ethnicity_garfield"]).strip().lower()
    if race not in {"hispanic_latino", "asian", "black_mixed_other", "caucasian"}:
        raise ValueError(
            "race_ethnicity_garfield must be one of: hispanic_latino, asian, "
            "black_mixed_other, caucasian"
        )
    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")

    history_bleeding = boolean(inputs, "history_bleeding")
    heart_failure = boolean(inputs, "history_heart_failure_or_lvef_below_40")
    history_stroke = boolean(inputs, "history_stroke")
    moderate_severe_ckd = boolean(inputs, "moderate_severe_ckd")
    vascular_disease = boolean(inputs, "history_coronary_or_peripheral_vascular_disease")
    diabetes = boolean(inputs, "diabetes")
    current_smoker = boolean(inputs, "current_smoker")
    dementia = boolean(inputs, "dementia")
    antiplatelet = boolean(inputs, "current_antiplatelet_drug")
    carotid_disease = boolean(inputs, "carotid_occlusive_disease")

    mortality_lp = (
        -0.306202287 * (sex == "female")
        + 0.693789082 * heart_failure
        + 0.306120964 * vascular_disease
        + 0.26585298 * history_stroke
        + 0.385407386 * history_bleeding
        + 0.280133213 * diabetes
        + 0.377903886 * moderate_severe_ckd
        + 0.489453313 * dementia
        + 0.345481149 * current_smoker
        + 0.157023564 * (race == "hispanic_latino")
        - 0.609609055 * (race == "asian")
        + 0.375675102 * (race == "black_mixed_other")
        + (0.031050027 if age_years <= 65 else 0.064594824) * (age_years - 65)
        + (-0.021535182 * (weight_kg - 75) if weight_kg <= 75 else 0)
        + (0.007678035 * (pulse_bpm - 120) if pulse_bpm <= 120 else 0)
        + (-0.019304333 * (diastolic_bp_mm_hg - 80) if diastolic_bp_mm_hg <= 80 else 0)
    )
    stroke_lp = (
        0.233182644 * heart_failure
        + 0.197919709 * vascular_disease
        + 0.800863063 * history_stroke
        + 0.29883967 * history_bleeding
        + 0.211995445 * diabetes
        + 0.349516938 * moderate_severe_ckd
        + 0.513221391 * dementia
        + 0.478831506 * current_smoker
        + 0.039138147 * (age_years - 65)
        + (0.01590016 * (diastolic_bp_mm_hg - 80) if diastolic_bp_mm_hg > 80 else 0)
    )
    bleeding_lp = (
        0.168950627 * vascular_disease
        + 0.782237771 * history_bleeding
        + 0.316245771 * carotid_disease
        + 0.498686574 * moderate_severe_ckd
        + 0.236620846 * antiplatelet
        + 0.176898047 * diabetes
        + 0.043476276 * (age_years - 65)
        + 0.004167103 * (pulse_bpm - 120)
    )

    treatment_adjustments = {
        "no_oac": (0.0, 0.0, 0.0),
        "vka": (-0.18593561, -0.352373263, 0.609713354),
        "noac": (-0.414591263, -0.572199357, 0.24232543),
    }
    baseline_survival = {
        "6_month": (0.987921904, 0.9955506465, 0.9968755499),
        "1_year": (0.9790643336, 0.9925445321, 0.9946821686),
        "2_year": (0.962450119, 0.987574311, 0.991720115),
    }
    linear_predictors = (mortality_lp, stroke_lp, bleeding_lp)
    outcome_names = ("mortality", "ischemic_stroke_or_systemic_embolism", "major_bleeding")
    risks: dict[str, dict[str, dict[str, float]]] = {}
    for horizon, baselines in baseline_survival.items():
        horizon_results: dict[str, dict[str, float]] = {name: {} for name in outcome_names}
        for treatment, adjustments in treatment_adjustments.items():
            for name, lp, adjustment, baseline in zip(
                outcome_names, linear_predictors, adjustments, baselines
            ):
                estimated_percent = 100 * (1 - baseline ** math.exp(lp + adjustment))
                horizon_results[name][treatment] = float(f"{estimated_percent:.1f}")
        risks[horizon] = horizon_results

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "scenario_risk_percent": risks,
            "linear_predictors": {
                "mortality": round(mortality_lp, 9),
                "ischemic_stroke_or_systemic_embolism": round(stroke_lp, 9),
                "major_bleeding": round(bleeding_lp, 9),
            },
            "treatment_scenarios": ("no_oac", "vka", "noac"),
            "model_version": "public 2017 GARFIELD-AF integrated model",
            "scenario_comparison_is_causal": False,
        },
        unit="%",
        interpretation=(
            "GARFIELD-AF reports model-estimated mortality, ischaemic stroke/systemic "
            "embolism, and major-bleeding risks at 6, 12, and 24 months under no-OAC, VKA, "
            "and NOAC scenarios. These are observational-model scenario estimates, not "
            "randomized causal treatment effects and not a prescription. The source population "
            "was adults with newly diagnosed non-valvular AF and at least one clinician-judged "
            "stroke risk factor; anticoagulation choice requires current guidelines, drug- and "
            "patient-specific contraindications, and shared clinical decision-making."
        ),
    )


__all__ = [
    "chokai_ureteral_stone_score",
    "dutch_lipid_clinic_network_score",
    "eortc_2006_nmibc_risk_table",
    "four_point_clock_drawing_test",
    "fullpiers_48_hour_adverse_maternal_outcome_risk",
    "guys_stone_score",
    "garfield_af_integrated_risk_2017",
    "hcm_risk_scd_2014_five_year_risk",
    "hendrich_ii_fall_risk_model",
    "isaric_4c_deterioration_probability",
    "kidney_failure_risk_equation_4_variable",
    "maggic_heart_failure_mortality_score",
    "ohts_egps_five_year_poag_point_system",
    "plcom2012_six_year_lung_cancer_risk",
    "revised_risk_analysis_index_clinical",
    "thoracoscore_in_hospital_mortality",
]
