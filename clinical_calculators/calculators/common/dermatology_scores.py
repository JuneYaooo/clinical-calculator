from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


PASI_REGIONS: dict[str, float] = {
    "head": 0.1,
    "upper_limbs": 0.2,
    "trunk": 0.3,
    "lower_limbs": 0.4,
}
PASI_SEVERITY_KEYS = ("erythema", "induration", "scaling")

EASI_REGIONS: dict[str, float] = {
    "head_neck": 0.1,
    "upper_limbs": 0.2,
    "trunk": 0.3,
    "lower_limbs": 0.4,
}
EASI_SEVERITY_KEYS = ("erythema", "edema", "excoriation", "lichenification")

SALT_REGIONS: dict[str, float] = {
    "vertex_percent_loss": 0.4,
    "right_profile_percent_loss": 0.18,
    "left_profile_percent_loss": 0.18,
    "posterior_percent_loss": 0.24,
}

HURLEY_STAGE_DESCRIPTIONS = {
    1: "single or multiple abscesses without sinus tracts or scarring",
    2: "recurrent abscesses with sinus tracts and scarring, separated lesions",
    3: "diffuse or near-diffuse involvement with multiple interconnected sinus tracts and abscesses",
}

GAGS_FACTORS: dict[str, int] = {
    "forehead": 2,
    "right_cheek": 2,
    "left_cheek": 2,
    "nose": 1,
    "chin": 1,
    "chest_upper_back": 3,
}

ROSACEA_IGA_GRADES = {
    0: "clear",
    1: "almost clear",
    2: "mild",
    3: "moderate",
    4: "severe",
}


def _integer_score(value: Any, key: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _region_score(
    inputs: dict[str, Any],
    region: str,
    severity_keys: tuple[str, ...],
    severity_maximum: int,
) -> tuple[int, int]:
    if region not in inputs:
        raise KeyError(region)

    region_inputs = inputs[region]
    if not isinstance(region_inputs, Mapping):
        raise ValueError(f"{region} must be a mapping of score keys")

    severity_sum = 0
    for key in severity_keys:
        if key not in region_inputs:
            raise KeyError(f"{region}.{key}")
        severity_sum += _integer_score(region_inputs[key], f"{region}.{key}", 0, severity_maximum)

    if "area" not in region_inputs:
        raise KeyError(f"{region}.area")
    area = _integer_score(region_inputs["area"], f"{region}.area", 0, 6)

    return severity_sum, area


def _weighted_area_severity_score(
    inputs: dict[str, Any],
    regions: dict[str, float],
    severity_keys: tuple[str, ...],
    severity_maximum: int,
) -> float:
    score = 0.0
    for region, weight in regions.items():
        severity_sum, area = _region_score(inputs, region, severity_keys, severity_maximum)
        score += severity_sum * area * weight
    return score


def _score_items(inputs: dict[str, Any], count: int, minimum: int, maximum: int, key: str = "items") -> int:
    if key not in inputs:
        raise KeyError(key)

    values = inputs[key]
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{key} must be a sequence of {count} integer scores")
    if len(values) != count:
        raise ValueError(f"{key} must contain exactly {count} scores")

    return sum(_integer_score(value, f"{key}[{index}]", minimum, maximum) for index, value in enumerate(values))


def _pasi_interpretation(score: float) -> str:
    if score < 10:
        severity = "mild"
    elif score <= 20:
        severity = "moderate"
    else:
        severity = "severe"
    return f"PASI severity: {severity}."


def _dlqi_interpretation(score: int) -> str:
    if score <= 1:
        effect = "no effect"
    elif score <= 5:
        effect = "small effect"
    elif score <= 10:
        effect = "moderate effect"
    elif score <= 20:
        effect = "very large effect"
    else:
        effect = "extremely large effect"
    return f"DLQI impact: {effect}."


def psoriasis_area_severity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _weighted_area_severity_score(inputs, PASI_REGIONS, PASI_SEVERITY_KEYS, 4)
    return result(metadata, score, "points", _pasi_interpretation(score))


def eczema_area_severity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _weighted_area_severity_score(inputs, EASI_REGIONS, EASI_SEVERITY_KEYS, 3)
    return result(metadata, score, "points", "EASI score on a 0-72 point scale.")


def scorad_atopic_dermatitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    extent = float(inputs["extent_percent"])
    if extent < 0 or extent > 100:
        raise ValueError("extent_percent must be between 0 and 100")
    intensity_score = _score_items(inputs, count=6, minimum=0, maximum=3, key="intensity_scores")
    pruritus = float(inputs["pruritus_vas"])
    sleep_loss = float(inputs["sleep_loss_vas"])
    if pruritus < 0 or pruritus > 10:
        raise ValueError("pruritus_vas must be between 0 and 10")
    if sleep_loss < 0 or sleep_loss > 10:
        raise ValueError("sleep_loss_vas must be between 0 and 10")

    score = extent / 5 + 7 * intensity_score / 2 + pruritus + sleep_loss
    if score < 25:
        interpretation = "mild atopic dermatitis by SCORAD"
    elif score <= 50:
        interpretation = "moderate atopic dermatitis by SCORAD"
    else:
        interpretation = "severe atopic dermatitis by SCORAD"
    return result(metadata, score, "points", interpretation)


def dermatology_life_quality_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=10, minimum=0, maximum=3)
    return result(metadata, score, "points", _dlqi_interpretation(score))


