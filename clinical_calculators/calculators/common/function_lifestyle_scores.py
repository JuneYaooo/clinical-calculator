from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


BARTHEL_DOMAINS = {
    "feeding",
    "bathing",
    "grooming",
    "dressing",
    "bowels",
    "bladder",
    "toilet_use",
    "transfers",
    "mobility",
    "stairs",
}
BARTHEL_DOMAIN_VALUES = {
    "feeding": (0, 5, 10),
    "bathing": (0, 5),
    "grooming": (0, 5),
    "dressing": (0, 5, 10),
    "bowels": (0, 5, 10),
    "bladder": (0, 5, 10),
    "toilet_use": (0, 5, 10),
    "transfers": (0, 5, 10, 15),
    "mobility": (0, 5, 10, 15),
    "stairs": (0, 5, 10),
}


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
    value = number(inputs, key)
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum:g} and {maximum:g}")
    return value


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


def _nonnegative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
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


def _score_items(inputs: dict[str, Any], count: int, minimum: int, maximum: int, key: str = "items") -> list[int]:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    scores = []
    for index, value in enumerate(values):
        item_key = f"{key}[{index}]"
        score = _integer_value(value, item_key)
        if score < minimum or score > maximum:
            raise ValueError(f"{item_key} must be between {minimum} and {maximum}")
        scores.append(score)
    return scores


def _prescored_items(
    inputs: dict[str, Any],
    count: int,
    minimum: int,
    maximum: int,
    key: str,
    *,
    allow_missing: bool = False,
) -> list[int]:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    scores = []
    for index, value in enumerate(values):
        item_key = f"{key}[{index}]"
        if value is None:
            if allow_missing:
                continue
            raise ValueError(f"{item_key} must be between {minimum} and {maximum}")
        score = _integer_value(value, item_key)
        if score < minimum or score > maximum:
            raise ValueError(f"{item_key} must be between {minimum} and {maximum}")
        scores.append(score)
    return scores


def _nonnegative_score_items(inputs: dict[str, Any], count: int, key: str = "items") -> list[int]:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    scores = []
    for index, value in enumerate(values):
        item_key = f"{key}[{index}]"
        score = _integer_value(value, item_key)
        if score < 0:
            raise ValueError(f"{item_key} must be nonnegative")
        scores.append(score)
    return scores


def _coded_boolean_items(inputs: dict[str, Any], count: int, key: str = "items") -> list[bool]:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} coded boolean values")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} coded boolean values")

    coded_items = []
    for index, value in enumerate(values):
        if isinstance(value, bool):
            coded_items.append(value)
        elif value == 0 or value == 1:
            coded_items.append(bool(value))
        else:
            raise ValueError(f"{key}[{index}] must be a bool or 0/1")
    return coded_items


def _range_label(score: int, ranges: tuple[tuple[int, int, str], ...]) -> str:
    for minimum, maximum, label in ranges:
        if minimum <= score <= maximum:
            return label
    raise ValueError("score is outside the supported interpretation range")


def _barthel_items(inputs: dict[str, Any]) -> dict[str, int]:
    if "items" not in inputs:
        raise KeyError("items")

    items = inputs["items"]
    if not isinstance(items, Mapping):
        raise ValueError("items must be a mapping of 10 Barthel domain scores")

    domain_keys = set(items.keys())
    if domain_keys != BARTHEL_DOMAINS:
        raise ValueError(f"items must contain exactly these domains: {sorted(BARTHEL_DOMAINS)}")

    scores = {}
    for domain, value in items.items():
        score = _integer_value(value, f"items[{domain}]")
        if score not in BARTHEL_DOMAIN_VALUES[domain]:
            raise ValueError(f"items[{domain}] must be one of {sorted(BARTHEL_DOMAIN_VALUES[domain])}")
        scores[str(domain)] = score
    return scores


def als_functional_rating_scale_revised(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=12, minimum=0, maximum=4))
    return result(
        metadata,
        score,
        "points",
        "ALSFRS-R: higher function with increasing score; total range 0-48.",
    )


def myasthenia_gravis_activities_of_daily_living(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_score_items(inputs, count=8, minimum=0, maximum=3))
    return result(
        metadata,
        score,
        "points",
        "MG-ADL: higher symptom burden with increasing score; total range 0-24.",
    )


