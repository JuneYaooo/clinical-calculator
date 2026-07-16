from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _coded_integer(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
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


def _number_in_range(inputs: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    value = number(inputs, key)
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum:g} and {maximum:g}")
    return value


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _points_from_allowed(inputs: dict[str, Any], key: str, allowed: set[int]) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    points = int(value)
    if points not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
    return points


def _score_items(inputs: dict[str, Any], count: int, minimum: float, maximum: float) -> list[float]:
    if "items" not in inputs:
        raise KeyError("items")
    values = inputs["items"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"items must be a sequence of {count} scores")
    if len(values) != count:
        raise ValueError(f"items must contain exactly {count} scores")

    scores = []
    for index, raw in enumerate(values):
        score = float(raw)
        if score < minimum or score > maximum:
            raise ValueError(f"items[{index}] must be between {minimum:g} and {maximum:g}")
        scores.append(score)
    return scores


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def _choice_input(inputs: dict[str, Any], key: str, allowed: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)
    value = str(inputs[key]).strip().lower()
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
    return value


def _category_result(
    metadata: CalculatorMetadata, value: str, unit: str, interpretation: str
) -> CalculationResult:
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit=unit,
        interpretation=interpretation,
    )


def _joint_count_28(inputs: dict[str, Any], key: str) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer from 0 to 28")

    integer_value = int(value)
    if integer_value < 0 or integer_value > 28:
        raise ValueError(f"{key} must be between 0 and 28")
    return integer_value


def _joint_count(inputs: dict[str, Any], key: str, maximum: int) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer from 0 to {maximum}")

    integer_value = int(value)
    if integer_value < 0 or integer_value > maximum:
        raise ValueError(f"{key} must be between 0 and {maximum}")
    return integer_value


def _nonnegative_integer(inputs: dict[str, Any], key: str) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    integer_value = int(value)
    if integer_value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return integer_value


def isth_bleeding_assessment_tool_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    total_score = _nonnegative_integer(inputs, "total_score")
    pediatric = _bool_input(inputs, "pediatric")
    sex = None

    if pediatric:
        threshold = 3
    else:
        sex = _choice_input(inputs, "sex", {"male", "female"})
        threshold = 4 if sex == "male" else 6

    abnormal = total_score >= threshold
    value = {
        "total_score": total_score,
        "threshold": threshold,
        "abnormal_screen": abnormal,
        "pediatric": pediatric,
        "sex": sex,
    }
    classification = "abnormal" if abnormal else "not abnormal"
    population = "pediatric" if pediatric else f"adult {sex}"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"ISTH-BAT pre-scored total is {classification} for {population} threshold.",
    )


def heparin_induced_thrombocytopenia_4ts_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(
        _coded_integer(inputs, key, 0, 2)
        for key in (
            "thrombocytopenia",
            "timing",
            "thrombosis",
            "other_causes",
        )
    )

    if score <= 3:
        probability = "low probability"
    elif score <= 5:
        probability = "intermediate probability"
    else:
        probability = "high probability"

    return result(metadata, score, "points", f"4Ts HIT pretest probability: {probability}.")


def das28_esr(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    tender_joint_count = _joint_count_28(inputs, "tender_joint_count_28")
    swollen_joint_count = _joint_count_28(inputs, "swollen_joint_count_28")
    esr = _positive_number(inputs, "esr_mm_hr")
    patient_global_health = _number_in_range(inputs, "patient_global_health", 0, 100)

    score = (
        0.56 * math.sqrt(tender_joint_count)
        + 0.28 * math.sqrt(swollen_joint_count)
        + 0.70 * math.log(esr)
        + 0.014 * patient_global_health
    )

    if score <= 2.6:
        activity = "remission"
    elif score <= 3.2:
        activity = "low"
    elif score <= 5.1:
        activity = "moderate"
    else:
        activity = "high"

    return result(metadata, score, "points", f"DAS28-ESR rheumatoid arthritis disease activity: {activity}.")


def dapsa_psoriatic_arthritis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _joint_count(inputs, "tender_joint_count_68", 68)
        + _joint_count(inputs, "swollen_joint_count_66", 66)
        + _number_in_range(inputs, "patient_global_assessment", 0, 10)
        + _number_in_range(inputs, "patient_pain", 0, 10)
        + _non_negative_number(inputs, "crp_mg_dl")
    )

    if score <= 4:
        activity = "remission"
    elif score <= 14:
        activity = "low"
    elif score <= 28:
        activity = "moderate"
    else:
        activity = "high"

    return result(metadata, score, "points", f"DAPSA psoriatic arthritis disease activity: {activity}.")


