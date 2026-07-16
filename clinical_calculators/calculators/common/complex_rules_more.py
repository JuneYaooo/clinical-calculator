from __future__ import annotations

import math
from typing import Any

from clinical_calculators.models import CalculationResult, CalculatorMetadata
from clinical_calculators.calculators._helpers import number, result


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _nonnegative(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return value


def _normalized(inputs: dict[str, Any], key: str) -> str:
    if key not in inputs:
        raise KeyError(key)
    return str(inputs[key]).strip().lower().replace("-", "_").replace(" ", "_")


def stone_nephrolithometry_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    stone_area = _positive(inputs, "stone_area_mm2")
    if stone_area <= 399:
        size_points = 1
    elif stone_area <= 799:
        size_points = 2
    elif stone_area <= 1599:
        size_points = 3
    else:
        size_points = 4

    tract_length_points = 1 if _positive(inputs, "skin_to_stone_distance_mm") <= 100 else 2

    obstruction = _normalized(inputs, "obstruction")
    if obstruction in {"none", "no", "absent", "mild"}:
        obstruction_points = 1
    elif obstruction in {"moderate", "severe"}:
        obstruction_points = 2
    else:
        raise ValueError("obstruction must be none/mild/moderate/severe")

    if bool(inputs.get("staghorn_calculus", False)):
        calyx_points = 3
    else:
        calyces = int(_positive(inputs, "calyces_involved"))
        if calyces < 1:
            raise ValueError("calyces_involved must be at least 1")
        calyx_points = 1 if calyces <= 2 else 2

    density_points = 1 if _positive(inputs, "stone_density_hu") <= 950 else 2
    score = size_points + tract_length_points + obstruction_points + calyx_points + density_points
    if score <= 7:
        label = "low complexity"
    elif score <= 10:
        label = "moderate complexity"
    else:
        label = "high complexity"
    return result(metadata, score, "points", f"S.T.O.N.E. nephrolithometry score: {label}.")


def renal_nephrometry_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    radius = _positive(inputs, "radius_cm")
    if radius <= 4:
        radius_points = 1
    elif radius < 7:
        radius_points = 2
    else:
        radius_points = 3

    exophytic_percent = _nonnegative(inputs, "exophytic_percent")
    if exophytic_percent > 100:
        raise ValueError("exophytic_percent must be between 0 and 100")
    if exophytic_percent >= 50:
        exophytic_points = 1
    elif exophytic_percent > 0:
        exophytic_points = 2
    else:
        exophytic_points = 3

    nearness = _nonnegative(inputs, "nearness_to_collecting_system_mm")
    if nearness >= 7:
        nearness_points = 1
    elif nearness > 4:
        nearness_points = 2
    else:
        nearness_points = 3

    location = _normalized(inputs, "location_relative_to_polar_lines")
    if location in {"entirely_above_or_below_polar_lines", "outside_polar_lines", "above_or_below"}:
        location_points = 1
    elif location in {"crosses_polar_line", "crosses_one_polar_line"}:
        location_points = 2
    elif location in {
        "entirely_between_polar_lines",
        "between_polar_lines",
        "crosses_axial_midline",
        "more_than_50_percent_crosses_polar_line",
    }:
        location_points = 3
    else:
        raise ValueError("location_relative_to_polar_lines is not supported")

    anterior_posterior = str(inputs.get("anterior_posterior", "x")).strip().lower()
    if anterior_posterior in {"anterior", "a"}:
        suffix = "a"
    elif anterior_posterior in {"posterior", "p"}:
        suffix = "p"
    elif anterior_posterior in {"not_applicable", "neither", "x"}:
        suffix = "x"
    else:
        raise ValueError("anterior_posterior must be anterior, posterior, or not_applicable")

    score = radius_points + exophytic_points + nearness_points + location_points
    descriptor = f"{score}{suffix}"
    if bool(inputs.get("touches_main_renal_vessels", False)):
        descriptor += "h"

    if score <= 6:
        label = "low complexity"
    elif score <= 9:
        label = "moderate complexity"
    else:
        label = "high complexity"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "descriptor": descriptor},
        unit="points",
        interpretation=f"R.E.N.A.L. nephrometry score: {label}.",
    )