def severity_of_alopecia_tool(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0.0
    for key, weight in SALT_REGIONS.items():
        if key not in inputs:
            raise KeyError(key)
        percent_loss = float(inputs[key])
        if percent_loss < 0 or percent_loss > 100:
            raise ValueError(f"{key} must be between 0 and 100")
        score += percent_loss * weight
    return result(metadata, score, "percent", "SALT weighted scalp hair-loss percent.")


def modified_rodnan_skin_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _score_items(inputs, count=17, minimum=0, maximum=3, key="site_scores")
    return result(metadata, score, "points", "mRSS summed skin thickness across 17 skin sites.")


def global_acne_grading_system(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    for region, factor in GAGS_FACTORS.items():
        if region not in inputs:
            raise KeyError(region)
        score += _integer_score(inputs[region], region, 0, 4) * factor

    if score == 0:
        severity = "none"
    elif score <= 18:
        severity = "mild"
    elif score <= 30:
        severity = "moderate"
    elif score <= 38:
        severity = "severe"
    else:
        severity = "very severe"

    return result(metadata, score, "points", f"GAGS acne severity: {severity}.")


def nail_psoriasis_severity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    matrix_score = _score_items(inputs, count=10, minimum=0, maximum=4, key="matrix_scores")
    bed_score = _score_items(inputs, count=10, minimum=0, maximum=4, key="bed_scores")
    score = matrix_score + bed_score
    return result(metadata, score, "points", "NAPSI summed matrix and nail-bed scores across 10 nails.")


def urticaria_activity_score_7(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    wheal_score = _score_items(inputs, count=7, minimum=0, maximum=3, key="daily_wheal_scores")
    pruritus_score = _score_items(inputs, count=7, minimum=0, maximum=3, key="daily_pruritus_scores")
    score = wheal_score + pruritus_score

    if score == 0:
        activity = "urticaria-free"
    elif score <= 6:
        activity = "well-controlled"
    elif score <= 15:
        activity = "mild"
    elif score <= 27:
        activity = "moderate"
    else:
        activity = "severe"

    return result(metadata, score, "points", f"UAS7 chronic urticaria activity: {activity}.")


def hidradenitis_suppurativa_hurley_stage(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    stage = _integer_score(inputs["stage"], "stage", 1, 3)
    return result(metadata, stage, "stage", f"Hurley stage {stage}: {HURLEY_STAGE_DESCRIPTIONS[stage]}.")


def investigator_global_assessment_rosacea(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_score(inputs["grade"], "grade", 0, 4)
    label = ROSACEA_IGA_GRADES[grade]
    value = {
        "grade": grade,
        "label": label,
        "clear_or_almost_clear": grade <= 1,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="IGA grade",
        interpretation=f"Investigator Global Assessment for rosacea grade {grade}: {label}.",
    )


def abcde_melanoma_warning_rule(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = (
        "asymmetry",
        "border_irregularity",
        "color_variation",
        "diameter_over_6_mm",
        "evolving",
    )
    warnings: dict[str, bool] = {}
    for key in keys:
        if key not in inputs:
            raise KeyError(key)
        value = inputs[key]
        if isinstance(value, bool):
            warnings[key] = value
        elif value == 0 or value == 1:
            warnings[key] = bool(value)
        else:
            raise ValueError(f"{key} must be a bool or 0/1")

    warning_count = sum(1 for value in warnings.values() if value)
    value = {"warning_sign_count": warning_count, "any_warning_sign": warning_count > 0, "warning_signs": warnings}
    interpretation = (
        "ABCDE melanoma warning rule: one or more warning signs coded; clinical skin examination is warranted."
        if warning_count
        else "ABCDE melanoma warning rule: no warning signs coded."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="warning signs",
        interpretation=interpretation,
    )
