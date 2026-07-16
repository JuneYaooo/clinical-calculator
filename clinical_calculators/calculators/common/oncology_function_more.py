from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


IMDC_FACTORS = (
    "karnofsky_less_80",
    "time_from_diagnosis_to_treatment_less_1_year",
    "hemoglobin_below_lln",
    "corrected_calcium_above_uln",
    "neutrophils_above_uln",
    "platelets_above_uln",
)


def _integer_value(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer")
    return int(numeric_value)


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    integer_value = _integer_value(inputs[key], key)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _number_in_range(inputs: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    if key not in inputs:
        raise KeyError(key)
    if isinstance(inputs[key], bool):
        raise ValueError(f"{key} must be numeric")

    numeric_value = float(inputs[key])
    if numeric_value < minimum or numeric_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return numeric_value


def _boolean_value(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)
    if not isinstance(inputs[key], bool):
        raise ValueError(f"{key} must be a boolean")
    return inputs[key]


def _choice_value(inputs: dict[str, Any], key: str, allowed: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)
    value = str(inputs[key]).strip()
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{key} must be one of: {allowed_values}")
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


def ecog_performance_status(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 0, 5)
    labels = {
        0: "fully active",
        1: "restricted in physically strenuous activity",
        2: "ambulatory and capable of self-care, up and about >50% of waking hours",
        3: "limited self-care, confined to bed or chair >50% of waking hours",
        4: "completely disabled",
        5: "dead",
    }
    return result(metadata, grade, "grade", f"ECOG performance status grade {grade}: {labels[grade]}.")


def karnofsky_performance_status(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 0, 100)
    if score % 10 != 0:
        raise ValueError("score must be a multiple of 10")

    labels = {
        100: "normal",
        90: "able normal activity with minor symptoms",
        80: "normal activity with effort",
        70: "cares for self, unable normal activity/work",
        60: "requires occasional assistance",
        50: "requires considerable assistance",
        40: "disabled",
        30: "severely disabled",
        20: "very sick",
        10: "moribund",
        0: "dead",
    }
    return result(metadata, score, "points", f"Karnofsky performance status {score}: {labels[score]}.")


def palliative_performance_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 0, 100)
    if score % 10 != 0:
        raise ValueError("score must be a multiple of 10")
    labels = {
        100: "full ambulation and normal activity",
        90: "full ambulation with some evidence of disease",
        80: "full ambulation with effort",
        70: "reduced ambulation and unable normal job/work",
        60: "reduced ambulation and unable hobby/house work",
        50: "mainly sit/lie with considerable assistance",
        40: "mainly in bed with mainly assistance",
        30: "totally bed bound",
        20: "totally bed bound with extensive disease",
        10: "totally bed bound and drowsy/coma",
        0: "dead",
    }
    return result(metadata, score, "points", f"Palliative Performance Scale {score}: {labels[score]}.")


def lansky_play_performance_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 0, 100)
    if score % 10 != 0:
        raise ValueError("score must be a multiple of 10")
    if score >= 80:
        label = "active with minor restriction or fatigue"
    elif score >= 50:
        label = "restricted active play"
    elif score >= 20:
        label = "limited quiet play or needs considerable assistance"
    elif score >= 10:
        label = "no play, does not get out of bed"
    else:
        label = "unresponsive"
    return result(metadata, score, "points", f"Lansky play-performance scale {score}: {label}.")