def padua_nephrometry_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    longitudinal = _normalized(inputs, "longitudinal_location")
    if longitudinal in {"upper_or_lower", "upper", "lower", "superior_or_inferior"}:
        longitudinal_points = 1
    elif longitudinal in {"middle", "middle_pole"}:
        longitudinal_points = 2
    else:
        raise ValueError("longitudinal_location must be upper_or_lower or middle")

    rim = _normalized(inputs, "rim_location")
    if rim == "lateral":
        rim_points = 1
    elif rim == "medial":
        rim_points = 2
    else:
        raise ValueError("rim_location must be lateral or medial")

    sinus_points = 2 if bool(inputs.get("renal_sinus_involved", False)) else 1
    collecting_points = 2 if bool(inputs.get("collecting_system_involved", False)) else 1

    tumor_size = _positive(inputs, "tumor_size_cm")
    if tumor_size <= 4:
        size_points = 1
    elif tumor_size <= 7:
        size_points = 2
    else:
        size_points = 3

    exophytic_percent = _nonnegative(inputs, "exophytic_percent")
    if exophytic_percent > 100:
        raise ValueError("exophytic_percent must be between 0 and 100")
    if exophytic_percent >= 50:
        exophytic_points = 1
    elif exophytic_percent > 0:
        exophytic_points = 2
    else:
        exophytic_points = 3

    score = (
        longitudinal_points
        + rim_points
        + sinus_points
        + collecting_points
        + size_points
        + exophytic_points
    )
    if score <= 7:
        label = "low risk"
    elif score <= 9:
        label = "intermediate risk"
    else:
        label = "high risk"
    return result(metadata, score, "points", f"PADUA nephrometry score: {label}.")


def tips_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (
        0.957 * math.log(_positive(inputs, "creatinine_mg_dl"))
        + 0.378 * math.log(_positive(inputs, "bilirubin_mg_dl"))
        + 1.12 * math.log(_positive(inputs, "inr"))
        + 0.643 * int(bool(inputs.get("etiology_viral_or_other", False)))
    )
    return result(metadata, value, "score", "TIPS mortality risk score")


def adrenal_washout_percentages(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    noncontrast = number(inputs, "noncontrast_hu")
    enhanced = number(inputs, "enhanced_hu")
    delayed = number(inputs, "delayed_hu")
    absolute_denominator = enhanced - noncontrast
    if absolute_denominator == 0 or enhanced == 0:
        raise ValueError("enhanced_hu must differ from noncontrast_hu and must not be zero")
    absolute = 100 * (enhanced - delayed) / absolute_denominator
    relative = 100 * (enhanced - delayed) / enhanced
    interpretation = "adenoma-compatible washout pattern" if absolute >= 60 or relative >= 40 else "washout below typical adenoma thresholds"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "absolute_washout_percent": round(absolute, 4),
            "relative_washout_percent": round(relative, 4),
        },
        unit="%",
        interpretation=interpretation,
    )


def stone_ureteral_stone_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if str(inputs.get("sex", "")).strip().lower() == "male":
        score += 2

    duration = number(inputs, "pain_duration_hours")
    if duration < 6:
        score += 3
    elif duration <= 24:
        score += 1

    race = str(inputs.get("race", "")).strip().lower()
    if race not in {"black", "african american", "african-american"}:
        score += 3

    nausea_or_vomiting = str(inputs.get("nausea_or_vomiting", "")).strip().lower()
    if nausea_or_vomiting == "vomiting":
        score += 2
    elif nausea_or_vomiting in {"nausea", "nausea only"}:
        score += 1

    if bool(inputs.get("hematuria", False)):
        score += 3

    if score <= 5:
        interpretation = "low probability of ureteral stone"
    elif score <= 9:
        interpretation = "moderate probability of ureteral stone"
    else:
        interpretation = "high probability of ureteral stone"
    return result(metadata, score, "points", interpretation)


def kdigo_aki_stage(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    stage = 0
    baseline = _positive(inputs, "baseline_creatinine_mg_dl")
    current = _positive(inputs, "current_creatinine_mg_dl")
    increase = number(inputs, "creatinine_increase_mg_dl")
    ratio = current / baseline

    if increase >= 0.3 or 1.5 <= ratio < 2:
        stage = max(stage, 1)
    if 2 <= ratio < 3:
        stage = max(stage, 2)
    if ratio >= 3 or current >= 4 or bool(inputs.get("renal_replacement_therapy", False)):
        stage = max(stage, 3)

    urine_output = number(inputs, "urine_output_ml_kg_hr")
    urine_duration = number(inputs, "urine_output_duration_hours")
    anuria_duration = number(inputs, "anuria_duration_hours")
    if urine_output < 0.5 and 6 <= urine_duration < 12:
        stage = max(stage, 1)
    if urine_output < 0.5 and urine_duration >= 12:
        stage = max(stage, 2)
    if urine_output < 0.3 and urine_duration >= 24:
        stage = max(stage, 3)
    if anuria_duration >= 12:
        stage = max(stage, 3)

    interpretation = "no AKI by supplied KDIGO criteria" if stage == 0 else f"KDIGO AKI stage {stage}"
    return result(metadata, stage, "stage", interpretation)