def clinical_frailty_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 1, 9)
    label = _range_label(
        grade,
        (
            (1, 3, "not frail or managing well"),
            (4, 4, "vulnerable"),
            (5, 5, "mild frailty"),
            (6, 6, "moderate frailty"),
            (7, 8, "severe frailty"),
            (9, 9, "terminally ill"),
        ),
    )
    return result(metadata, grade, "grade", f"Clinical Frailty Scale grade {grade}: {label}.")


def edmonton_frail_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 0, 17)
    label = _range_label(
        score,
        (
            (0, 5, "not frail"),
            (6, 7, "apparently vulnerable"),
            (8, 9, "mild frailty"),
            (10, 11, "moderate frailty"),
            (12, 17, "severe frailty"),
        ),
    )
    return result(metadata, score, "points", f"Edmonton Frail Scale: {label}.")


def adverse_childhood_experiences_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(1 for item in _coded_boolean_items(inputs, count=10) if item)
    if score >= 4:
        label = "higher cumulative exposure"
    elif score > 0:
        label = "some cumulative exposure"
    else:
        label = "no coded ACE exposure"
    return result(metadata, score, "count", f"ACE score: {label}; total range 0-10.")


def barthel_activities_of_daily_living_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_barthel_items(inputs).values())
    if score > 100:
        raise ValueError("Barthel total score must be between 0 and 100")

    label = _range_label(
        score,
        (
            (0, 20, "total dependence"),
            (21, 60, "severe dependence"),
            (61, 90, "moderate dependence"),
            (91, 99, "slight dependence"),
            (100, 100, "independent"),
        ),
    )
    return result(metadata, score, "points", f"Barthel Index: {label}.")


def berg_balance_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=14, minimum=0, maximum=4))
    fall_risk = "greater fall risk" if score < 45 else "not below the 45-point fall-risk cutoff"
    return result(metadata, score, "points", f"Berg Balance Scale: {fall_risk}.")


def functional_independence_measure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=18, minimum=1, maximum=7))
    interpretation = "Functional Independence Measure: higher independence with increasing score."
    return result(metadata, score, "points", interpretation)


def waterlow_pressure_ulcer_risk_score_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    scores = _nonnegative_score_items(inputs, count=len(inputs.get("component_points", ())), key="component_points")
    if not scores:
        raise ValueError("component_points must contain at least one pre-scored component")

    score = sum(scores)
    if score >= 20:
        risk = "very high risk"
    elif score >= 15:
        risk = "high risk"
    elif score >= 10:
        risk = "at risk"
    else:
        risk = "below Waterlow 10+ at-risk threshold"

    return result(metadata, score, "points", f"Waterlow pressure ulcer risk score: {risk}.")


def functional_ambulation_category(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 0, 5)
    labels = {
        0: "nonfunctional ambulation",
        1: "dependent ambulation with continuous assistance",
        2: "dependent ambulation with intermittent assistance",
        3: "supervised ambulation",
        4: "independent ambulation on level surfaces",
        5: "independent ambulation",
    }
    return result(metadata, grade, "category", f"Functional Ambulation Category {grade}: {labels[grade]}.")


