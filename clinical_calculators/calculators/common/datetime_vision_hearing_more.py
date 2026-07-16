from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata

OTS_VISUAL_ACUITY_POINTS = {
    "nlp": 60,
    "lp_hm": 70,
    "one_200_to_19_200": 80,
    "twenty_200_to_20_50": 90,
    "twenty_40_or_better": 100,
}
OTS_RISK_FACTOR_POINTS = {
    "globe_rupture": 23,
    "endophthalmitis": 17,
    "perforating_injury": 14,
    "retinal_detachment": 11,
    "relative_afferent_pupillary_defect": 10,
}

DR_SEVERITY_GRADES = {
    "no_apparent_retinopathy": (0, "no apparent diabetic retinopathy"),
    "mild_npdr": (1, "mild nonproliferative diabetic retinopathy"),
    "moderate_npdr": (2, "moderate nonproliferative diabetic retinopathy"),
    "severe_npdr": (3, "severe nonproliferative diabetic retinopathy"),
    "pdr": (4, "proliferative diabetic retinopathy"),
}

ROP_PLUS_DISEASE = {"none", "pre_plus", "plus"}

HOUSE_BRACKMANN_GRADES = {
    1: ("I", "normal"),
    2: ("II", "mild dysfunction"),
    3: ("III", "moderate dysfunction"),
    4: ("IV", "moderately severe dysfunction"),
    5: ("V", "severe dysfunction"),
    6: ("VI", "total paralysis"),
}

NEI_VFQ_25_SUBSCALES = {
    "general_health": ("1",),
    "general_vision": ("2",),
    "ocular_pain": ("4", "19"),
    "near_activities": ("5", "6", "7"),
    "distance_activities": ("8", "9", "14"),
    "social_functioning": ("11", "13"),
    "mental_health": ("3", "21", "22", "25"),
    "role_difficulties": ("17", "18"),
    "dependency": ("20", "23", "24"),
    "driving": ("15c", "16", "16a"),
    "color_vision": ("12",),
    "peripheral_vision": ("10",),
}
NEI_VFQ_25_SCORING_ITEMS = frozenset(
    item for items in NEI_VFQ_25_SUBSCALES.values() for item in items
)


def _date_input(inputs: dict[str, Any], key: str) -> date:
    if key not in inputs:
        raise KeyError(key)
    value = inputs[key]
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _gestational_age_label(days: int) -> str:
    return f"{days // 7}w{days % 7}d"


