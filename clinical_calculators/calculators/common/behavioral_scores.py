from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _integer_item(value: Any, key: str, index: int, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key}[{index}] must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key}[{index}] must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key}[{index}] must be between {minimum} and {maximum}")
    return integer_value


def _score_items(inputs: dict[str, Any], count: int, minimum: int, maximum: int, key: str = "items") -> int:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    return sum(_integer_item(value, key, index, minimum, maximum) for index, value in enumerate(values))


def _optional_sex(inputs: dict[str, Any], key: str = "sex") -> str | None:
    if key not in inputs or inputs[key] is None:
        return None

    sex = str(inputs[key]).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female' when provided")
    return sex


def _boolean_input(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value == 0 or value == 1:
        return bool(value)
    raise ValueError(f"{key} must be a bool or 0/1")


def _range_label(score: int, ranges: tuple[tuple[int, int, str], ...]) -> str:
    for minimum, maximum, label in ranges:
        if minimum <= score <= maximum:
            return label
    raise ValueError("score is outside the supported interpretation range")


def columbia_suicide_severity_screen_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "ideation_severity" not in inputs:
        raise KeyError("ideation_severity")
    ideation_severity = _integer_item(inputs["ideation_severity"], "ideation_severity", 0, 0, 5)
    suicidal_behavior = _boolean_input(inputs, "suicidal_behavior")
    recent_behavior = _boolean_input(inputs, "recent_behavior")

    if recent_behavior:
        risk_level = "high_acuity"
        interpretation = "C-SSRS pre-scored screen: high-acuity positive screen; urgent safety assessment is indicated."
    elif suicidal_behavior or ideation_severity >= 4:
        risk_level = "positive"
        interpretation = "C-SSRS pre-scored screen: positive screen; prompt suicide risk assessment is indicated."
    elif ideation_severity > 0:
        risk_level = "nonzero_ideation"
        interpretation = "C-SSRS pre-scored screen: suicidal ideation endorsed without high-acuity behavior code."
    else:
        risk_level = "negative"
        interpretation = "C-SSRS pre-scored screen: no suicidal ideation or behavior coded."

    value = {
        "ideation_severity": ideation_severity,
        "suicidal_behavior": suicidal_behavior,
        "recent_behavior": recent_behavior,
        "risk_level": risk_level,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=interpretation,
    )


def audit_alcohol_use_disorders_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _score_items(inputs, count=10, minimum=0, maximum=4, key="item_scores")
    label = _range_label(
        score,
        (
            (0, 7, "lower-risk range"),
            (8, 15, "hazardous alcohol use range"),
            (16, 19, "harmful alcohol use range"),
            (20, 40, "possible dependence range"),
        ),
    )
    return result(metadata, score, "points", f"AUDIT total score: {label}.")


def geriatric_depression_scale_15(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=15, minimum=0, maximum=1)
    severity = _range_label(
        score,
        (
            (0, 4, "normal range"),
            (5, 8, "mild depression range"),
            (9, 11, "moderate depression range"),
            (12, 15, "severe depression range"),
        ),
    )
    screening_note = "suggestive of depression; diagnostic evaluation is warranted" if score >= 5 else "not suggestive"
    return result(metadata, score, "points", f"GDS-15: {severity}; {screening_note}.")


def confusion_assessment_method(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    feature_1 = _boolean_input(inputs, "acute_onset_or_fluctuating_course")
    feature_2 = _boolean_input(inputs, "inattention")
    feature_3 = _boolean_input(inputs, "disorganized_thinking")
    feature_4 = _boolean_input(inputs, "altered_level_of_consciousness")
    cam_positive = feature_1 and feature_2 and (feature_3 or feature_4)
    value = {
        "cam_positive": cam_positive,
        "features_positive": {
            "acute_onset_or_fluctuating_course": feature_1,
            "inattention": feature_2,
            "disorganized_thinking": feature_3,
            "altered_level_of_consciousness": feature_4,
        },
    }
    classification = "positive" if cam_positive else "negative"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=f"Confusion Assessment Method: {classification} screen for delirium.",
    )


def insomnia_severity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=7, minimum=0, maximum=4)
    severity = _range_label(
        score,
        (
            (0, 7, "no clinically significant insomnia"),
            (8, 14, "subthreshold insomnia"),
            (15, 21, "clinical insomnia, moderate severity"),
            (22, 28, "clinical insomnia, severe"),
        ),
    )
    return result(metadata, score, "points", f"Insomnia Severity Index: {severity}.")


def phq_9_depression_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=9, minimum=0, maximum=3)
    severity = _range_label(
        score,
        (
            (0, 4, "minimal"),
            (5, 9, "mild"),
            (10, 14, "moderate"),
            (15, 19, "moderately severe"),
            (20, 27, "severe"),
        ),
    )

    return result(metadata, score, "points", f"PHQ-9 depression severity: {severity}.")


def gad_7_anxiety_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=7, minimum=0, maximum=3)
    severity = _range_label(
        score,
        (
            (0, 4, "minimal"),
            (5, 9, "mild"),
            (10, 14, "moderate"),
            (15, 21, "severe"),
        ),
    )

    return result(metadata, score, "points", f"GAD-7 anxiety severity: {severity}.")


def audit_c_alcohol_use_screening(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=3, minimum=0, maximum=4)
    sex = _optional_sex(inputs)
    threshold_note = "Common positive screening thresholds are >=4 men or >=3 women."

    if sex is None:
        interpretation = f"AUDIT-C score {score}. {threshold_note}"
    else:
        threshold = 4 if sex == "male" else 3
        classification = "positive" if score >= threshold else "negative"
        interpretation = f"AUDIT-C {classification} screen for {sex}; score {score}. {threshold_note}"

    return result(metadata, score, "points", interpretation)


