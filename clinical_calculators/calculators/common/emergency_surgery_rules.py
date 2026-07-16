from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _boolean_flag(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = _number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _score_true(inputs: dict[str, Any], key: str, points: int = 1) -> int:
    return points if _boolean_flag(inputs, key) else 0


def _allowed_points(inputs: dict[str, Any], key: str, allowed: set[int]) -> int:
    value = _integer_in_range(inputs, key, min(allowed), max(allowed))
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
    return value


def _choice(inputs: dict[str, Any], key: str, choices: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in choices:
        raise ValueError(f"{key} must be one of: {sorted(choices)}")
    return value


def centor_mcisaac_strep_pharyngitis_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _number(inputs, "age_years")
    score = (
        _score_true(inputs, "fever")
        + _score_true(inputs, "absence_of_cough")
        + _score_true(inputs, "tender_anterior_cervical_adenopathy")
        + _score_true(inputs, "tonsillar_exudates_or_swelling")
    )

    if 3 <= age_years <= 14:
        score += 1
    elif age_years >= 45:
        score -= 1

    if score <= 1:
        interpretation = "low risk by Centor/McIsaac strep pharyngitis score"
    elif score <= 3:
        interpretation = "intermediate risk by Centor/McIsaac strep pharyngitis score"
    else:
        interpretation = "high risk by Centor/McIsaac strep pharyngitis score"

    return result(metadata, score, "points", interpretation)


def alvarado_appendicitis_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _score_true(inputs, "migration_rlq")
        + _score_true(inputs, "anorexia")
        + _score_true(inputs, "nausea_vomiting")
        + _score_true(inputs, "rlq_tenderness", 2)
        + _score_true(inputs, "rebound_tenderness")
        + _score_true(inputs, "fever")
        + _score_true(inputs, "leukocytosis", 2)
        + _score_true(inputs, "left_shift")
    )

    if score <= 4:
        interpretation = "appendicitis unlikely by Alvarado score"
    elif score <= 6:
        interpretation = "appendicitis possible by Alvarado score"
    elif score <= 8:
        interpretation = "appendicitis probable by Alvarado score"
    else:
        interpretation = "appendicitis very probable by Alvarado score"

    return result(metadata, score, "points", interpretation)


def adult_appendicitis_response_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _score_true(inputs, "vomiting") + _score_true(inputs, "rlq_pain")
    score += _integer_in_range(inputs, "rebound_or_muscular_defense", 0, 3)

    if _number(inputs, "temperature_c") >= 38.5:
        score += 1

    wbc = _number(inputs, "wbc_10e9_l")
    if wbc >= 15:
        score += 2
    elif wbc >= 10:
        score += 1

    neutrophil_percent = _number(inputs, "neutrophil_percent")
    if neutrophil_percent >= 85:
        score += 2
    elif neutrophil_percent >= 70:
        score += 1

    crp = _number(inputs, "crp_mg_l")
    if crp >= 50:
        score += 2
    elif crp >= 10:
        score += 1

    if score <= 4:
        interpretation = "low risk by Adult Appendicitis Response score"
    elif score <= 8:
        interpretation = "indeterminate risk by Adult Appendicitis Response score"
    else:
        interpretation = "high risk by Adult Appendicitis Response score"

    return result(metadata, score, "points", interpretation)


def ottawa_ankle_rules(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    unable_to_bear_weight = _boolean_flag(inputs, "unable_to_bear_weight_4_steps")
    malleolar_positive = _boolean_flag(inputs, "pain_malleolar_zone") and (
        _boolean_flag(inputs, "bone_tenderness_posterior_lateral_malleolus")
        or _boolean_flag(inputs, "bone_tenderness_posterior_medial_malleolus")
        or unable_to_bear_weight
    )
    midfoot_positive = _boolean_flag(inputs, "pain_midfoot_zone") and (
        _boolean_flag(inputs, "bone_tenderness_navicular")
        or _boolean_flag(inputs, "bone_tenderness_base_5th_metatarsal")
        or unable_to_bear_weight
    )

    positive = malleolar_positive or midfoot_positive
    interpretation = (
        "positive Ottawa ankle rule; ankle or foot radiography is indicated"
        if positive
        else "negative Ottawa ankle rule; radiography is not indicated by this rule"
    )

    return result(metadata, 1 if positive else 0, "", interpretation)


def ottawa_knee_rules(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive = (
        _number(inputs, "age_years") >= 55
        or _boolean_flag(inputs, "isolated_patellar_tenderness")
        or _boolean_flag(inputs, "fibular_head_tenderness")
        or _boolean_flag(inputs, "cannot_flex_to_90")
        or _boolean_flag(inputs, "unable_to_bear_weight_4_steps")
    )
    interpretation = (
        "positive Ottawa knee rule; knee radiography is indicated"
        if positive
        else "negative Ottawa knee rule; radiography is not indicated by this rule"
    )

    return result(metadata, 1 if positive else 0, "", interpretation)


def mangled_extremity_severity_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "skeletal_soft_tissue_injury", 1, 4)
        + _integer_in_range(inputs, "shock", 0, 2)
        + _integer_in_range(inputs, "age", 0, 2)
    )
    ischemia = _integer_in_range(inputs, "limb_ischemia", 0, 3)
    ischemia_time = _number(inputs, "ischemia_time_hours")
    if ischemia_time < 0:
        raise ValueError("ischemia_time_hours must be nonnegative")
    score += ischemia * (2 if ischemia_time > 6 else 1)

    interpretation = (
        "high MESS; limb salvage probability is poor in original threshold studies"
        if score >= 7
        else "lower MESS; interpret with vascular, orthopedic, and soft-tissue context"
    )
    return result(metadata, score, "points", interpretation)


def pediatric_trauma_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _allowed_points(inputs, key, {-1, 1, 2})
        for key in (
            "weight",
            "airway",
            "systolic_bp",
            "central_nervous_system",
            "open_wound",
            "skeletal_injury",
        )
    )
    interpretation = (
        "higher trauma risk by Pediatric Trauma Score"
        if score <= 8
        else "lower trauma risk by Pediatric Trauma Score"
    )
    return result(metadata, score, "points", interpretation)


