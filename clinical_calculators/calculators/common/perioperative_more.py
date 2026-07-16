from __future__ import annotations

import math
from collections.abc import Sequence
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


def _nonnegative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return value


def _choice(inputs: dict[str, Any], key: str, allowed: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{key} must be one of: {allowed_values}")
    return value


def _integer_in_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _coded_component_points(
    inputs: dict[str, Any], key: str, expected_count: int, allowed_points: set[int]
) -> list[int]:
    raw = inputs.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{key} must be a sequence of coded component point values")
    if len(raw) != expected_count:
        raise ValueError(f"{key} must contain {expected_count} coded component point values")

    points = []
    for index, value in enumerate(raw):
        if isinstance(value, bool):
            raise ValueError(f"{key}[{index}] must be a coded integer point value")
        numeric_value = float(value)
        if not numeric_value.is_integer() or int(numeric_value) not in allowed_points:
            allowed = ", ".join(str(point) for point in sorted(allowed_points))
            raise ValueError(f"{key}[{index}] must be one of: {allowed}")
        points.append(int(numeric_value))
    return points


def _possum_component_scores(inputs: dict[str, Any]) -> tuple[int, int]:
    physiological_score = sum(
        _coded_component_points(inputs, "physiological_component_points", 12, {1, 2, 4, 8})
    )
    operative_score = sum(_coded_component_points(inputs, "operative_component_points", 6, {1, 2, 4, 8}))
    return physiological_score, operative_score


def _logistic_percent(logit: float) -> float:
    return round(100 / (1 + math.exp(-logit)), 1)


def _classification_result(
    metadata: CalculatorMetadata, value: Any, unit: str, interpretation: str
) -> CalculationResult:
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit=unit,
        interpretation=interpretation,
    )


def rcri_perioperative_cardiac_risk_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    risk_factor_keys = (
        "high_risk_surgery",
        "ischemic_heart_disease",
        "congestive_heart_failure",
        "cerebrovascular_disease",
        "insulin_treated_diabetes",
        "creatinine_gt_2_mg_dl",
    )
    score = sum(1 for key in risk_factor_keys if _boolean_flag(inputs, key))

    if score == 0:
        risk_class = "class I"
    elif score == 1:
        risk_class = "class II"
    elif score == 2:
        risk_class = "class III"
    else:
        risk_class = "class IV"

    return result(metadata, score, "points", f"RCRI perioperative cardiac risk: {risk_class}.")