def estimated_due_date_and_gestational_age(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    as_of_date = _date_input(inputs, "as_of_date")

    if "lmp_date" in inputs:
        start_date = _date_input(inputs, "lmp_date")
        cycle_length_days = int(inputs.get("cycle_length_days", 28))
        estimated_due_date = start_date + timedelta(days=280 + (cycle_length_days - 28))
        dating_method = "last menstrual period"
    elif "conception_date" in inputs:
        start_date = _date_input(inputs, "conception_date")
        estimated_due_date = start_date + timedelta(days=266)
        dating_method = "conception date"
    elif "embryo_transfer_date" in inputs:
        transfer_date = _date_input(inputs, "embryo_transfer_date")
        embryo_age_days = int(number(inputs, "embryo_age_days"))
        estimated_due_date = transfer_date + timedelta(days=266 - embryo_age_days)
        dating_method = "embryo transfer date"
    elif "ultrasound_exam_date" in inputs:
        ultrasound_date = _date_input(inputs, "ultrasound_exam_date")
        gestational_age_days = int(number(inputs, "gestational_age_days_at_ultrasound"))
        estimated_due_date = ultrasound_date + timedelta(days=280 - gestational_age_days)
        dating_method = "ultrasound gestational age"
    else:
        raise KeyError("lmp_date, conception_date, embryo_transfer_date, or ultrasound_exam_date")

    gestational_age_days = 280 - (estimated_due_date - as_of_date).days
    value = {
        "estimated_due_date": estimated_due_date.isoformat(),
        "gestational_age_days": gestational_age_days,
        "gestational_age": _gestational_age_label(gestational_age_days),
        "dating_method": dating_method,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="date",
        interpretation=f"Estimated due date and gestational age by {dating_method}.",
    )


def visual_acuity_from_logmar(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    logmar = number(inputs, "logmar")
    decimal_acuity = 10 ** (-logmar)
    value = {
        "logmar": round(logmar, 4),
        "decimal_acuity": round(decimal_acuity, 4),
        "snellen_20_denominator": round(20 / decimal_acuity, 4),
        "etdrs_letters": round(85 - 50 * logmar),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="visual acuity",
        interpretation="visual acuity conversion from LogMAR",
    )


def _bool_input(inputs: dict[str, Any], key: str) -> bool:
    return bool(inputs.get(key, False))


def _integer_input(inputs: dict[str, Any], key: str) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    return int(value)


def _ots_category(raw_score: int) -> int:
    if raw_score <= 44:
        return 1
    if raw_score <= 65:
        return 2
    if raw_score <= 80:
        return 3
    if raw_score <= 91:
        return 4
    return 5


def ocular_trauma_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    visual_acuity = str(inputs["initial_visual_acuity"])
    if visual_acuity not in OTS_VISUAL_ACUITY_POINTS:
        allowed = ", ".join(sorted(OTS_VISUAL_ACUITY_POINTS))
        raise ValueError(f"initial_visual_acuity must be one of: {allowed}")

    deductions = {
        key: points for key, points in OTS_RISK_FACTOR_POINTS.items() if _bool_input(inputs, key)
    }
    raw_score = OTS_VISUAL_ACUITY_POINTS[visual_acuity] - sum(deductions.values())
    category = _ots_category(raw_score)
    value = {
        "raw_score": raw_score,
        "category": category,
        "initial_visual_acuity": visual_acuity,
        "deductions": deductions,
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="OTS category",
        interpretation=f"Ocular Trauma Score category {category} from raw score {raw_score}.",
    )


def diabetic_retinopathy_severity_scale(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    severity = str(inputs["severity"])
    if severity not in DR_SEVERITY_GRADES:
        allowed = ", ".join(DR_SEVERITY_GRADES)
        raise ValueError(f"severity must be one of: {allowed}")
    order, description = DR_SEVERITY_GRADES[severity]
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"grade": severity, "order": order, "description": description},
        unit="severity grade",
        interpretation=f"Diabetic retinopathy severity: {description}.",
    )


def retinopathy_of_prematurity_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    zone = int(number(inputs, "zone"))
    stage = int(number(inputs, "stage"))
    plus_disease = str(inputs["plus_disease"])
    if zone not in {1, 2, 3}:
        raise ValueError("zone must be 1, 2, or 3")
    if stage < 0 or stage > 5:
        raise ValueError("stage must be between 0 and 5")
    if plus_disease not in ROP_PLUS_DISEASE:
        allowed = ", ".join(sorted(ROP_PLUS_DISEASE))
        raise ValueError(f"plus_disease must be one of: {allowed}")

    zone_label = {1: "Zone I", 2: "Zone II", 3: "Zone III"}[zone]
    plus_label = plus_disease.replace("_", "-")
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"zone": zone, "stage": stage, "plus_disease": plus_disease},
        unit="ROP classification",
        interpretation=f"{zone_label}, stage {stage}, {plus_label} disease.",
    )


