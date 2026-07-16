from __future__ import annotations

from collections.abc import Sequence
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


def _bool_input_default(inputs: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in inputs:
        return default
    return _bool_input(inputs, key)


def _integer_value(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{label} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return integer_value


def _integer_input(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)
    return _integer_value(inputs[key], key, minimum, maximum)


def _score_items(inputs: dict[str, Any], count: int, minimum: int, maximum: int, key: str = "items") -> int:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    return sum(
        _integer_value(value, f"{key}[{index}]", minimum, maximum)
        for index, value in enumerate(values)
    )


def _sex(inputs: dict[str, Any]) -> str:
    if "sex" not in inputs:
        raise KeyError("sex")

    sex = str(inputs["sex"]).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    return sex


def _text_choice(inputs: dict[str, Any], key: str, choices: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{key} must be one of: {allowed}")
    return value


def _range_label(score: int, ranges: tuple[tuple[int, int, str], ...]) -> str:
    for minimum, maximum, label in ranges:
        if minimum <= score <= maximum:
            return label
    raise ValueError("score is outside the supported interpretation range")


def stop_bang_sleep_apnea_screening(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = sum(
        1
        for key in (
            "snoring",
            "tired",
            "observed_apnea",
            "high_blood_pressure",
        )
        if _bool_input(inputs, key)
    )
    value += int(number(inputs, "bmi") > 35)
    value += int(number(inputs, "age_years") > 50)
    value += int(number(inputs, "neck_circumference_cm") > 40)
    value += int(_sex(inputs) == "male")

    risk = _range_label(value, ((0, 2, "low"), (3, 4, "intermediate"), (5, 8, "high")))
    return result(metadata, value, "points", f"STOP-Bang sleep apnea screening risk: {risk}.")


def bode_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    fev1_percent_predicted = number(inputs, "fev1_percent_predicted")
    six_min_walk_m = number(inputs, "six_min_walk_m")
    mmrc_grade = _integer_input(inputs, "mmrc_grade", 0, 4)
    bmi = number(inputs, "bmi")

    if fev1_percent_predicted >= 65:
        fev1_points = 0
    elif fev1_percent_predicted >= 50:
        fev1_points = 1
    elif fev1_percent_predicted >= 36:
        fev1_points = 2
    else:
        fev1_points = 3

    if six_min_walk_m >= 350:
        walk_points = 0
    elif six_min_walk_m >= 250:
        walk_points = 1
    elif six_min_walk_m >= 150:
        walk_points = 2
    else:
        walk_points = 3

    if mmrc_grade <= 1:
        mmrc_points = 0
    else:
        mmrc_points = mmrc_grade - 1

    bmi_points = 0 if bmi > 21 else 1
    value = fev1_points + walk_points + mmrc_points + bmi_points

    return result(metadata, value, "points", "BODE index; higher scores indicate higher COPD mortality risk.")


def pneumonia_severity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = _sex(inputs)
    score = int(number(inputs, "age_years"))
    if sex == "female":
        score -= 10

    score += 10 if _bool_input(inputs, "nursing_home_resident") else 0
    score += 30 if _bool_input(inputs, "neoplastic_disease") else 0
    score += 20 if _bool_input(inputs, "liver_disease") else 0
    score += 10 if _bool_input(inputs, "congestive_heart_failure") else 0
    score += 10 if _bool_input(inputs, "cerebrovascular_disease") else 0
    score += 10 if _bool_input(inputs, "renal_disease") else 0
    score += 20 if _bool_input(inputs, "altered_mental_status") else 0
    score += 20 if number(inputs, "respiratory_rate") >= 30 else 0
    score += 20 if number(inputs, "systolic_bp") < 90 else 0
    temperature_c = number(inputs, "temperature_c")
    score += 15 if temperature_c < 35 or temperature_c >= 40 else 0
    score += 10 if number(inputs, "pulse") >= 125 else 0
    score += 30 if number(inputs, "arterial_ph") < 7.35 else 0
    score += 20 if number(inputs, "bun_mg_dl") >= 30 else 0
    score += 20 if number(inputs, "sodium_mEq_l") < 130 else 0
    score += 10 if number(inputs, "glucose_mg_dl") >= 250 else 0
    score += 10 if number(inputs, "hematocrit_percent") < 30 else 0
    low_oxygen = False
    if "pao2_mm_hg" in inputs:
        low_oxygen = number(inputs, "pao2_mm_hg") < 60
    if "oxygen_saturation_percent" in inputs:
        low_oxygen = low_oxygen or number(inputs, "oxygen_saturation_percent") < 90
    score += 10 if low_oxygen else 0
    score += 10 if _bool_input(inputs, "pleural_effusion") else 0

    if score <= 70:
        risk_class = "II"
        mortality = "0.6%"
    elif score <= 90:
        risk_class = "III"
        mortality = "0.9%"
    elif score <= 130:
        risk_class = "IV"
        mortality = "9.3%"
    else:
        risk_class = "V"
        mortality = "27.0%"

    low_risk_screen = (
        number(inputs, "age_years") <= 50
        and not any(
            _bool_input(inputs, key)
            for key in (
                "neoplastic_disease",
                "liver_disease",
                "congestive_heart_failure",
                "cerebrovascular_disease",
                "renal_disease",
                "altered_mental_status",
            )
        )
        and number(inputs, "respiratory_rate") < 30
        and number(inputs, "systolic_bp") >= 90
        and 35 <= temperature_c < 40
        and number(inputs, "pulse") < 125
    )
    if low_risk_screen:
        risk_class = "I"
        mortality = "0.1%"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "risk_class": risk_class, "mortality": mortality},
        unit="points",
        interpretation=f"PSI/PORT risk class {risk_class}, approximate mortality {mortality}.",
    )


def hemoglobin_corrected_dlco(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = _sex(inputs)
    age = number(inputs, "age_years")
    hemoglobin = number(inputs, "hemoglobin_g_dl")
    predicted_dlco = number(inputs, "predicted_dlco")
    if hemoglobin <= 0:
        raise ValueError("hemoglobin_g_dl must be positive")

    coefficient = 10.22 if sex == "male" and age >= 15 else 9.38
    value = predicted_dlco * (1.7 * hemoglobin / (coefficient + hemoglobin))
    return result(metadata, value, "same as input DLCO", "hemoglobin-corrected predicted DLCO")


def cat_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _score_items(inputs, count=8, minimum=0, maximum=5)
    impact = _range_label(
        value,
        (
            (0, 9, "low impact"),
            (10, 20, "medium impact"),
            (21, 30, "high impact"),
            (31, 40, "very high impact"),
        ),
    )

    return result(metadata, value, "points", f"CAT symptom burden: {impact}.")


def asthma_control_test_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _score_items(inputs, count=5, minimum=1, maximum=5)
    if value >= 20:
        control = "well controlled"
    elif value >= 16:
        control = "not well controlled"
    else:
        control = "very poorly controlled"

    return result(metadata, value, "points", f"Asthma Control Test: {control}.")


def berlin_questionnaire_sleep_apnea_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    positive_categories = sum(
        1
        for key in (
            "category_1_positive",
            "category_2_positive",
            "category_3_positive",
        )
        if _bool_input(inputs, key)
    )
    risk = "high" if positive_categories >= 2 else "low"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"positive_categories": positive_categories, "risk": risk},
        unit="categories",
        interpretation=(
            f"Berlin Questionnaire OSA risk: {risk}; "
            f"{positive_categories} of 3 pre-scored categories positive."
        ),
    )


def rhinitis_control_assessment_test_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    value = _score_items(inputs, count=6, minimum=1, maximum=5)
    control = "not well controlled" if value <= 21 else "well controlled"
    return result(metadata, value, "points", f"Rhinitis Control Assessment Test: {control}.")


def childhood_asthma_control_test_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _score_items(inputs, count=7, minimum=0, maximum=5)
    control = "may be well controlled" if value >= 20 else "not well controlled"
    return result(metadata, value, "points", f"Childhood Asthma Control Test: {control}.")


def mmrc_dyspnea_grade(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _integer_input(inputs, "grade", 0, 4)
    label = (
        "breathless only with strenuous exercise",
        "short of breath when hurrying or walking up a slight hill",
        "walks slower than peers or stops for breath at own pace",
        "stops for breath after about 100 m or a few minutes",
        "too breathless to leave the house or breathless when dressing",
    )[value]

    return result(metadata, value, "points", f"mMRC grade {value}: {label}.")


def predicted_postoperative_fev1_perfusion(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    preoperative_fev1_l = number(inputs, "preoperative_fev1_l")
    fraction_perfusion_removed = number(inputs, "fraction_perfusion_removed")
    if not 0 <= fraction_perfusion_removed <= 1:
        raise ValueError("fraction_perfusion_removed must be between 0 and 1")

    value = preoperative_fev1_l * (1 - fraction_perfusion_removed)
    return result(metadata, value, "L", "predicted postoperative FEV1 by perfusion method")


def predicted_postoperative_fev1_anatomic(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    preoperative_fev1_l = number(inputs, "preoperative_fev1_l")
    segments_removed = number(inputs, "segments_removed")
    total_segments = float(inputs.get("total_segments", 19))
    if total_segments <= 0:
        raise ValueError("total_segments must be greater than 0")
    if segments_removed < 0 or segments_removed > total_segments:
        raise ValueError("segments_removed must be between 0 and total_segments")

    value = preoperative_fev1_l * (1 - segments_removed / total_segments)
    return result(metadata, value, "L", "predicted postoperative FEV1 by anatomic method")


def decaf_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    emrcd_grade = _text_choice(inputs, "emrcd_grade", {"1", "2", "3", "4", "5a", "5b"})
    eosinophils = number(inputs, "eosinophils_10e9_l")
    arterial_ph = number(inputs, "arterial_ph")
    if eosinophils < 0:
        raise ValueError("eosinophils_10e9_l must be greater than or equal to 0")

    score = 0
    if emrcd_grade == "5a":
        score += 1
    elif emrcd_grade == "5b":
        score += 2
    if eosinophils < 0.05:
        score += 1
    if _bool_input(inputs, "consolidation"):
        score += 1
    if arterial_ph < 7.30:
        score += 1
    if _bool_input(inputs, "atrial_fibrillation"):
        score += 1

    if score <= 1:
        risk_group = "low"
    elif score == 2:
        risk_group = "intermediate"
    else:
        risk_group = "high"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "risk_group": risk_group},
        unit="points",
        interpretation=f"DECAF score {score}: {risk_group} in-hospital mortality risk group.",
    )


def gap_index_ipf(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = number(inputs, "age_years")
    if age < 0:
        raise ValueError("age_years must be greater than or equal to 0")
    sex = _sex(inputs)
    fvc = number(inputs, "fvc_percent_predicted")
    if fvc < 0:
        raise ValueError("fvc_percent_predicted must be greater than or equal to 0")

    score = 0
    score += 1 if sex == "male" else 0

    if age > 65:
        score += 2
    elif age >= 61:
        score += 1

    if fvc < 50:
        score += 2
    elif fvc <= 75:
        score += 1

    if _bool_input_default(inputs, "dlco_unable", False):
        score += 3
    else:
        dlco = number(inputs, "dlco_percent_predicted")
        if dlco < 0:
            raise ValueError("dlco_percent_predicted must be greater than or equal to 0")
        if dlco <= 35:
            score += 2
        elif dlco <= 55:
            score += 1

    if score <= 3:
        stage = "I"
    elif score <= 5:
        stage = "II"
    else:
        stage = "III"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "stage": stage},
        unit="points",
        interpretation=f"GAP index for IPF score {score}: stage {stage}.",
    )


__all__ = [
    "asthma_control_test_score",
    "berlin_questionnaire_sleep_apnea_risk",
    "bode_index",
    "cat_score",
    "childhood_asthma_control_test_score",
    "decaf_score",
    "gap_index_ipf",
    "hemoglobin_corrected_dlco",
    "mmrc_dyspnea_grade",
    "pneumonia_severity_index",
    "predicted_postoperative_fev1_anatomic",
    "predicted_postoperative_fev1_perfusion",
    "rhinitis_control_assessment_test_score",
    "stop_bang_sleep_apnea_screening",
]