def timed_up_and_go_test(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    seconds = _positive_number(inputs, "seconds")
    risk = "fall risk threshold met for older adults" if seconds >= 12 else "below older-adult fall-risk threshold"
    return result(metadata, seconds, "seconds", f"Timed Up and Go Test: {risk}.")


def tinetti_poma(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    balance_score = _integer_in_range(inputs, "balance_score", 0, 16)
    gait_score = _integer_in_range(inputs, "gait_score", 0, 12)
    total_score = balance_score + gait_score
    risk = _range_label(
        total_score,
        (
            (0, 18, "high fall risk"),
            (19, 24, "medium fall risk"),
            (25, 28, "low fall risk"),
        ),
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"total_score": total_score, "balance_score": balance_score, "gait_score": gait_score},
        unit="points",
        interpretation=f"Tinetti POMA: {risk}.",
    )


def bone_mineral_density_t_score_interpretation(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    t_score = number(inputs, "t_score")
    fragility_fracture = _bool_input(inputs, "fragility_fracture")
    if t_score >= -1.0:
        classification = "normal bone density"
    elif t_score > -2.5:
        classification = "low bone mass"
    elif fragility_fracture:
        classification = "severe osteoporosis"
    else:
        classification = "osteoporosis"
    value = {"t_score": round(t_score, 4), "classification": classification, "fragility_fracture": fragility_fracture}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="T-score",
        interpretation=f"BMD T-score interpretation: {classification}.",
    )


def community_periodontal_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw_codes = inputs.get("sextant_codes")
    if isinstance(raw_codes, (str, bytes)) or not isinstance(raw_codes, Sequence):
        raise ValueError("sextant_codes must be a sequence of CPI sextant codes")
    if not raw_codes:
        raise ValueError("sextant_codes must contain at least one code")

    codes = []
    for index, raw_code in enumerate(raw_codes):
        code = _integer_value(raw_code, f"sextant_codes[{index}]")
        if code < 0 or code > 4:
            raise ValueError(f"sextant_codes[{index}] must be between 0 and 4")
        codes.append(code)

    highest = max(codes)
    labels = {
        0: "healthy periodontal finding",
        1: "bleeding observed",
        2: "calculus detected",
        3: "periodontal pocket 4-5 mm",
        4: "periodontal pocket 6 mm or deeper",
    }
    return result(metadata, highest, "code", f"Community Periodontal Index code {highest}: {labels[highest]}.")


def modified_rankin_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 0, 6)
    labels = {
        0: "no symptoms",
        1: "no significant disability",
        2: "slight disability",
        3: "moderate disability",
        4: "moderately severe disability",
        5: "severe disability",
        6: "dead",
    }
    return result(metadata, grade, "grade", f"Modified Rankin Scale grade {grade}: {labels[grade]}.")


def sarc_f_sarcopenia_screen(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=5, minimum=0, maximum=2))
    classification = "risk positive" if score >= 4 else "risk negative"
    return result(metadata, score, "points", f"SARC-F sarcopenia screen: {classification}.")


def perceived_stress_scale_10(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=10, minimum=0, maximum=4))
    label = _range_label(
        score,
        (
            (0, 13, "low perceived stress"),
            (14, 26, "moderate perceived stress"),
            (27, 40, "high perceived stress"),
        ),
    )
    return result(metadata, score, "points", f"PSS-10: {label}.")


def fagerstrom_nicotine_dependence_test(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_nonnegative_score_items(inputs, count=6))
    if score > 10:
        raise ValueError("Fagerstrom total score must be between 0 and 10")

    label = _range_label(
        score,
        (
            (0, 2, "very low nicotine dependence"),
            (3, 4, "low nicotine dependence"),
            (5, 5, "medium nicotine dependence"),
            (6, 7, "high nicotine dependence"),
            (8, 10, "very high nicotine dependence"),
        ),
    )
    return result(metadata, score, "points", f"Fagerstrom nicotine dependence: {label}.")


def gold_hypoglycemia_awareness_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _integer_in_range(inputs, "score", 1, 7)
    classification = "impaired awareness" if score >= 4 else "normal awareness"
    return result(metadata, score, "points", f"Gold hypoglycemia awareness score: {classification}.")


def six_minute_walk_distance_predicted(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    age = number(inputs, "age_years")
    height = number(inputs, "height_cm")
    weight = number(inputs, "weight_kg")
    if sex == "male":
        predicted = (7.57 * height) - (5.02 * age) - (1.76 * weight) - 309
    else:
        predicted = (2.11 * height) - (2.29 * weight) - (5.78 * age) + 667
    if predicted <= 0:
        raise ValueError("predicted 6MWD must be positive")

    observed = number(inputs, "observed_6mwd_m") if "observed_6mwd_m" in inputs else None
    value: dict[str, float] = {"predicted_6mwd_m": round(predicted, 4)}
    if observed is not None:
        value["percent_predicted"] = round(100 * observed / predicted, 4)

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="m",
        interpretation="six-minute walk distance predicted by age, height, weight, and sex",
    )