def pure_tone_average(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    thresholds = [
        number(inputs, "threshold_500_hz_db"),
        number(inputs, "threshold_1000_hz_db"),
        number(inputs, "threshold_2000_hz_db"),
    ]
    if "threshold_4000_hz_db" in inputs:
        thresholds.append(number(inputs, "threshold_4000_hz_db"))
    value = sum(thresholds) / len(thresholds)
    return result(metadata, value, "dB HL", "pure tone average hearing threshold")


def _side_score(inputs: dict[str, Any], side: str, keys: tuple[str, ...], allowed: set[int]) -> int:
    if side not in inputs:
        raise KeyError(side)
    side_inputs = inputs[side]
    if not isinstance(side_inputs, dict):
        raise ValueError(f"{side} must be a mapping")
    total = 0
    for key in keys:
        if key not in side_inputs:
            raise KeyError(f"{side}.{key}")
        value = int(number(side_inputs, key))
        if value not in allowed:
            raise ValueError(f"{side}.{key} must be one of {sorted(allowed)}")
        total += value
    return total


def lund_mackay_ct_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sinus_keys = ("maxillary", "anterior_ethmoid", "posterior_ethmoid", "sphenoid", "frontal")
    total = 0
    for side in ("left", "right"):
        total += _side_score(inputs, side, sinus_keys, {0, 1, 2})
        total += _side_score(inputs, side, ("omc",), {0, 2})
    return result(metadata, total, "points", "Lund-Mackay CT sinus score; higher score indicates greater radiographic disease")


def lund_kennedy_endoscopic_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = ("polyps", "edema", "discharge", "scarring", "crusting")
    total = _side_score(inputs, "left", keys, {0, 1, 2}) + _side_score(inputs, "right", keys, {0, 1, 2})
    return result(metadata, total, "points", "Lund-Kennedy endoscopic score; higher score indicates greater endoscopic disease")


def house_brackmann_facial_nerve_grade(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_input(inputs, "grade")
    if grade not in HOUSE_BRACKMANN_GRADES:
        raise ValueError("grade must be an integer from 1 to 6")
    roman, severity = HOUSE_BRACKMANN_GRADES[grade]
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"grade": grade, "roman": roman, "severity": severity},
        unit="House-Brackmann grade",
        interpretation=f"House-Brackmann grade {roman}: {severity}.",
    )


def friedman_staging_system(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    tongue_position = _integer_input(inputs, "friedman_tongue_position")
    tonsil_size = _integer_input(inputs, "tonsil_size")
    bmi = number(inputs, "bmi")
    anatomic_deformity = _bool_input(inputs, "significant_craniofacial_or_anatomic_deformity")

    if tongue_position not in {1, 2, 3, 4}:
        raise ValueError("friedman_tongue_position must be 1, 2, 3, or 4")
    if tonsil_size not in {0, 1, 2, 3, 4}:
        raise ValueError("tonsil_size must be 0, 1, 2, 3, or 4")
    if bmi <= 0:
        raise ValueError("bmi must be greater than 0 kg/m^2")

    if bmi > 40 or anatomic_deformity:
        stage = 4
        reason = "stage IV criterion"
    elif tongue_position in {1, 2} and tonsil_size in {3, 4}:
        stage = 1
        reason = "favorable tongue position with large tonsils"
    elif (
        tongue_position in {1, 2}
        and tonsil_size in {0, 1, 2}
        or tongue_position in {3, 4}
        and tonsil_size in {3, 4}
    ):
        stage = 2
        reason = "intermediate anatomic pattern"
    else:
        stage = 3
        reason = "unfavorable tongue position with small tonsils"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "stage": stage,
            "friedman_tongue_position": tongue_position,
            "tonsil_size": tonsil_size,
            "bmi": round(bmi, 4),
            "significant_craniofacial_or_anatomic_deformity": anatomic_deformity,
            "stage_reason": reason,
        },
        unit="Friedman stage",
        interpretation=f"Friedman stage {stage}: {reason}.",
    )