def cdai_rheumatoid_arthritis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _joint_count_28(inputs, "tender_joint_count_28")
        + _joint_count_28(inputs, "swollen_joint_count_28")
        + _number_in_range(inputs, "patient_global_assessment", 0, 10)
        + _number_in_range(inputs, "provider_global_assessment", 0, 10)
    )

    if score <= 2.8:
        activity = "remission"
    elif score <= 10:
        activity = "low"
    elif score <= 22:
        activity = "moderate"
    else:
        activity = "high"

    return result(metadata, score, "points", f"CDAI rheumatoid arthritis disease activity: {activity}.")


def sdai_rheumatoid_arthritis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _joint_count_28(inputs, "tender_joint_count_28")
        + _joint_count_28(inputs, "swollen_joint_count_28")
        + _number_in_range(inputs, "patient_global_assessment", 0, 10)
        + _number_in_range(inputs, "provider_global_assessment", 0, 10)
        + _number_in_range(inputs, "crp_mg_dl", 0, 100)
    )

    if score <= 3.3:
        activity = "remission"
    elif score <= 11:
        activity = "low"
    elif score <= 26:
        activity = "moderate"
    else:
        activity = "high"
    return result(metadata, score, "points", f"SDAI rheumatoid arthritis disease activity: {activity}.")


def basdai_ankylosing_spondylitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    items = _score_items(inputs, 6, 0, 10)
    score = (items[0] + items[1] + items[2] + items[3] + ((items[4] + items[5]) / 2)) / 5
    interpretation = "active disease by BASDAI threshold" if score >= 4 else "lower disease activity by BASDAI"
    return result(metadata, score, "score", interpretation)


def basfi_ankylosing_spondylitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    items = _score_items(inputs, 10, 0, 10)
    score = sum(items) / 10
    return result(metadata, score, "score", "BASFI functional limitation score; higher scores indicate worse function.")


def asdas_ankylosing_spondylitis_disease_activity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    back_pain = _number_in_range(inputs, "inflammatory_back_pain", 0, 10)
    morning_stiffness = _number_in_range(inputs, "morning_stiffness", 0, 10)
    patient_global = _number_in_range(inputs, "patient_global", 0, 10)
    peripheral = _number_in_range(inputs, "peripheral_pain_swelling", 0, 10)

    has_crp = "crp_mg_l" in inputs
    has_esr = "esr_mm_hr" in inputs
    if has_crp == has_esr:
        raise ValueError("provide exactly one of crp_mg_l or esr_mm_hr")

    if has_crp:
        score = (
            0.12 * back_pain
            + 0.06 * morning_stiffness
            + 0.11 * patient_global
            + 0.07 * peripheral
            + 0.58 * math.log(_non_negative_number(inputs, "crp_mg_l") + 1)
        )
        method = "CRP"
    else:
        score = (
            0.08 * back_pain
            + 0.07 * morning_stiffness
            + 0.11 * patient_global
            + 0.09 * peripheral
            + 0.29 * math.sqrt(_non_negative_number(inputs, "esr_mm_hr"))
        )
        method = "ESR"

    if score < 1.3:
        activity = "inactive disease"
    elif score < 2.1:
        activity = "moderate disease activity"
    elif score <= 3.5:
        activity = "high disease activity"
    else:
        activity = "very high disease activity"
    return result(metadata, score, "score", f"ASDAS-{method}: {activity}.")


