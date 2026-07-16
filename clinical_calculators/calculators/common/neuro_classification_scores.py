from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


NIHSS_ITEM_MAXIMA = (3, 2, 2, 2, 3, 4, 4, 2, 2, 3, 2, 2, 1, 2, 2)
UPDRS_PART_KEYS = ("part_i", "part_ii", "part_iii", "part_iv")


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


def _string_choice(inputs: dict[str, Any], key: str, allowed: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{key} must be one of: {sorted(allowed)}")
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


def _nihss_items(inputs: dict[str, Any]) -> list[int]:
    if "items" not in inputs:
        raise KeyError("items")

    items = inputs["items"]
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence of 15 NIHSS item scores")
    if len(items) != len(NIHSS_ITEM_MAXIMA):
        raise ValueError("items must contain exactly 15 NIHSS item scores")

    scores = []
    for index, (item, maximum) in enumerate(zip(items, NIHSS_ITEM_MAXIMA), start=1):
        if isinstance(item, bool):
            raise ValueError(f"items[{index}] must be an integer from 0 to {maximum}")

        numeric_value = float(item)
        if not numeric_value.is_integer():
            raise ValueError(f"items[{index}] must be an integer from 0 to {maximum}")

        score = int(numeric_value)
        if score < 0 or score > maximum:
            raise ValueError(f"items[{index}] must be between 0 and {maximum}")
        scores.append(score)

    return scores


def _integer_score_items(inputs: dict[str, Any], key: str, count: int, minimum: int, maximum: int) -> list[int]:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    return [_integer_item(value, key, index, minimum, maximum) for index, value in enumerate(values)]


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


def expanded_disability_status_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _number(inputs, "score")
    doubled = score * 2
    if score < 0 or score > 10 or not doubled.is_integer():
        raise ValueError("score must be from 0 to 10 in 0.5-point increments")

    if score == 0:
        label = "normal neurologic examination"
    elif score < 4:
        label = "mild to moderate disability without major walking limitation"
    elif score < 6:
        label = "limited walking ability but ambulatory without constant bilateral assistance"
    elif score < 7:
        label = "walking disability requiring unilateral or bilateral assistance"
    elif score < 8:
        label = "restricted to wheelchair-level mobility"
    else:
        label = "bed or chair restricted disability range"
    return result(metadata, int(score) if score.is_integer() else score, "points", f"EDSS {score:g}: {label}.")


def multiple_sclerosis_functional_composite(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    z_scores = (
        _number(inputs, "timed_25_foot_walk_z"),
        _number(inputs, "nine_hole_peg_test_z"),
        _number(inputs, "cognitive_test_z"),
    )
    score = sum(z_scores) / 3
    return result(
        metadata,
        score,
        "z-score",
        "MSFC composite z-score; higher values indicate higher functional performance relative to the reference set.",
    )


def quantitative_myasthenia_gravis_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = sum(_integer_score_items(inputs, "item_scores", 13, 0, 3))
    return result(metadata, score, "points", "QMG total score; higher weakness burden with increasing score.")


def unified_parkinsons_disease_rating_scale_prescored(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "part_scores" not in inputs:
        raise KeyError("part_scores")
    part_scores = inputs["part_scores"]
    if not isinstance(part_scores, Mapping):
        raise ValueError("part_scores must be a mapping of UPDRS part scores")
    if set(part_scores.keys()) != set(UPDRS_PART_KEYS):
        raise ValueError(f"part_scores must contain exactly these parts: {list(UPDRS_PART_KEYS)}")

    cleaned = {}
    for key in UPDRS_PART_KEYS:
        value = _integer_item(part_scores[key], f"part_scores.{key}", 0, 0, 199)
        cleaned[key] = value
    total = sum(cleaned.values())
    value = {"total_score": total, "part_scores": cleaned}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="UPDRS pre-scored total; higher Parkinson disease burden with increasing score.",
    )


def hoehn_yahr_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if isinstance(inputs.get("stage"), bool):
        raise ValueError("stage must be one of 0, 1, 1.5, 2, 2.5, 3, 4, or 5")
    stage = _number(inputs, "stage")
    allowed = {
        0.0: "no signs of disease",
        1.0: "unilateral disease",
        1.5: "unilateral plus axial involvement",
        2.0: "bilateral disease without impairment of balance",
        2.5: "mild bilateral disease with recovery on pull test",
        3.0: "mild to moderate bilateral disease with some postural instability; physically independent",
        4.0: "severe disability; still able to walk or stand unassisted",
        5.0: "wheelchair bound or bedridden unless aided",
    }
    if stage not in allowed:
        raise ValueError("stage must be one of 0, 1, 1.5, 2, 2.5, 3, 4, or 5")
    value = int(stage) if stage.is_integer() else stage
    return result(metadata, value, "stage", f"Hoehn and Yahr stage {value}: {allowed[stage]}.")


def rapid_arterial_occlusion_evaluation_scale(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    component_maxima = {
        "facial_palsy": 2,
        "arm_motor_function": 2,
        "leg_motor_function": 2,
        "head_and_gaze_deviation": 1,
        "cortical_signs": 2,
    }
    score = sum(_integer_in_range(inputs, key, 0, maximum) for key, maximum in component_maxima.items())
    interpretation = (
        "RACE score meets the commonly used large vessel occlusion screening cutoff."
        if score >= 5
        else "RACE score is below the commonly used large vessel occlusion screening cutoff."
    )
    return result(metadata, score, "points", interpretation)


def nih_stroke_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(_nihss_items(inputs))

    if score == 0:
        interpretation = "NIHSS: no symptoms."
    elif score <= 4:
        interpretation = "NIHSS: minor stroke severity."
    elif score <= 15:
        interpretation = "NIHSS: moderate stroke severity."
    elif score <= 20:
        interpretation = "NIHSS: moderate-severe stroke severity."
    else:
        interpretation = "NIHSS: severe stroke severity."

    return result(metadata, score, "points", interpretation)


def hunt_hess_subarachnoid_hemorrhage_grade(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_in_range(inputs, "grade", 1, 5)
    labels = {
        1: "asymptomatic or mild headache",
        2: "moderate-severe headache or nuchal rigidity with no deficit except cranial nerve palsy",
        3: "drowsy/confused or mild focal deficit",
        4: "stupor with moderate-severe hemiparesis",
        5: "deep coma with decerebrate posturing",
    }

    return result(metadata, grade, "grade", f"Hunt-Hess grade {grade}: {labels[grade]}.")


def marshall_ct_classification(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    visible_pathology = _boolean_flag(inputs, "visible_intracranial_pathology")
    cisterns = _string_choice(inputs, "cisterns", {"normal", "compressed", "absent"})
    midline_shift_mm = _number(inputs, "midline_shift_mm")
    lesion_volume_ml = _number(inputs, "high_or_mixed_density_lesion_volume_ml")
    mass_lesion_evacuated = _boolean_flag(inputs, "mass_lesion_evacuated")

    if midline_shift_mm < 0:
        raise ValueError("midline_shift_mm must be nonnegative")
    if lesion_volume_ml < 0:
        raise ValueError("high_or_mixed_density_lesion_volume_ml must be nonnegative")

    if mass_lesion_evacuated:
        return result(metadata, 5, "class", "Marshall CT class V: evacuated mass lesion.")
    if lesion_volume_ml > 25:
        return result(metadata, 6, "class", "Marshall CT class VI: non-evacuated mass lesion greater than 25 mL.")
    if not visible_pathology:
        return result(metadata, 1, "class", "Marshall CT class I: no visible intracranial pathology.")
    if midline_shift_mm > 5:
        return result(metadata, 4, "class", "Marshall CT class IV: diffuse injury with midline shift greater than 5 mm.")
    if cisterns in {"compressed", "absent"}:
        return result(metadata, 3, "class", "Marshall CT class III: diffuse injury with swelling.")
    return result(metadata, 2, "class", "Marshall CT class II: diffuse injury with cisterns present and shift 0-5 mm.")


def rotterdam_ct_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    basal_cisterns = _string_choice(inputs, "basal_cisterns", {"normal", "compressed", "absent"})
    midline_shift_mm = _number(inputs, "midline_shift_mm")
    if midline_shift_mm < 0:
        raise ValueError("midline_shift_mm must be nonnegative")

    cistern_points = {"normal": 0, "compressed": 1, "absent": 2}[basal_cisterns]
    score = (
        1
        + cistern_points
        + int(midline_shift_mm > 5)
        + (0 if _boolean_flag(inputs, "epidural_mass_lesion_present") else 1)
        + int(_boolean_flag(inputs, "intraventricular_or_traumatic_sah"))
    )

    interpretation = (
        "higher Rotterdam CT score; CT findings are associated with worse prognosis after traumatic brain injury"
        if score >= 4
        else "lower Rotterdam CT score; CT findings are associated with lower risk than higher score strata"
    )
    return result(metadata, score, "points", interpretation)