def body_surface_area_palm_method(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    palms = _number(inputs, "patient_palms")
    if palms < 0:
        raise ValueError("patient_palms must be nonnegative")
    return result(metadata, palms, "% TBSA", "estimated burn area by patient palm method")


def nexus_chest_decision_instrument(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive = _number(inputs, "age_years") > 60
    for key in (
        "rapid_deceleration_mechanism",
        "chest_pain",
        "intoxication",
        "abnormal_alertness",
        "distracting_painful_injury",
        "chest_wall_tenderness",
    ):
        positive = positive or _boolean_flag(inputs, key)

    interpretation = (
        "positive NEXUS Chest decision instrument; chest imaging is indicated by this rule"
        if positive
        else "negative NEXUS Chest decision instrument; very low risk by this rule"
    )
    return result(metadata, 1 if positive else 0, "", interpretation)


def pecarn_pediatric_abdominal_trauma_rule(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    positive = any(
        _boolean_flag(inputs, key)
        for key in (
            "abdominal_wall_trauma_or_seatbelt_sign",
            "gcs_less_than_14",
            "abdominal_tenderness",
            "thoracic_wall_trauma",
            "abdominal_pain",
            "decreased_breath_sounds",
            "vomiting",
        )
    )
    interpretation = (
        "positive PECARN blunt abdominal trauma rule; not very low risk for intra-abdominal injury requiring acute intervention"
        if positive
        else "very low risk by PECARN blunt abdominal trauma rule when all seven criteria are absent"
    )
    return result(metadata, 1 if positive else 0, "", interpretation)


def pecarn_pediatric_head_injury_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = _number(inputs, "age_years")
    if age_years < 0 or age_years >= 18:
        raise ValueError("age_years must be from 0 to less than 18")

    altered_or_low_gcs = _boolean_flag(inputs, "gcs_le_14_or_altered_mental_status")
    severe_mechanism = _boolean_flag(inputs, "severe_mechanism")

    if age_years < 2:
        high_risk = altered_or_low_gcs or _boolean_flag(inputs, "palpable_skull_fracture")
        intermediate_risk = (
            _boolean_flag(inputs, "non_frontal_scalp_hematoma")
            or _boolean_flag(inputs, "loss_of_consciousness_5_seconds_or_more")
            or severe_mechanism
            or _boolean_flag(inputs, "not_acting_normally_per_parent")
        )
    else:
        high_risk = altered_or_low_gcs or _boolean_flag(inputs, "signs_basilar_skull_fracture")
        intermediate_risk = (
            _boolean_flag(inputs, "history_loss_of_consciousness")
            or _boolean_flag(inputs, "history_vomiting")
            or severe_mechanism
            or _boolean_flag(inputs, "severe_headache")
        )

    if high_risk:
        return result(metadata, 2, "", "high risk by PECARN pediatric head injury rule; CT is generally recommended")
    if intermediate_risk:
        return result(
            metadata,
            1,
            "",
            "intermediate risk by PECARN pediatric head injury rule; observation versus CT depends on clinical context",
        )
    return result(metadata, 0, "", "very low risk by PECARN pediatric head injury rule; CT is not routinely recommended")


def nexus_chest_ct_major_injury_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive = any(
        _boolean_flag(inputs, key)
        for key in (
            "abnormal_chest_xray",
            "distracting_injury",
            "chest_wall_tenderness",
            "sternal_tenderness",
            "thoracic_spine_tenderness",
            "scapular_tenderness",
        )
    )
    interpretation = (
        "positive NEXUS Chest CT-Major Injury rule; major thoracic injury is not excluded by this rule"
        if positive
        else "low risk by NEXUS Chest CT-Major Injury rule when all six criteria are absent"
    )
    return result(metadata, 1 if positive else 0, "", interpretation)


def injury_severity_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw_scores = inputs.get("ais_by_region")
    if isinstance(raw_scores, (str, bytes)) or not isinstance(raw_scores, Sequence):
        raise ValueError("ais_by_region must be a sequence of six AIS severity scores")
    if len(raw_scores) != 6:
        raise ValueError("ais_by_region must contain exactly six body-region scores")

    scores = []
    for index, raw_score in enumerate(raw_scores):
        if isinstance(raw_score, bool):
            raise ValueError(f"ais_by_region[{index}] must be an integer AIS score")
        numeric_score = float(raw_score)
        if not numeric_score.is_integer():
            raise ValueError(f"ais_by_region[{index}] must be an integer AIS score")
        score = int(numeric_score)
        if score < 0 or score > 6:
            raise ValueError(f"ais_by_region[{index}] must be between 0 and 6")
        scores.append(score)

    if 6 in scores:
        iss = 75
    else:
        iss = sum(score * score for score in sorted(scores, reverse=True)[:3])
    severity = "severe trauma range" if iss >= 16 else "lower injury severity range"
    return result(metadata, iss, "points", f"Injury Severity Score: {severity}.")


def triss_survival_probability(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    injury_type = _choice(inputs, "injury_type", {"blunt", "penetrating"})
    rts = _number(inputs, "revised_trauma_score")
    iss = _number(inputs, "injury_severity_score")
    age = _number(inputs, "age_years")

    if rts < 0 or rts > 7.8408:
        raise ValueError("revised_trauma_score must be between 0 and 7.8408")
    if iss < 0 or iss > 75:
        raise ValueError("injury_severity_score must be between 0 and 75")
    if age < 0:
        raise ValueError("age_years must be nonnegative")

    coefficients = {
        "blunt": (-0.4499, 0.8085, -0.0835, -1.7430),
        "penetrating": (-2.5355, 0.9934, -0.0651, -1.1360),
    }
    b0, b_rts, b_iss, b_age = coefficients[injury_type]
    age_index = 1 if age >= 55 else 0
    logit = b0 + (b_rts * rts) + (b_iss * iss) + (b_age * age_index)
    probability_percent = 100 / (1 + math.exp(-logit))

    interpretation = (
        "higher predicted survival by TRISS"
        if probability_percent >= 50
        else "lower predicted survival by TRISS"
    )
    return result(metadata, probability_percent, "%", interpretation)


def tash_trauma_associated_severe_hemorrhage_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    hemoglobin = _number(inputs, "hemoglobin_g_dl")
    base_excess = _number(inputs, "base_excess_mmol_l")
    systolic_bp = _number(inputs, "systolic_bp_mm_hg")
    heart_rate = _number(inputs, "heart_rate")
    if hemoglobin < 0:
        raise ValueError("hemoglobin_g_dl must be nonnegative")
    if systolic_bp < 0:
        raise ValueError("systolic_bp_mm_hg must be nonnegative")
    if heart_rate < 0:
        raise ValueError("heart_rate must be nonnegative")

    score = 0
    if hemoglobin < 7:
        score += 8
    elif hemoglobin < 9:
        score += 6
    elif hemoglobin < 10:
        score += 4
    elif hemoglobin < 11:
        score += 3
    elif hemoglobin < 12:
        score += 2

    if base_excess < -10:
        score += 4
    elif base_excess < -6:
        score += 3
    elif base_excess < -2:
        score += 1

    if systolic_bp < 100:
        score += 4
    elif systolic_bp < 120:
        score += 1

    if heart_rate > 120:
        score += 2
    elif heart_rate > 100:
        score += 1

    score += _score_true(inputs, "positive_fast", 3)
    score += _score_true(inputs, "unstable_pelvic_fracture", 6)
    score += _score_true(inputs, "open_or_dislocated_femur_fracture", 3)
    score += _score_true(inputs, "male")

    if score >= 23:
        risk = "very high risk"
    elif score >= 16:
        risk = "high risk"
    elif score >= 9:
        risk = "intermediate risk"
    else:
        risk = "low risk"
    return result(metadata, score, "points", f"TASH severe hemorrhage score: {risk}.")