def charlson_comorbidity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    condition_weights = {
        "myocardial_infarction": 1,
        "congestive_heart_failure": 1,
        "peripheral_vascular_disease": 1,
        "cerebrovascular_disease": 1,
        "dementia": 1,
        "chronic_pulmonary_disease": 1,
        "connective_tissue_disease": 1,
        "peptic_ulcer_disease": 1,
        "mild_liver_disease": 1,
        "diabetes_without_end_organ_damage": 1,
        "hemiplegia": 2,
        "moderate_or_severe_renal_disease": 2,
        "diabetes_with_end_organ_damage": 2,
        "localized_solid_tumor": 2,
        "leukemia": 2,
        "lymphoma": 2,
        "moderate_or_severe_liver_disease": 3,
        "metastatic_solid_tumor": 6,
        "aids": 6,
    }
    score = sum(weight for key, weight in condition_weights.items() if _bool_input(inputs, key))

    age = _nonnegative_number(inputs, "age_years")
    if age < 50:
        age_points = 0
    elif age < 60:
        age_points = 1
    elif age < 70:
        age_points = 2
    elif age < 80:
        age_points = 3
    else:
        age_points = 4

    total = score + age_points
    value = {"score": total, "condition_points": score, "age_points": age_points}
    interpretation = "Charlson Comorbidity Index: higher comorbidity burden with increasing score."
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=interpretation,
    )


def waist_to_hip_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    ratio = _positive_number(inputs, "waist_cm") / _positive_number(inputs, "hip_cm")
    cutoff = 0.9 if sex == "male" else 0.85
    interpretation = (
        "WHO waist-to-hip ratio: increased central adiposity risk."
        if ratio >= cutoff
        else "WHO waist-to-hip ratio: below increased-risk cutoff."
    )
    return result(metadata, ratio, "ratio", interpretation)


def waist_to_height_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ratio = _positive_number(inputs, "waist_cm") / _positive_number(inputs, "height_cm")
    if ratio >= 0.6:
        category = "high central adiposity risk"
    elif ratio >= 0.5:
        category = "increased central adiposity risk"
    else:
        category = "below increased-risk cutoff"
    return result(metadata, ratio, "ratio", f"NICE waist-to-height ratio: {category}.")


def norton_pressure_ulcer_risk_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _integer_in_range(inputs, key, 1, 4)
        for key in (
            "physical_condition",
            "mental_condition",
            "activity",
            "mobility",
            "incontinence",
        )
    )
    if score <= 12:
        risk = "high pressure ulcer risk"
    elif score <= 14:
        risk = "pressure ulcer risk"
    else:
        risk = "lower pressure ulcer risk"
    return result(metadata, score, "points", f"Norton Scale: {risk}.")


def decayed_missing_filled_teeth_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _integer_in_range(inputs, key, 0, 32)
        for key in ("decayed_teeth", "missing_teeth", "filled_teeth")
    )
    if score > 32:
        raise ValueError("DMFT total cannot exceed 32 permanent teeth")
    return result(metadata, score, "teeth", "DMFT index: decayed + missing + filled permanent teeth.")


def harris_hip_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _number_in_range(inputs, key, 0, maximum)
        for key, maximum in (
            ("pain", 44),
            ("function", 47),
            ("absence_deformity", 4),
            ("range_of_motion", 5),
        )
    )
    label = _range_label(
        score,
        (
            (0, 69, "poor hip function"),
            (70, 79, "fair hip function"),
            (80, 89, "good hip function"),
            (90, 100, "top category hip function"),
        ),
    )
    return result(metadata, score, "points", f"Harris Hip Score: {label}.")


def lysholm_knee_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _integer_in_range(inputs, key, 0, maximum)
        for key, maximum in (
            ("limp", 5),
            ("support", 5),
            ("locking", 15),
            ("instability", 25),
            ("pain", 25),
            ("swelling", 10),
            ("stair_climbing", 10),
            ("squatting", 5),
        )
    )
    label = _range_label(
        score,
        (
            (0, 64, "poor knee function"),
            (65, 83, "fair knee function"),
            (84, 94, "good knee function"),
            (95, 100, "top category knee function"),
        ),
    )
    return result(metadata, score, "points", f"Lysholm Knee Score: {label}.")


def constant_murley_shoulder_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _number_in_range(inputs, key, 0, maximum)
        for key, maximum in (
            ("pain", 15),
            ("activities_of_daily_living", 20),
            ("range_of_motion", 40),
            ("strength", 25),
        )
    )
    label = _range_label(
        score,
        (
            (0, 55, "poor shoulder function"),
            (56, 70, "fair shoulder function"),
            (71, 85, "good shoulder function"),
            (86, 100, "top category shoulder function"),
        ),
    )
    return result(metadata, score, "points", f"Constant-Murley Shoulder Score: {label}.")