def brodsky_tonsil_grading_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    percent = number(inputs, "tonsillar_airway_occupation_percent")
    if percent < 0 or percent > 100:
        raise ValueError("tonsillar_airway_occupation_percent must be between 0 and 100")

    if _bool_input(inputs, "tonsils_within_fossa"):
        grade = 0
        band = "tonsils within fossa"
    elif percent <= 25:
        grade = 1
        band = "0-25% airway occupation"
    elif percent <= 50:
        grade = 2
        band = ">25-50% airway occupation"
    elif percent <= 75:
        grade = 3
        band = ">50-75% airway occupation"
    else:
        grade = 4
        band = ">75% airway occupation"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "grade": grade,
            "tonsillar_airway_occupation_percent": round(percent, 4),
            "tonsils_within_fossa": _bool_input(inputs, "tonsils_within_fossa"),
            "band": band,
        },
        unit="Brodsky grade",
        interpretation=f"Brodsky tonsil grade {grade}: {band}.",
    )


def iol_power_srk_formula(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    a_constant = number(inputs, "a_constant")
    axial_length = number(inputs, "axial_length_mm")
    keratometry = number(inputs, "average_keratometry_d")
    if axial_length <= 0:
        raise ValueError("axial_length_mm must be greater than 0")
    if keratometry <= 0:
        raise ValueError("average_keratometry_d must be greater than 0")

    power = a_constant - (2.5 * axial_length) - (0.9 * keratometry)
    return result(
        metadata,
        power,
        "D",
        "SRK IOL power formula: P = A - 2.5L - 0.9K.",
    )


def _nei_item_score(value: Any, key: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"item_scores[{key}] must be a 0-100 score or None")
    score = float(value)
    if not math.isfinite(score) or score < 0 or score > 100:
        raise ValueError(f"item_scores[{key}] must be between 0 and 100")
    return score


def _rounded_score(score: float) -> float:
    return round(score, 4)


def nei_visual_function_questionnaire_25(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "item_scores" not in inputs:
        raise KeyError("item_scores")

    raw_item_scores = inputs["item_scores"]
    if not isinstance(raw_item_scores, Mapping):
        raise ValueError("item_scores must be a mapping of pre-scored item ids to 0-100 scores")

    item_scores: dict[str, float | None] = {}
    for raw_key, raw_value in raw_item_scores.items():
        key = str(raw_key)
        if key not in NEI_VFQ_25_SCORING_ITEMS:
            allowed = ", ".join(sorted(NEI_VFQ_25_SCORING_ITEMS))
            raise ValueError(f"item_scores keys must be one of: {allowed}")
        item_scores[key] = _nei_item_score(raw_value, key)

    subscales: dict[str, float] = {}
    for subscale, keys in NEI_VFQ_25_SUBSCALES.items():
        answered_scores = [item_scores[key] for key in keys if item_scores.get(key) is not None]
        if answered_scores:
            subscales[subscale] = _rounded_score(sum(answered_scores) / len(answered_scores))

    composite_subscales = [
        score for subscale, score in subscales.items() if subscale != "general_health"
    ]
    if not composite_subscales:
        raise ValueError("item_scores must include at least one answered vision-targeted subscale")

    composite_score = _rounded_score(sum(composite_subscales) / len(composite_subscales))
    value = {
        "subscales": subscales,
        "composite_score": composite_score,
        "answered_item_count": sum(1 for score in item_scores.values() if score is not None),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="0-100 score",
        interpretation=(
            "NEI VFQ-25 subscales and composite score from pre-scored 0-100 item values; "
            "higher scores indicate better self-reported visual function."
        ),
    )


__all__ = [
    "brodsky_tonsil_grading_scale",
    "diabetic_retinopathy_severity_scale",
    "estimated_due_date_and_gestational_age",
    "friedman_staging_system",
    "house_brackmann_facial_nerve_grade",
    "iol_power_srk_formula",
    "lund_kennedy_endoscopic_score",
    "lund_mackay_ct_score",
    "nei_visual_function_questionnaire_25",
    "ocular_trauma_score",
    "pure_tone_average",
    "retinopathy_of_prematurity_classification",
    "visual_acuity_from_logmar",
]