def imdc_risk_model_renal_cell_carcinoma(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(1 for factor in IMDC_FACTORS if _boolean_value(inputs, factor))

    if score == 0:
        risk = "favorable"
    elif score <= 2:
        risk = "intermediate"
    else:
        risk = "poor"

    return result(metadata, score, "risk factors", f"IMDC risk model: {risk} risk ({score} factors).")


def gleason_grade_group(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    primary = _integer_in_range(inputs, "primary_pattern", 1, 5)
    secondary = _integer_in_range(inputs, "secondary_pattern", 1, 5)
    gleason_score = primary + secondary

    if (primary, secondary) == (3, 3):
        grade_group = 1
    elif (primary, secondary) == (3, 4):
        grade_group = 2
    elif (primary, secondary) == (4, 3):
        grade_group = 3
    elif gleason_score == 8 and primary >= 3 and secondary >= 3:
        grade_group = 4
    elif 9 <= gleason_score <= 10:
        grade_group = 5
    else:
        raise ValueError("Gleason primary and secondary patterns do not map to a supported grade group")

    return result(
        metadata,
        grade_group,
        "grade group",
        f"Gleason score {gleason_score} ({primary}+{secondary}): grade group {grade_group}.",
    )


def genant_semiquantitative_vertebral_fracture_grade(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    height_loss = _number_in_range(inputs, "height_loss_percent", 0, 100)
    if height_loss < 20:
        grade = 0
        label = "normal or no Genant vertebral fracture by height-loss threshold"
    elif height_loss < 25:
        grade = 1
        label = "mild vertebral fracture"
    elif height_loss < 40:
        grade = 2
        label = "moderate vertebral fracture"
    else:
        grade = 3
        label = "severe vertebral fracture"
    return result(metadata, grade, "grade", f"Genant semiquantitative grade {grade}: {label}.")


def recist_1_1_response(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    baseline_sum = _number_in_range(inputs, "baseline_sum_mm", 0.0001, 100000)
    current_sum = _number_in_range(inputs, "current_sum_mm", 0, 100000)
    nadir_sum = _number_in_range(inputs, "nadir_sum_mm", 0.0001, 100000)
    target_lesions_absent = _boolean_value(inputs, "target_lesions_absent")
    new_lesions = _boolean_value(inputs, "new_lesions")
    non_target_progressive_disease = _boolean_value(inputs, "non_target_progressive_disease")

    baseline_change_percent = ((current_sum - baseline_sum) / baseline_sum) * 100
    nadir_change_percent = ((current_sum - nadir_sum) / nadir_sum) * 100
    nadir_absolute_increase = current_sum - nadir_sum

    if new_lesions or non_target_progressive_disease:
        reasons = []
        if new_lesions:
            reasons.append("new lesions")
        if non_target_progressive_disease:
            reasons.append("non-target lesion progressive disease")
        return _category_result(
            metadata,
            "PD",
            "response",
            f"RECIST 1.1 progressive disease due to {' and '.join(reasons)}.",
        )

    if target_lesions_absent:
        return _category_result(
            metadata,
            "CR",
            "response",
            "RECIST 1.1 complete response: disappearance of target lesions with no progression trigger.",
        )

    if nadir_change_percent >= 20 and nadir_absolute_increase >= 5:
        return _category_result(
            metadata,
            "PD",
            "response",
            "RECIST 1.1 progressive disease: at least 20% increase from nadir and at least 5 mm absolute increase.",
        )

    if baseline_change_percent <= -30:
        return _category_result(
            metadata,
            "PR",
            "response",
            "RECIST 1.1 partial response: at least 30% decrease in target-lesion sum from baseline.",
        )

    return _category_result(
        metadata,
        "SD",
        "response",
        "RECIST 1.1 stable disease: neither sufficient shrinkage for PR nor sufficient increase for PD.",
    )


def irecist_response(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    target_response = _choice_value(inputs, "target_response", {"CR", "PR", "SD", "PD", "NE"})
    non_target_response = _choice_value(
        inputs, "non_target_response", {"CR", "non-CR/non-PD", "PD", "NE"}
    )
    new_lesions = _boolean_value(inputs, "new_lesions")
    prior_iupd = _boolean_value(inputs, "prior_iupd")
    progression_confirmed = _boolean_value(inputs, "progression_confirmed")

    progression_present = target_response == "PD" or non_target_response == "PD" or new_lesions
    if progression_present:
        if prior_iupd and progression_confirmed:
            return _category_result(
                metadata,
                "iCPD",
                "response",
                "iRECIST confirmed progressive disease after prior iUPD with confirmed further progression.",
            )
        return _category_result(
            metadata,
            "iUPD",
            "response",
            "iRECIST unconfirmed progressive disease: first progression event requires confirmation.",
        )

    if target_response == "CR" and non_target_response in {"CR", "non-CR/non-PD"}:
        response = "iCR"
        label = "complete response"
    elif target_response == "PR" and non_target_response in {"CR", "non-CR/non-PD", "NE"}:
        response = "iPR"
        label = "partial response"
    elif target_response in {"SD", "NE"} or non_target_response in {"non-CR/non-PD", "NE"}:
        response = "iSD"
        label = "stable disease"
    else:
        response = "iNE"
        label = "not evaluable"

    return _category_result(metadata, response, "response", f"iRECIST {label} ({response}).")


def palliative_prognostic_score_pap(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    dyspnea_points = 1.0 if _boolean_value(inputs, "dyspnea") else 0.0
    anorexia_points = 1.5 if _boolean_value(inputs, "anorexia") else 0.0

    karnofsky_score = _integer_in_range(inputs, "karnofsky_score", 10, 100)
    if karnofsky_score % 10 != 0:
        raise ValueError("karnofsky_score must be a multiple of 10")
    karnofsky_points = 0.0 if karnofsky_score >= 30 else 2.5

    clinical_prediction_weeks = _number_in_range(inputs, "clinical_prediction_weeks", 0, 1000)
    if clinical_prediction_weeks > 12:
        clinical_prediction_points = 0.0
    elif clinical_prediction_weeks >= 11:
        clinical_prediction_points = 2.0
    elif clinical_prediction_weeks >= 9:
        clinical_prediction_points = 2.5
    elif clinical_prediction_weeks >= 7:
        clinical_prediction_points = 2.5
    elif clinical_prediction_weeks >= 5:
        clinical_prediction_points = 6.0
    elif clinical_prediction_weeks >= 3:
        clinical_prediction_points = 8.5
    else:
        clinical_prediction_points = 8.5

    white_blood_cell_count = _number_in_range(inputs, "white_blood_cell_count_10e9_l", 0, 1000)
    if white_blood_cell_count <= 8.5:
        white_blood_cell_points = 0.0
    elif white_blood_cell_count <= 11:
        white_blood_cell_points = 0.5
    else:
        white_blood_cell_points = 1.5

    lymphocyte_percentage = _number_in_range(inputs, "lymphocyte_percentage", 0, 100)
    if lymphocyte_percentage >= 20:
        lymphocyte_points = 0.0
    elif lymphocyte_percentage >= 12:
        lymphocyte_points = 1.0
    else:
        lymphocyte_points = 2.5

    score = (
        dyspnea_points
        + anorexia_points
        + karnofsky_points
        + clinical_prediction_points
        + white_blood_cell_points
        + lymphocyte_points
    )
    if score <= 5.5:
        group = "A"
        survival = "greater than 70% probability of 30-day survival"
    elif score <= 11:
        group = "B"
        survival = "30% to 70% probability of 30-day survival"
    else:
        group = "C"
        survival = "less than 30% probability of 30-day survival"

    return result(metadata, score, "points", f"PaP score {score:g}: group {group}, {survival}.")


def palliative_prognostic_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    pps = _integer_in_range(inputs, "palliative_performance_scale", 10, 100)
    if pps % 10 != 0:
        raise ValueError("palliative_performance_scale must be a multiple of 10")
    if pps <= 20:
        pps_points = 4.0
    elif pps <= 50:
        pps_points = 2.5
    else:
        pps_points = 0.0

    oral_intake = _choice_value(inputs, "oral_intake", {"normal", "moderately_reduced", "mouthfuls_or_less"})
    oral_points = {
        "normal": 0.0,
        "moderately_reduced": 1.0,
        "mouthfuls_or_less": 2.5,
    }[oral_intake]

    edema_points = 1.0 if _boolean_value(inputs, "edema") else 0.0
    dyspnea_points = 3.5 if _boolean_value(inputs, "dyspnea_at_rest") else 0.0
    delirium_points = 4.0 if _boolean_value(inputs, "delirium") else 0.0
    score = pps_points + oral_points + edema_points + dyspnea_points + delirium_points

    if score > 6:
        interpretation = "PPI greater than 6: high likelihood of survival shorter than 3 weeks."
    elif score > 4:
        interpretation = "PPI greater than 4: increased likelihood of survival shorter than 6 weeks."
    else:
        interpretation = "PPI 4 or lower: lower short-term mortality risk by PPI cutoffs."
    return result(metadata, score, "points", interpretation)


def radiation_pneumonitis_dose_constraint_support(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    mean_lung_dose = _number_in_range(inputs, "mean_lung_dose_gy", 0, 200)
    v20_percent = _number_in_range(inputs, "v20_percent", 0, 100)

    exceeded = []
    if mean_lung_dose > 20:
        exceeded.append("mean lung dose >20 Gy")
    if v20_percent > 30:
        exceeded.append("V20 >30%")

    if exceeded:
        return _category_result(
            metadata,
            "constraints_exceeded",
            "classification",
            "Radiation pneumonitis dose constraints exceeded: " + ", ".join(exceeded) + ".",
        )

    return _category_result(
        metadata,
        "within_constraints",
        "classification",
        "Radiation pneumonitis dose constraints within QUANTEC-style support thresholds: mean lung dose <=20 Gy and V20 <=30%.",
    )


def van_nuys_prognostic_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    tumor_size = _number_in_range(inputs, "tumor_size_mm", 0, 1000)
    if tumor_size <= 15:
        size_points = 1
    elif tumor_size <= 40:
        size_points = 2
    else:
        size_points = 3

    margin_width = _number_in_range(inputs, "margin_width_mm", 0, 1000)
    if margin_width >= 10:
        margin_points = 1
    elif margin_width >= 1:
        margin_points = 2
    else:
        margin_points = 3

    pathologic_classification = _choice_value(
        inputs,
        "pathologic_classification",
        {
            "low_or_intermediate_without_necrosis",
            "low_or_intermediate_with_necrosis",
            "high_grade",
        },
    )
    pathology_points = {
        "low_or_intermediate_without_necrosis": 1,
        "low_or_intermediate_with_necrosis": 2,
        "high_grade": 3,
    }[pathologic_classification]

    age = _number_in_range(inputs, "age_years", 0, 130)
    if age > 60:
        age_points = 1
    elif age >= 40:
        age_points = 2
    else:
        age_points = 3

    score = size_points + margin_points + pathology_points + age_points
    if score <= 6:
        risk = "low risk"
    elif score <= 9:
        risk = "intermediate risk"
    else:
        risk = "high risk"

    return result(metadata, score, "points", f"Van Nuys Prognostic Index for DCIS: {risk}.")