def lower_extremity_functional_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=20, minimum=0, maximum=4))
    return result(
        metadata,
        score,
        "points",
        "Lower Extremity Functional Scale: higher lower-extremity function with increasing score.",
    )


def dizziness_handicap_inventory(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    scores = _prescored_items(inputs, count=25, minimum=0, maximum=4, key="item_scores")
    for index, score in enumerate(scores):
        if score not in {0, 2, 4}:
            raise ValueError(f"item_scores[{index}] must be one of [0, 2, 4]")

    total = sum(scores)
    return result(
        metadata,
        total,
        "points",
        "Dizziness Handicap Inventory: higher scores indicate greater perceived dizziness handicap; total range 0-100.",
    )


def oxford_hip_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_prescored_items(inputs, count=12, minimum=0, maximum=4, key="item_scores"))
    return result(
        metadata,
        score,
        "points",
        "Oxford Hip Score: higher scores indicate better hip symptoms/function; total range 0-48.",
    )


def oswestry_disability_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    scores = _prescored_items(
        inputs,
        count=10,
        minimum=0,
        maximum=5,
        key="section_scores",
        allow_missing=True,
    )
    if not scores:
        raise ValueError("section_scores must contain at least one completed section score")

    raw_score = sum(scores)
    score_percent = 100 * raw_score / (5 * len(scores))
    value = {
        "score_percent": round(score_percent, 4),
        "raw_score": raw_score,
        "completed_sections": len(scores),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="percent",
        interpretation="Oswestry Disability Index: higher percentage scores indicate greater low-back disability.",
    )


def neck_disability_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw_score = sum(_prescored_items(inputs, count=10, minimum=0, maximum=5, key="item_scores"))
    value = {
        "raw_score": raw_score,
        "score_percent": round(100 * raw_score / 50, 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="Neck Disability Index: higher scores indicate greater neck-related disability; raw range 0-50.",
    )


def quickdash_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "items" not in inputs:
        raise KeyError("items")

    values = inputs["items"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("items must be a sequence of 11 QuickDASH scores")
    if len(values) != 11:
        raise ValueError("items must contain exactly 11 QuickDASH scores")

    completed: list[int] = []
    for index, value in enumerate(values):
        if value is None:
            continue
        score = _integer_value(value, f"items[{index}]")
        if score < 1 or score > 5:
            raise ValueError(f"items[{index}] must be between 1 and 5")
        completed.append(score)

    if len(completed) < 10:
        raise ValueError("QuickDASH requires at least 10 completed item scores")
    scaled_score = ((sum(completed) / len(completed)) - 1) * 25
    value = {"score": round(scaled_score, 4), "completed_items": len(completed)}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="QuickDASH disability/symptom score: 0 is least disability and 100 is most disability.",
    )


def dash_full_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "items" not in inputs:
        raise KeyError("items")

    values = inputs["items"]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("items must be a sequence of 30 DASH scores")
    if len(values) != 30:
        raise ValueError("items must contain exactly 30 DASH scores")

    completed: list[int] = []
    for index, value in enumerate(values):
        if value is None:
            continue
        score = _integer_value(value, f"items[{index}]")
        if score < 1 or score > 5:
            raise ValueError(f"items[{index}] must be between 1 and 5")
        completed.append(score)

    if len(completed) < 27:
        raise ValueError("DASH requires at least 27 completed item scores")

    scaled_score = ((sum(completed) / len(completed)) - 1) * 25
    value = {"score": round(scaled_score, 4), "completed_items": len(completed)}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="DASH disability/symptom score: higher scores indicate greater disability.",
    )


def _coded_points(inputs: dict[str, Any], key: str, options: Mapping[str, int]) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, str):
        code = value.strip().lower()
        if code not in options:
            raise ValueError(f"{key} must be one of {sorted(options)}")
        return options[code]

    score = _integer_value(value, key)
    if score not in set(options.values()):
        raise ValueError(f"{key} must be a valid coded score")
    return score