def acr_eular_2015_gout_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    entry_criterion = _bool_input(inputs, "entry_criterion")
    sufficient_msu_crystals = _bool_input(inputs, "sufficient_msu_crystals")

    if not entry_criterion:
        value = {"score": None, "entry_criterion": False, "classified_as_gout": False}
        return CalculationResult(
            calculator_id=metadata.id,
            status="implemented",
            message="calculation completed",
            value=value,
            unit="points",
            interpretation="2015 ACR/EULAR gout classification entry criterion not met.",
        )

    if sufficient_msu_crystals:
        value = {"score": None, "entry_criterion": True, "classified_as_gout": True}
        return CalculationResult(
            calculator_id=metadata.id,
            status="implemented",
            message="calculation completed",
            value=value,
            unit="points",
            interpretation="2015 ACR/EULAR gout classification sufficient criterion met.",
        )

    score = (
        _points_from_allowed(inputs, "clinical_pattern", {0, 1, 2})
        + _points_from_allowed(inputs, "episode_characteristics", {0, 1, 2})
        + _points_from_allowed(inputs, "time_course", {0, 1, 2})
        + _points_from_allowed(inputs, "tophus", {0, 4})
        + _points_from_allowed(inputs, "serum_urate", {-4, 0, 2, 3, 4})
        + _points_from_allowed(inputs, "synovial_fluid", {-2, 0})
        + _points_from_allowed(inputs, "imaging_urate_deposition", {0, 4})
        + _points_from_allowed(inputs, "imaging_gout_erosion", {0, 4})
    )
    classified = score >= 8
    value = {"score": score, "entry_criterion": True, "classified_as_gout": classified}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"2015 ACR/EULAR gout classification score {score}: {'classified' if classified else 'not classified'}.",
    )


def adjusted_gapss_antiphospholipid_syndrome_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = 0
    if _bool_input(inputs, "anticardiolipin"):
        score += 5
    if _bool_input(inputs, "anti_beta2_glycoprotein_i"):
        score += 4
    if _bool_input(inputs, "lupus_anticoagulant"):
        score += 4
    if _bool_input(inputs, "hyperlipidemia"):
        score += 3
    if _bool_input(inputs, "arterial_hypertension"):
        score += 1

    interpretation = "Adjusted GAPSS: higher scores indicate higher thrombotic risk."
    return result(metadata, score, "points", interpretation)


def isth_overt_dic_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    platelets = _positive_number(inputs, "platelets_10e9_l")
    if platelets < 50:
        score = 2
    elif platelets <= 100:
        score = 1
    else:
        score = 0

    fibrin_marker = inputs.get("fibrin_marker_increase")
    fibrin_marker_points = {"none": 0, "moderate": 2, "strong": 3}
    if fibrin_marker not in fibrin_marker_points:
        raise ValueError("fibrin_marker_increase must be one of: none, moderate, strong")
    score += fibrin_marker_points[fibrin_marker]

    pt_prolongation = _number_in_range(inputs, "pt_prolongation_seconds", 0, 300)
    if pt_prolongation > 6:
        score += 2
    elif pt_prolongation >= 3:
        score += 1

    if _positive_number(inputs, "fibrinogen_g_l") <= 1.0:
        score += 1

    interpretation = (
        "ISTH overt DIC score compatible with overt DIC; repeat scoring and treat underlying disorder."
        if score >= 5
        else "ISTH overt DIC score below overt DIC threshold."
    )
    return result(metadata, score, "points", interpretation)


def cll_international_prognostic_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    stage = str(inputs.get("clinical_stage", "")).strip().lower()
    if stage not in {"low", "rai_i_iv", "binet_b_c"}:
        raise ValueError("clinical_stage must be one of: low, rai_i_iv, binet_b_c")

    score = 0
    if _positive_number(inputs, "age_years") > 65:
        score += 1
    if stage in {"rai_i_iv", "binet_b_c"}:
        score += 1
    if _positive_number(inputs, "beta2_microglobulin_mg_l") > 3.5:
        score += 2
    if _bool_input(inputs, "ighv_unmutated"):
        score += 2
    if _bool_input(inputs, "del17p_or_tp53_mutated"):
        score += 4

    if score <= 1:
        risk = "low risk"
    elif score <= 3:
        risk = "intermediate risk"
    elif score <= 6:
        risk = "high risk"
    else:
        risk = "very high risk"
    return result(metadata, score, "points", f"CLL-IPI: {risk}.")