def ariscat_postoperative_pulmonary_complications_risk(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = _nonnegative_number(inputs, "age_years")
    spo2_percent = _nonnegative_number(inputs, "spo2_percent")
    duration_hours = _nonnegative_number(inputs, "duration_hours")

    score = 0
    if age_years > 80:
        score += 16
    elif age_years >= 51:
        score += 3

    if spo2_percent <= 90:
        score += 24
    elif spo2_percent <= 95:
        score += 8

    if _boolean_flag(inputs, "respiratory_infection_last_month"):
        score += 17
    if _boolean_flag(inputs, "preoperative_anemia_hb_le_10"):
        score += 11

    incision_points = {
        "peripheral": 0,
        "upper_abdominal": 15,
        "intrathoracic": 24,
    }
    score += incision_points[_choice(inputs, "surgical_incision", set(incision_points))]

    if duration_hours > 3:
        score += 23
    elif duration_hours >= 2:
        score += 16

    if _boolean_flag(inputs, "emergency_surgery"):
        score += 8

    if score >= 45:
        risk = "high"
    elif score >= 26:
        risk = "intermediate"
    else:
        risk = "low"

    return result(metadata, score, "points", f"ARISCAT postoperative pulmonary complication risk: {risk}.")


def caprini_vte_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "risk_factor_points" not in inputs:
        raise KeyError("risk_factor_points")

    risk_factor_points = inputs["risk_factor_points"]
    if isinstance(risk_factor_points, (str, bytes)) or not hasattr(risk_factor_points, "__iter__"):
        raise ValueError("risk_factor_points must be a list of coded point values")

    score = 0
    allowed_points = {1, 2, 3, 5}
    for point in risk_factor_points:
        if isinstance(point, bool):
            raise ValueError("risk_factor_points items must be coded point values in {1, 2, 3, 5}")
        numeric_point = float(point)
        if not numeric_point.is_integer() or int(numeric_point) not in allowed_points:
            raise ValueError("risk_factor_points items must be coded point values in {1, 2, 3, 5}")
        score += int(numeric_point)

    if score >= 5:
        risk = "high"
    elif score >= 3:
        risk = "moderate"
    elif score >= 1:
        risk = "low"
    else:
        risk = "very low"

    return result(metadata, score, "points", f"Caprini VTE risk: {risk}.")


def clavien_dindo_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    death = _boolean_flag(inputs, "death")
    icu_management = _boolean_flag(inputs, "icu_management")
    organ_dysfunction = _choice(inputs, "organ_dysfunction", {"none", "single", "multiple"})
    intervention = _choice(
        inputs,
        "intervention",
        {"none", "without_general_anesthesia", "with_general_anesthesia"},
    )
    grade_ii_therapy = _boolean_flag(inputs, "grade_ii_therapy")
    disability_suffix = _boolean_flag(inputs, "disability_at_discharge")

    if not death:
        if icu_management and organ_dysfunction == "none":
            raise ValueError("icu_management requires single or multiple organ_dysfunction")
        if organ_dysfunction != "none" and not icu_management:
            raise ValueError("organ_dysfunction requires icu_management for Clavien-Dindo grade IV")

    if death:
        grade = "V"
        ordinal = 5
        label = "death"
    elif organ_dysfunction == "multiple":
        grade = "IVb"
        ordinal = 4
        label = "life-threatening complication with multiorgan dysfunction requiring ICU management"
    elif organ_dysfunction == "single":
        grade = "IVa"
        ordinal = 4
        label = "life-threatening complication with single-organ dysfunction requiring ICU management"
    elif intervention == "with_general_anesthesia":
        grade = "IIIb"
        ordinal = 3
        label = "intervention under general anesthesia"
    elif intervention == "without_general_anesthesia":
        grade = "IIIa"
        ordinal = 3
        label = "surgical, endoscopic, or radiological intervention without general anesthesia"
    elif grade_ii_therapy:
        grade = "II"
        ordinal = 2
        label = "grade II therapy such as pharmacologic treatment beyond grade I medications, transfusion, or parenteral nutrition"
    else:
        grade = "I"
        ordinal = 1
        label = "deviation from normal postoperative course without higher-grade therapy"

    suffix = "d" if disability_suffix else ""
    displayed_grade = f"{grade}{suffix}"
    return _classification_result(
        metadata,
        {"grade": grade, "ordinal": ordinal, "disability_suffix": disability_suffix},
        "classification",
        f"Clavien-Dindo Grade {displayed_grade}: {label}.",
    )


def lemon_airway_assessment(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    component_keys = (
        "look_external_abnormal",
        "evaluate_332_abnormal",
        "mallampati_ge_3",
        "obstruction_present",
        "neck_mobility_limited",
    )
    score = sum(1 for key in component_keys if _boolean_flag(inputs, key))
    return result(
        metadata,
        score,
        "features",
        f"LEMON airway assessment: {score} of 5 difficult-airway risk features present; no universal cutoff is applied.",
    )


def cormack_lehane_laryngoscopy_grade(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 1, 4)
    labels = {
        1: "full view of the glottis",
        2: "partial view of the glottis",
        3: "only epiglottis visible",
        4: "neither glottis nor epiglottis visible",
    }
    difficult_laryngoscopy = grade >= 3

    return _classification_result(
        metadata,
        {"grade": grade, "difficult_laryngoscopy": difficult_laryngoscopy},
        "grade",
        f"Cormack-Lehane Grade {grade}: {labels[grade]}.",
    )


def possum_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    physiological_score, operative_score = _possum_component_scores(inputs)
    morbidity_logit = -5.91 + (0.16 * physiological_score) + (0.19 * operative_score)
    mortality_logit = -7.04 + (0.13 * physiological_score) + (0.16 * operative_score)
    value = {
        "physiological_score": physiological_score,
        "operative_score": operative_score,
        "morbidity_risk_percent": _logistic_percent(morbidity_logit),
        "mortality_risk_percent": _logistic_percent(mortality_logit),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="risk",
        interpretation="POSSUM morbidity and mortality estimates from pre-scored physiological and operative components.",
    )


def p_possum_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    physiological_score, operative_score = _possum_component_scores(inputs)
    mortality_logit = -9.065 + (0.1692 * physiological_score) + (0.1550 * operative_score)
    value = {
        "physiological_score": physiological_score,
        "operative_score": operative_score,
        "mortality_risk_percent": _logistic_percent(mortality_logit),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="risk",
        interpretation="P-POSSUM mortality estimate from the Portsmouth logistic equation.",
    )


def comprehensive_complication_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw = inputs.get("complication_grades")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("complication_grades must be a sequence of Clavien-Dindo grade codes")

    weights = {
        "I": 8.7,
        "II": 20.9,
        "IIIa": 26.2,
        "IIIb": 33.7,
        "IVa": 42.4,
        "IVb": 46.2,
        "V": 100.0,
    }
    grades = [str(grade).strip() for grade in raw]
    if any(grade not in weights for grade in grades):
        allowed = ", ".join(weights)
        raise ValueError(f"complication_grades items must be one of: {allowed}")

    if "V" in grades:
        score = 100.0
    else:
        score = round(math.sqrt(sum(weights[grade] ** 2 for grade in grades)), 1)

    value = {"score": score, "complication_count": len(grades)}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"Comprehensive Complication Index {score:g} on a 0-100 scale.",
    )


def eras_compliance_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    raw = inputs.get("items")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("items must be a sequence of true/false/None ERAS element statuses")

    applicable = 0
    completed = 0
    for index, item in enumerate(raw):
        if item is None:
            continue
        if not isinstance(item, bool):
            raise ValueError(f"items[{index}] must be True, False, or None")
        applicable += 1
        completed += int(item)

    if applicable == 0:
        raise ValueError("at least one ERAS item must be applicable")

    compliance = round((completed / applicable) * 100, 1)
    label = "high compliance" if compliance >= 80 else "below high-compliance threshold"
    value = {
        "completed_items": completed,
        "applicable_items": applicable,
        "compliance_percent": compliance,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="percent",
        interpretation=f"ERAS compliance {compliance:g}%: {label}.",
    )