def thoracolumbar_injury_classification_severity_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    morphology = _coded_points(
        inputs,
        "morphology",
        {
            "none": 0,
            "compression": 1,
            "burst": 2,
            "translational_rotational": 3,
            "distraction": 4,
        },
    )
    posterior_ligamentous_complex = _coded_points(
        inputs,
        "posterior_ligamentous_complex",
        {
            "intact": 0,
            "suspected_indeterminate": 2,
            "injured": 3,
        },
    )
    neurologic_status = _coded_points(
        inputs,
        "neurologic_status",
        {
            "intact": 0,
            "nerve_root": 2,
            "complete_cord": 2,
            "incomplete_cord": 3,
            "cauda_equina": 3,
        },
    )
    total = morphology + posterior_ligamentous_complex + neurologic_status
    if total <= 3:
        recommendation = "nonoperative treatment"
    elif total == 4:
        recommendation = "nonoperative or operative treatment"
    else:
        recommendation = "operative treatment"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total,
            "morphology_points": morphology,
            "posterior_ligamentous_complex_points": posterior_ligamentous_complex,
            "neurologic_status_points": neurologic_status,
        },
        unit="points",
        interpretation=f"TLICS: {recommendation}; use with imaging and clinical judgment.",
    )


def spinal_instability_neoplastic_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    location = _coded_points(
        inputs,
        "location",
        {
            "rigid": 0,
            "semirigid": 1,
            "mobile": 2,
            "junctional": 3,
        },
    )
    pain = _coded_points(
        inputs,
        "pain",
        {
            "none": 0,
            "painless": 0,
            "occasional_nonmechanical": 1,
            "mechanical": 3,
        },
    )
    bone_lesion = _coded_points(
        inputs,
        "bone_lesion",
        {
            "blastic": 0,
            "mixed": 1,
            "lytic": 2,
        },
    )
    alignment = _coded_points(
        inputs,
        "alignment",
        {
            "normal": 0,
            "de_novo_deformity": 2,
            "subluxation_translation": 4,
        },
    )
    vertebral_body_collapse = _coded_points(
        inputs,
        "vertebral_body_collapse",
        {
            "none": 0,
            "no_collapse_greater_than_50_percent_body_involved": 1,
            "less_than_50_percent": 2,
            "greater_than_50_percent": 3,
        },
    )
    posterolateral_involvement = _coded_points(
        inputs,
        "posterolateral_involvement",
        {
            "none": 0,
            "unilateral": 1,
            "bilateral": 3,
        },
    )
    total = (
        location
        + pain
        + bone_lesion
        + alignment
        + vertebral_body_collapse
        + posterolateral_involvement
    )
    classification = _range_label(
        total,
        (
            (0, 6, "stable"),
            (7, 12, "potentially unstable"),
            (13, 18, "unstable"),
        ),
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total,
            "location_points": location,
            "pain_points": pain,
            "bone_lesion_points": bone_lesion,
            "alignment_points": alignment,
            "vertebral_body_collapse_points": vertebral_body_collapse,
            "posterolateral_involvement_points": posterolateral_involvement,
        },
        unit="points",
        interpretation=f"SINS: {classification}; total range 0-18.",
    )


def tegner_activity_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 0, 10)
    if grade == 0:
        label = "sick leave or disability pension because of knee problems"
    elif grade <= 2:
        label = "light work or walking activity level"
    elif grade <= 4:
        label = "moderate work or recreational sport activity level"
    elif grade <= 6:
        label = "heavy work or recreational competitive sport activity level"
    elif grade <= 9:
        label = "competitive sport activity level"
    else:
        label = "elite competitive sport activity level"
    return result(metadata, grade, "grade", f"Tegner Activity Scale grade {grade}: {label}.")


def olerud_molander_ankle_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    component_maximums = {
        "pain": 25,
        "stiffness": 10,
        "swelling": 10,
        "stair_climbing": 10,
        "running": 5,
        "jumping": 5,
        "squatting": 5,
        "supports": 10,
        "work_activities": 20,
    }
    score = sum(_integer_in_range(inputs, key, 0, maximum) for key, maximum in component_maximums.items())
    if score > 100:
        raise ValueError("Olerud-Molander Ankle Score total cannot exceed 100")
    return result(
        metadata,
        score,
        "points",
        "Olerud-Molander Ankle Score: higher scores indicate better ankle function.",
    )