def rapid3_rheumatoid_arthritis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _number_in_range(inputs, "physical_function", 0, 10)
        + _number_in_range(inputs, "pain", 0, 10)
        + _number_in_range(inputs, "patient_global", 0, 10)
    )
    if score <= 3:
        activity = "remission"
    elif score <= 6:
        activity = "low severity"
    elif score <= 12:
        activity = "moderate severity"
    else:
        activity = "high severity"
    return result(metadata, score, "points", f"RAPID3 rheumatoid arthritis activity: {activity}.")


def acr_eular_2010_rheumatoid_arthritis_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    component_specs = {
        "joint_involvement": {0, 1, 2, 3, 5},
        "serology": {0, 2, 3},
        "acute_phase_reactants": {0, 1},
        "symptom_duration": {0, 1},
    }
    score = 0
    for key, allowed in component_specs.items():
        score += _coded_integer(inputs, key, min(allowed), max(allowed))
        if score and _coded_integer(inputs, key, min(allowed), max(allowed)) not in allowed:
            raise ValueError(f"{key} must be one of: {sorted(allowed)}")

    classified = score >= 6
    value = {"score": score, "definite_ra_classification": classified}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"2010 ACR/EULAR RA classification score {score}: {'classified' if classified else 'not classified'}.",
    )


def sle_2019_eular_acr_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ana_positive = _bool_input(inputs, "ana_positive")
    clinical_criterion_present = _bool_input(inputs, "clinical_criterion_present")
    raw_scores = inputs.get("weighted_domain_scores")
    if isinstance(raw_scores, (str, bytes)) or not isinstance(raw_scores, Sequence):
        raise ValueError("weighted_domain_scores must be a sequence of nonnegative domain scores")

    scores = []
    for index, raw_score in enumerate(raw_scores):
        score = float(raw_score)
        if score < 0:
            raise ValueError(f"weighted_domain_scores[{index}] must be nonnegative")
        scores.append(score)
    total = sum(scores) if ana_positive else 0
    classified = ana_positive and clinical_criterion_present and total >= 10
    value = {
        "score": round(total, 4),
        "ana_entry_criterion": ana_positive,
        "clinical_criterion_present": clinical_criterion_present,
        "classified_as_sle": classified,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"2019 EULAR/ACR SLE classification score {round(total, 4)}: {'classified' if classified else 'not classified'}.",
    )