def epworth_sleepiness_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=8, minimum=0, maximum=3)
    severity = _range_label(
        score,
        (
            (0, 10, "normal range"),
            (11, 12, "mild excessive sleepiness"),
            (13, 15, "moderate excessive sleepiness"),
            (16, 24, "severe excessive sleepiness"),
        ),
    )

    return result(metadata, score, "points", f"Epworth Sleepiness Scale: {severity}.")


def karolinska_sleepiness_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "score" not in inputs:
        raise KeyError("score")
    score = _integer_item(inputs["score"], "score", 0, 1, 9)
    labels = {
        1: "extremely alert",
        2: "very alert",
        3: "alert",
        4: "rather alert",
        5: "neither alert nor sleepy",
        6: "some signs of sleepiness",
        7: "sleepy, no effort to stay awake",
        8: "sleepy, some effort to stay awake",
        9: "very sleepy, great effort to stay awake, fighting sleep",
    }
    return result(metadata, score, "grade", f"Karolinska Sleepiness Scale grade {score}: {labels[score]}.")


def pittsburgh_sleep_quality_index_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _score_items(inputs, count=7, minimum=0, maximum=3, key="component_scores")
    interpretation = (
        "Pittsburgh Sleep Quality Index: poor sleep quality range using the common >5 cutoff."
        if score > 5
        else "Pittsburgh Sleep Quality Index: good sleep quality range using the common >5 cutoff."
    )
    return result(metadata, score, "points", interpretation)


def morningness_eveningness_questionnaire_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "score" not in inputs:
        raise KeyError("score")
    score = _integer_item(inputs["score"], "score", 0, 16, 86)
    preference = _range_label(
        score,
        (
            (16, 30, "definite evening type"),
            (31, 41, "moderate evening type"),
            (42, 58, "intermediate type"),
            (59, 69, "moderate morning type"),
            (70, 86, "definite morning type"),
        ),
    )
    return result(metadata, score, "points", f"Morningness-Eveningness Questionnaire: {preference}.")


def mini_mental_state_examination_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "score" not in inputs:
        raise KeyError("score")
    score = _integer_item(inputs["score"], "score", 0, 0, 30)
    interpretation = (
        "Mini-Mental State Examination: possible cognitive impairment range using the common <24 cutoff; "
        "interpret in clinical, language, and education context."
        if score < 24
        else "Mini-Mental State Examination: common normal screening range; interpret in clinical, language, and education context."
    )
    return result(metadata, score, "points", interpretation)


def clinical_institute_withdrawal_assessment_alcohol_revised_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "component_scores" not in inputs:
        raise KeyError("component_scores")
    values = inputs["component_scores"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("component_scores must be a sequence of 10 CIWA-Ar component scores")
    if len(values) != 10:
        raise ValueError("component_scores must contain exactly 10 scores")

    scores = []
    for index, value in enumerate(values):
        maximum = 4 if index == 9 else 7
        scores.append(_integer_item(value, "component_scores", index, 0, maximum))

    total = sum(scores)
    if total <= 8:
        severity = "minimal or absent withdrawal range"
    elif total <= 15:
        severity = "mild withdrawal range"
    elif total <= 20:
        severity = "moderate withdrawal range"
    else:
        severity = "severe withdrawal range"
    return result(metadata, total, "points", f"CIWA-Ar pre-scored total: {severity}.")


def young_mania_rating_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "component_points" not in inputs:
        raise KeyError("component_points")
    values = inputs["component_points"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("component_points must be a sequence of 11 pre-scored components")
    if len(values) != 11:
        raise ValueError("component_points must contain exactly 11 pre-scored components")
    scores = [_integer_item(value, "component_points", index, 0, 8) for index, value in enumerate(values)]
    total = sum(scores)
    if total > 60:
        raise ValueError("YMRS total score cannot exceed 60")
    return result(metadata, total, "points", "Young Mania Rating Scale: higher scores indicate greater mania severity.")


def madrs_depression_rating_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=10, minimum=0, maximum=6)
    return result(metadata, score, "points", "MADRS total score: higher scores indicate greater depressive symptom severity.")


def yale_brown_obsessive_compulsive_scale(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _score_items(inputs, count=10, minimum=0, maximum=4)
    severity = _range_label(
        score,
        (
            (0, 7, "subclinical"),
            (8, 15, "mild"),
            (16, 23, "moderate"),
            (24, 31, "severe"),
            (32, 40, "extreme"),
        ),
    )
    return result(metadata, score, "points", f"Y-BOCS total score: {severity} obsessive-compulsive symptom range.")


def _panss_subscale(inputs: dict[str, Any], key: str, count: int) -> int:
    if key not in inputs:
        raise KeyError(key)
    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} PANSS item scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")
    return sum(_integer_item(value, key, index, 1, 7) for index, value in enumerate(values))


def panss_prescored(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    positive = _panss_subscale(inputs, "positive_items", 7)
    negative = _panss_subscale(inputs, "negative_items", 7)
    general = _panss_subscale(inputs, "general_items", 16)
    total = positive + negative + general
    value = {
        "positive_score": positive,
        "negative_score": negative,
        "general_score": general,
        "total_score": total,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="PANSS pre-scored subscales and total score; higher scores indicate greater symptom burden.",
    )