def _optional_scored_items_percent(inputs: dict[str, Any], key: str, expected: int) -> float | None:
    if key not in inputs or inputs[key] is None:
        return None
    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {expected} item scores")
    if len(values) != expected:
        raise ValueError(f"{key} must contain exactly {expected} scores")
    completed = []
    for index, value in enumerate(values):
        if value is None:
            continue
        score = _integer_value(value, f"{key}[{index}]")
        if score < 0 or score > 4:
            raise ValueError(f"{key}[{index}] must be between 0 and 4")
        completed.append(score)
    if not completed:
        return None
    return round(100 * sum(completed) / (4 * len(completed)), 4)


def foot_and_ankle_ability_measure(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    adl_percent = _optional_scored_items_percent(inputs, "adl_items", 21)
    sports_percent = _optional_scored_items_percent(inputs, "sports_items", 8)
    if adl_percent is None and sports_percent is None:
        raise KeyError("adl_items or sports_items")
    value: dict[str, float] = {}
    if adl_percent is not None:
        value["adl_percent"] = adl_percent
    if sports_percent is not None:
        value["sports_percent"] = sports_percent
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="percent",
        interpretation="FAAM: higher percentage scores indicate better foot and ankle ability.",
    )


def kujala_anterior_knee_pain_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    scores = _nonnegative_score_items(inputs, count=10, key="component_points")
    total = sum(scores)
    if total > 100:
        raise ValueError("Kujala Anterior Knee Pain Scale total cannot exceed 100")
    return result(metadata, total, "points", "Kujala anterior knee pain scale: higher scores indicate better function.")


def _visa_score(metadata: CalculatorMetadata, inputs: dict[str, Any], label: str) -> CalculationResult:
    scores = _nonnegative_score_items(inputs, count=8)
    total = sum(scores)
    if total > 100:
        raise ValueError(f"{label} total score cannot exceed 100")
    return result(metadata, total, "points", f"{label}: higher scores indicate better tendon function.")


def visa_achilles_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _visa_score(metadata, inputs, "VISA-A Achilles tendinopathy score")


def visa_patella_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return _visa_score(metadata, inputs, "VISA-P patellar tendinopathy score")


def modified_dental_anxiety_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_score_items(inputs, count=5, minimum=1, maximum=5))
    if score >= 19:
        label = "high dental anxiety range"
    elif score >= 12:
        label = "moderate dental anxiety range"
    else:
        label = "lower dental anxiety range"
    return result(metadata, score, "points", f"Modified Dental Anxiety Scale: {label}; total range 5-25.")


def jaw_functional_limitation_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw_items = inputs.get("items")
    if isinstance(raw_items, (str, bytes)) or not isinstance(raw_items, Sequence):
        raise ValueError("items must be a sequence of 8 or 20 Jaw Functional Limitation Scale scores")
    if len(raw_items) not in {8, 20}:
        raise ValueError("items must contain either 8 or 20 Jaw Functional Limitation Scale scores")
    items = _score_items(inputs, count=len(raw_items), minimum=0, maximum=10)
    total = sum(items)
    value = {
        "total_score": total,
        "mean_score": round(total / len(items), 4),
        "item_count": len(items),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="Jaw Functional Limitation Scale: higher scores indicate greater functional limitation.",
    )


def _surface_scores(inputs: dict[str, Any], key: str = "surface_scores") -> list[int]:
    return _score_items(inputs, count=len(inputs[key]), minimum=0, maximum=3, key=key)


def silness_loe_plaque_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    scores = _surface_scores(inputs)
    if not scores:
        raise ValueError("surface_scores must contain at least one score")
    mean_score = sum(scores) / len(scores)
    return result(metadata, mean_score, "index", "Silness-Loe Plaque Index: mean of coded 0-3 surface scores.")


def loe_silness_gingival_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    scores = _surface_scores(inputs)
    if not scores:
        raise ValueError("surface_scores must contain at least one score")
    mean_score = sum(scores) / len(scores)
    if mean_score == 0:
        label = "no inflammation"
    elif mean_score <= 1:
        label = "mild inflammation"
    elif mean_score <= 2:
        label = "moderate inflammation"
    else:
        label = "severe inflammation"
    return result(metadata, mean_score, "index", f"Loe-Silness Gingival Index: {label}.")