def revised_international_prognostic_scoring_system_mds(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    cytogenetic_points = {
        "very_good": 0,
        "good": 1,
        "intermediate": 2,
        "poor": 3,
        "very_poor": 4,
    }[_choice_input(inputs, "cytogenetic_risk", {"very_good", "good", "intermediate", "poor", "very_poor"})]

    blasts = _number_in_range(inputs, "bone_marrow_blast_percent", 0, 100)
    if blasts <= 2:
        blast_points = 0
    elif blasts < 5:
        blast_points = 1
    elif blasts <= 10:
        blast_points = 2
    else:
        blast_points = 3

    hemoglobin = _positive_number(inputs, "hemoglobin_g_dl")
    if hemoglobin >= 10:
        hemoglobin_points = 0
    elif hemoglobin >= 8:
        hemoglobin_points = 1
    else:
        hemoglobin_points = 1.5

    platelets = _positive_number(inputs, "platelets_10e9_l")
    if platelets >= 100:
        platelet_points = 0
    elif platelets >= 50:
        platelet_points = 0.5
    else:
        platelet_points = 1

    anc = _non_negative_number(inputs, "absolute_neutrophil_count_10e9_l")
    anc_points = 0 if anc >= 0.8 else 0.5

    score = cytogenetic_points + blast_points + hemoglobin_points + platelet_points + anc_points
    if score <= 1.5:
        risk = "very low risk"
    elif score <= 3:
        risk = "low risk"
    elif score <= 4.5:
        risk = "intermediate risk"
    elif score <= 6:
        risk = "high risk"
    else:
        risk = "very high risk"

    return result(metadata, score, "points", f"IPSS-R MDS: {risk}.")


def revised_international_staging_system_multiple_myeloma(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    beta2_microglobulin = _positive_number(inputs, "beta2_microglobulin_mg_l")
    albumin = _positive_number(inputs, "albumin_g_dl")
    ldh_high = _bool_input(inputs, "ldh_above_upper_limit_normal")
    high_risk_cytogenetics = _bool_input(inputs, "high_risk_cytogenetics")

    if beta2_microglobulin < 3.5 and albumin >= 3.5:
        iss_stage = "I"
    elif beta2_microglobulin >= 5.5:
        iss_stage = "III"
    else:
        iss_stage = "II"

    if iss_stage == "I" and not ldh_high and not high_risk_cytogenetics:
        r_iss_stage = "I"
    elif iss_stage == "III" and (ldh_high or high_risk_cytogenetics):
        r_iss_stage = "III"
    else:
        r_iss_stage = "II"

    return _category_result(
        metadata,
        r_iss_stage,
        "stage",
        f"R-ISS multiple myeloma stage {r_iss_stage} (ISS stage {iss_stage}).",
    )


def sledai_2k_disease_activity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        8 * _coded_integer(inputs, "weight_8_count", 0, 8)
        + 4 * _coded_integer(inputs, "weight_4_count", 0, 6)
        + 2 * _coded_integer(inputs, "weight_2_count", 0, 7)
        + _coded_integer(inputs, "weight_1_count", 0, 3)
    )

    if score == 0:
        activity = "no activity"
    elif score <= 5:
        activity = "mild activity"
    elif score <= 10:
        activity = "moderate activity"
    elif score <= 19:
        activity = "high activity"
    else:
        activity = "very high activity"

    return result(metadata, score, "points", f"SLEDAI-2K disease activity: {activity}.")


ESSDAI_DOMAIN_WEIGHTS = {
    "constitutional": 3,
    "lymphadenopathy": 4,
    "glandular": 2,
    "articular": 2,
    "cutaneous": 3,
    "pulmonary": 5,
    "renal": 5,
    "muscular": 6,
    "peripheral_nervous_system": 5,
    "central_nervous_system": 5,
    "hematological": 2,
    "biological": 1,
}


def essdai_sjogrens_disease_activity(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(weight * _coded_integer(inputs, domain, 0, 3) for domain, weight in ESSDAI_DOMAIN_WEIGHTS.items())

    if score == 0:
        activity = "no systemic activity"
    elif score < 5:
        activity = "low systemic activity"
    elif score < 14:
        activity = "moderate systemic activity"
    else:
        activity = "high systemic activity"

    return result(metadata, score, "points", f"ESSDAI Sjogren's disease activity: {activity}.")


HCT_CI_WEIGHTS = {
    "arrhythmia": 1,
    "cardiac": 1,
    "inflammatory_bowel_disease": 1,
    "diabetes": 1,
    "cerebrovascular_disease": 1,
    "psychiatric_disturbance": 1,
    "mild_hepatic": 1,
    "obesity": 1,
    "infection": 1,
    "rheumatologic": 2,
    "peptic_ulcer": 2,
    "moderate_or_severe_renal": 2,
    "moderate_pulmonary": 2,
    "prior_solid_tumor": 3,
    "heart_valve_disease": 3,
    "severe_pulmonary": 3,
    "moderate_or_severe_hepatic": 3,
}


def hct_ci(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if _bool_input(inputs, "mild_hepatic") and _bool_input(inputs, "moderate_or_severe_hepatic"):
        raise ValueError("provide only one hepatic HCT-CI severity category")
    if _bool_input(inputs, "moderate_pulmonary") and _bool_input(inputs, "severe_pulmonary"):
        raise ValueError("provide only one pulmonary HCT-CI severity category")

    score = sum(weight for key, weight in HCT_CI_WEIGHTS.items() if _bool_input(inputs, key))
    if score == 0:
        risk = "low comorbidity burden"
    elif score <= 2:
        risk = "intermediate comorbidity burden"
    else:
        risk = "high comorbidity burden"

    return result(metadata, score, "points", f"HCT-CI: {risk}.")


def jaam_dic_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 1 if _coded_integer(inputs, "sirs_criteria_count", 0, 4) >= 3 else 0

    platelets = _positive_number(inputs, "platelets_10e9_l")
    if platelets <= 80:
        platelet_points = 3
    elif platelets < 120:
        platelet_points = 1
    else:
        platelet_points = 0

    platelet_decrease = _number_in_range(inputs, "platelet_decrease_percent_24h", 0, 100)
    if platelet_decrease > 50:
        platelet_decrease_points = 3
    elif platelet_decrease > 30:
        platelet_decrease_points = 1
    else:
        platelet_decrease_points = 0
    score += max(platelet_points, platelet_decrease_points)

    fdp = _non_negative_number(inputs, "fdp_mcg_ml")
    if fdp >= 25:
        score += 3
    elif fdp >= 10:
        score += 1

    if _positive_number(inputs, "pt_ratio") >= 1.2:
        score += 1

    interpretation = "JAAM DIC score meets DIC diagnostic threshold." if score >= 4 else "JAAM DIC score below DIC threshold."
    return result(metadata, score, "points", interpretation)


def dipss_myelofibrosis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _positive_number(inputs, "age_years") > 65:
        score += 1
    if _positive_number(inputs, "hemoglobin_g_dl") < 10:
        score += 2
    if _positive_number(inputs, "leukocyte_count_10e9_l") > 25:
        score += 1
    if _number_in_range(inputs, "circulating_blast_percent", 0, 100) >= 1:
        score += 1
    if _bool_input(inputs, "constitutional_symptoms"):
        score += 1

    if score == 0:
        risk = "low risk"
    elif score <= 2:
        risk = "intermediate-1 risk"
    elif score <= 4:
        risk = "intermediate-2 risk"
    else:
        risk = "high risk"

    return result(metadata, score, "points", f"DIPSS myelofibrosis: {risk}.")


def eln_2022_aml_risk_stratification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    favorable_recurrent = _bool_input(inputs, "favorable_recurrent_genetic_abnormality")
    mutated_npm1 = _bool_input(inputs, "mutated_npm1")
    flt3_itd = _bool_input(inputs, "flt3_itd")
    bzip_cebpa = _bool_input(inputs, "bzip_in_frame_cebpa")
    t_9_11 = _bool_input(inputs, "t_9_11")
    adverse_cytogenetics = _bool_input(inputs, "adverse_risk_cytogenetics")
    adverse_gene_mutation = _bool_input(inputs, "adverse_risk_gene_mutation")

    favorable = favorable_recurrent or (mutated_npm1 and not flt3_itd) or bzip_cebpa
    if adverse_cytogenetics:
        risk = "adverse"
        reason = "adverse-risk cytogenetics"
    elif favorable:
        risk = "favorable"
        reason = "favorable-risk genetic feature"
    elif adverse_gene_mutation:
        risk = "adverse"
        reason = "adverse-risk gene mutation without an overriding favorable subtype"
    elif flt3_itd or t_9_11:
        risk = "intermediate"
        reason = "intermediate-risk genetic feature"
    else:
        risk = "intermediate"
        reason = "not otherwise classified as favorable or adverse by coded ELN 2022 inputs"

    return _category_result(metadata, risk, "risk", f"ELN 2022 AML risk: {risk} ({reason}).")


def polycythemia_vera_thrombosis_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age = _non_negative_number(inputs, "age_years")
    prior_thrombosis = _bool_input(inputs, "prior_thrombosis")

    risk = "high" if age > 60 or prior_thrombosis else "low"
    interpretation = (
        "Polycythemia vera thrombosis risk: high risk by age >60 years or prior thrombosis."
        if risk == "high"
        else "Polycythemia vera thrombosis risk: low risk by absence of age >60 years and prior thrombosis."
    )
    return _category_result(metadata, risk, "risk", interpretation)
