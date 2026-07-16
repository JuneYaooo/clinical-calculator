from __future__ import annotations

import math
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be greater than 0")
    return value


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


def _category_points(inputs: dict[str, Any], key: str, point_map: dict[str, int]) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if value not in point_map:
        allowed = ", ".join(sorted(point_map))
        raise ValueError(f"{key} must be one of: {allowed}")
    return point_map[value]


def _integer_range(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    integer = int(value)
    if integer < minimum or integer > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer


def glasgow_blatchford_upper_gi_bleeding_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    bun = _non_negative_number(inputs, "bun_mg_dl")
    hemoglobin = _positive_number(inputs, "hemoglobin_g_dl")
    sex = inputs.get("sex")
    systolic_bp = _positive_number(inputs, "systolic_bp")
    pulse = _non_negative_number(inputs, "pulse")

    if sex not in {"male", "female"}:
        raise ValueError("sex must be one of: female, male")

    score = 0
    urea_mmol_l = bun / 2.801
    if urea_mmol_l >= 25:
        score += 6
    elif urea_mmol_l >= 10:
        score += 4
    elif urea_mmol_l >= 8:
        score += 3
    elif urea_mmol_l >= 6.5:
        score += 2

    if sex == "male":
        if hemoglobin < 10:
            score += 6
        elif hemoglobin < 12:
            score += 3
        elif hemoglobin <= 12.9:
            score += 1
    else:
        if hemoglobin < 10:
            score += 6
        elif hemoglobin < 12:
            score += 1

    if systolic_bp < 90:
        score += 3
    elif systolic_bp < 100:
        score += 2
    elif systolic_bp <= 109:
        score += 1

    if pulse >= 100:
        score += 1
    if _boolean_flag(inputs, "melena"):
        score += 1
    if _boolean_flag(inputs, "syncope"):
        score += 2
    if _boolean_flag(inputs, "hepatic_disease"):
        score += 2
    if _boolean_flag(inputs, "cardiac_failure"):
        score += 2

    interpretation = "very low risk by Glasgow-Blatchford score" if score <= 1 else "higher risk by Glasgow-Blatchford score"
    return result(metadata, score, "points", interpretation)


def rockall_upper_gi_bleeding_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _non_negative_number(inputs, "age_years")
    score = 0
    if age >= 80:
        score += 2
    elif age >= 60:
        score += 1

    score += _category_points(inputs, "shock", {"none": 0, "tachycardia": 1, "hypotension": 2})
    score += _category_points(
        inputs,
        "comorbidity",
        {"none": 0, "major": 2, "renal_liver_malignancy": 3},
    )
    score += _category_points(
        inputs,
        "diagnosis",
        {"mallory_weiss_or_none": 0, "all_other": 1, "upper_gi_malignancy": 2},
    )
    score += _category_points(
        inputs,
        "stigmata",
        {"none_or_dark_spot": 0, "blood_or_adherent_clot_or_visible_vessel": 2},
    )

    if score <= 2:
        interpretation = "low risk by Rockall score"
    elif score <= 4:
        interpretation = "moderate risk by Rockall score"
    else:
        interpretation = "high risk by Rockall score"

    return result(metadata, score, "points", interpretation)


def full_rockall_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    return rockall_upper_gi_bleeding_score(metadata, inputs)


def aims65_upper_gi_bleeding_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    if _positive_number(inputs, "albumin_g_dl") < 3.0:
        score += 1
    if _positive_number(inputs, "inr") > 1.5:
        score += 1
    if _boolean_flag(inputs, "altered_mental_status"):
        score += 1
    if _positive_number(inputs, "systolic_bp") <= 90:
        score += 1
    if _non_negative_number(inputs, "age_years") > 65:
        score += 1

    interpretation = "higher risk by AIMS65" if score >= 2 else "lower risk by AIMS65"
    return result(metadata, score, "points", interpretation)


def must_malnutrition_screening(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bmi = _positive_number(inputs, "bmi")
    weight_loss = _non_negative_number(inputs, "unplanned_weight_loss_percent")

    score = 0
    if bmi < 18.5:
        score += 2
    elif bmi <= 20:
        score += 1

    if weight_loss > 10:
        score += 2
    elif weight_loss >= 5:
        score += 1

    if _boolean_flag(inputs, "acute_disease_no_intake_over_5_days"):
        score += 2

    if score == 0:
        interpretation = "low malnutrition risk by MUST"
    elif score == 1:
        interpretation = "medium malnutrition risk by MUST"
    else:
        interpretation = "high malnutrition risk by MUST"

    return result(metadata, score, "points", interpretation)


def nrs_2002_nutritional_risk_screening(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = _integer_range(inputs, "impaired_nutritional_status", 0, 3)
    score += _integer_range(inputs, "disease_severity", 0, 3)
    if _non_negative_number(inputs, "age_years") >= 70:
        score += 1

    interpretation = (
        "nutritional risk present by NRS-2002"
        if score >= 3
        else "nutritional risk not indicated by NRS-2002"
    )
    return result(metadata, score, "points", interpretation)


def nutritional_risk_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    albumin_g_l = _positive_number(inputs, "albumin_g_dl") * 10
    current_weight = _positive_number(inputs, "current_weight_kg")
    usual_weight = _positive_number(inputs, "usual_weight_kg")

    score = 1.519 * albumin_g_l + 41.7 * (current_weight / usual_weight)
    if score > 100:
        risk = "no nutritional risk"
    elif score >= 97.5:
        risk = "mild nutritional risk"
    elif score >= 83.5:
        risk = "moderate nutritional risk"
    else:
        risk = "severe nutritional risk"

    return result(metadata, score, "points", f"NRI: {risk}.")


def geriatric_nutritional_risk_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    albumin_g_l = _positive_number(inputs, "albumin_g_dl") * 10
    current_weight = _positive_number(inputs, "current_weight_kg")
    ideal_weight = _positive_number(inputs, "ideal_weight_kg")
    weight_ratio = min(current_weight / ideal_weight, 1.0)

    score = 1.489 * albumin_g_l + 41.7 * weight_ratio
    if score > 98:
        risk = "no nutrition-related risk"
    elif score >= 92:
        risk = "low nutrition-related risk"
    elif score >= 82:
        risk = "moderate nutrition-related risk"
    else:
        risk = "major nutrition-related risk"

    return result(metadata, score, "points", f"GNRI: {risk}.")


def refeeding_syndrome_risk_nice(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bmi = _positive_number(inputs, "bmi")
    weight_loss = _non_negative_number(inputs, "unintentional_weight_loss_percent")
    intake_days = _non_negative_number(inputs, "little_or_no_nutritional_intake_days")
    low_electrolytes = _boolean_flag(inputs, "low_potassium_phosphate_or_magnesium_before_feeding")
    alcohol_or_drugs = _boolean_flag(inputs, "alcohol_misuse_or_relevant_drugs")

    major_criteria_met = sum(
        (
            bmi < 16,
            weight_loss > 15,
            intake_days > 10,
            low_electrolytes,
        )
    )
    minor_criteria_met = sum(
        (
            bmi < 18.5,
            weight_loss > 10,
            intake_days > 5,
            alcohol_or_drugs,
        )
    )
    high_risk = major_criteria_met >= 1 or minor_criteria_met >= 2

    value = {
        "high_risk": high_risk,
        "major_criteria_met": major_criteria_met,
        "minor_criteria_met": minor_criteria_met,
    }
    interpretation = (
        "NICE refeeding risk: high risk criteria met."
        if high_risk
        else "NICE refeeding risk: high risk criteria not met."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=interpretation,
    )


def feverpain_sore_throat_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = 0
    for key in (
        "fever_past_24h",
        "purulence",
        "attend_rapidly_3_days_or_less",
        "severely_inflamed_tonsils",
        "no_cough_or_coryza",
    ):
        if _boolean_flag(inputs, key):
            score += 1

    if score <= 1:
        interpretation = "low likelihood by FeverPAIN score"
    elif score <= 3:
        interpretation = "intermediate likelihood by FeverPAIN score"
    else:
        interpretation = "high likelihood by FeverPAIN score"

    return result(metadata, score, "points", interpretation)


def crohns_disease_activity_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    sex = str(inputs.get("sex", "")).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be one of: female, male")

    abdominal_mass = _integer_range(inputs, "abdominal_mass", 0, 5)
    if abdominal_mass not in {0, 2, 5}:
        raise ValueError("abdominal_mass must be one of: 0, 2, 5")

    current_weight = _positive_number(inputs, "current_weight_kg")
    standard_weight = _positive_number(inputs, "standard_weight_kg")
    hematocrit_standard = 47 if sex == "male" else 42
    hematocrit_deficit = max(0.0, hematocrit_standard - _non_negative_number(inputs, "hematocrit_percent"))
    weight_deficit_percent = max(0.0, (1 - (current_weight / standard_weight)) * 100)

    score = (
        2 * _integer_range(inputs, "liquid_stools_7_days", 0, 999)
        + 5 * _integer_range(inputs, "abdominal_pain_sum_7_days", 0, 21)
        + 7 * _integer_range(inputs, "general_wellbeing_sum_7_days", 0, 28)
        + 20 * _integer_range(inputs, "complications_count", 0, 99)
        + (30 if _boolean_flag(inputs, "antidiarrheal_or_opiate") else 0)
        + 10 * abdominal_mass
        + 6 * hematocrit_deficit
        + weight_deficit_percent
    )

    if score < 150:
        activity = "remission"
    elif score < 220:
        activity = "mild activity"
    elif score <= 450:
        activity = "moderate to severe activity"
    else:
        activity = "severe activity"
    return result(metadata, score, "points", f"CDAI Crohn disease activity: {activity}.")


def simple_endoscopic_score_crohns_disease(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "segments" not in inputs:
        raise KeyError("segments")
    segments = inputs["segments"]
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must be a non-empty list")

    allowed_segments = {"ileum", "right_colon", "transverse_colon", "left_colon", "rectum"}
    seen_segments: set[str] = set()
    segment_scores: dict[str, int] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segments[{index}] must be an object")
        name = str(segment.get("name", "")).strip().lower()
        if name not in allowed_segments:
            allowed = ", ".join(sorted(allowed_segments))
            raise ValueError(f"segments[{index}].name must be one of: {allowed}")
        if name in seen_segments:
            raise ValueError(f"duplicate SES-CD segment: {name}")
        seen_segments.add(name)

        segment_scores[name] = sum(
            _integer_range(segment, key, 0, 3)
            for key in ("ulcer_size", "ulcerated_surface", "affected_surface", "narrowing")
        )

    total_score = sum(segment_scores.values())
    value = {"total_score": total_score, "segment_scores": segment_scores}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation="SES-CD endoscopic activity score; higher scores indicate more severe endoscopic activity.",
    )


def montreal_classification_crohns_disease(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age = _non_negative_number(inputs, "age_at_diagnosis_years")
    if age <= 16:
        age_code = "A1"
    elif age <= 40:
        age_code = "A2"
    else:
        age_code = "A3"

    location = str(inputs.get("location", "")).strip().lower()
    if location not in {"l1", "l2", "l3"}:
        raise ValueError("location must be one of: l1, l2, l3")
    location_code = location.upper()
    upper_gi_modifier = _boolean_flag(inputs, "upper_gi_modifier")
    if upper_gi_modifier:
        location_code = f"{location_code}+L4"

    behavior = str(inputs.get("behavior", "")).strip().lower()
    if behavior not in {"b1", "b2", "b3"}:
        raise ValueError("behavior must be one of: b1, b2, b3")
    behavior_code = behavior.upper()
    perianal_modifier = _boolean_flag(inputs, "perianal_modifier")
    if perianal_modifier:
        behavior_code = f"{behavior_code}p"

    classification = f"{age_code} {location_code} {behavior_code}"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "age": age_code,
            "location": location_code,
            "behavior": behavior_code,
            "classification": classification,
        },
        unit="classification",
        interpretation=f"Montreal Crohn disease classification: {classification}.",
    )


def montreal_classification_ulcerative_colitis(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    extent = str(inputs.get("extent", "")).strip().lower()
    if extent not in {"e1", "e2", "e3"}:
        raise ValueError("extent must be one of: e1, e2, e3")

    severity = str(inputs.get("severity", "")).strip().lower()
    if severity not in {"s0", "s1", "s2", "s3"}:
        raise ValueError("severity must be one of: s0, s1, s2, s3")

    extent_code = extent.upper()
    severity_code = severity.upper()
    classification = f"{extent_code} {severity_code}"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "extent": extent_code,
            "severity": severity_code,
            "classification": classification,
        },
        unit="classification",
        interpretation=f"Montreal ulcerative colitis classification: {classification}.",
    )


def boston_bowel_preparation_scale(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    segment_scores = {
        key: _integer_range(inputs, key, 0, 3)
        for key in ("right_colon", "transverse_colon", "left_colon")
    }
    total_score = sum(segment_scores.values())
    adequate_preparation = total_score >= 6 and min(segment_scores.values()) >= 2
    value = {
        "total_score": total_score,
        "segment_scores": segment_scores,
        "adequate_preparation": adequate_preparation,
    }
    interpretation = (
        "BBPS bowel preparation: adequate by total score and segment minimum."
        if adequate_preparation
        else "BBPS bowel preparation: inadequate by total score or segment minimum."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=interpretation,
    )


def controlling_nutritional_status_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    albumin = _positive_number(inputs, "albumin_g_dl")
    if albumin >= 3.5:
        albumin_points = 0
    elif albumin >= 3.0:
        albumin_points = 2
    elif albumin >= 2.5:
        albumin_points = 4
    else:
        albumin_points = 6

    lymphocytes = _positive_number(inputs, "total_lymphocytes_per_mm3")
    if lymphocytes >= 1600:
        lymphocyte_points = 0
    elif lymphocytes >= 1200:
        lymphocyte_points = 1
    elif lymphocytes >= 800:
        lymphocyte_points = 2
    else:
        lymphocyte_points = 3

    cholesterol = _positive_number(inputs, "total_cholesterol_mg_dl")
    if cholesterol >= 180:
        cholesterol_points = 0
    elif cholesterol >= 140:
        cholesterol_points = 1
    elif cholesterol >= 100:
        cholesterol_points = 2
    else:
        cholesterol_points = 3

    total_score = albumin_points + lymphocyte_points + cholesterol_points
    if total_score <= 1:
        severity = "normal nutritional status"
    elif total_score <= 4:
        severity = "mild undernutrition"
    elif total_score <= 8:
        severity = "moderate undernutrition"
    else:
        severity = "severe undernutrition"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "total_score": total_score,
            "albumin_points": albumin_points,
            "lymphocyte_points": lymphocyte_points,
            "cholesterol_points": cholesterol_points,
        },
        unit="points",
        interpretation=f"CONUT nutritional status: {severity}.",
    )


def ulcerative_colitis_endoscopic_index_severity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = (
        _integer_range(inputs, "vascular_pattern", 0, 2)
        + _integer_range(inputs, "bleeding", 0, 3)
        + _integer_range(inputs, "erosions_ulcers", 0, 3)
    )
    if score <= 1:
        severity = "minimal endoscopic activity"
    elif score <= 4:
        severity = "mild to moderate endoscopic activity"
    else:
        severity = "severe endoscopic activity"
    return result(metadata, score, "points", f"UCEIS: {severity}.")


def rutgeerts_score_postoperative_crohn_recurrence(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = str(inputs.get("grade", "")).strip().lower()
    labels = {
        "i0": "no lesions",
        "i1": "five or fewer aphthous lesions",
        "i2": "more than five aphthous lesions or larger anastomotic lesions",
        "i3": "diffuse aphthous ileitis with inflamed mucosa",
        "i4": "diffuse inflammation with large ulcers, nodules, or narrowing",
    }
    if grade not in labels:
        raise ValueError("grade must be one of: i0, i1, i2, i3, i4")

    recurrence = grade in {"i2", "i3", "i4"}
    value = {"grade": grade, "endoscopic_recurrence": recurrence}
    interpretation = f"Rutgeerts score {grade}: {labels[grade]}; {'recurrence threshold met' if recurrence else 'below recurrence threshold'}."
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="grade",
        interpretation=interpretation,
    )


def glim_malnutrition_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    phenotypic = any(
        _boolean_flag(inputs, key)
        for key in ("weight_loss", "low_bmi", "reduced_muscle_mass")
    )
    etiologic = any(
        _boolean_flag(inputs, key)
        for key in ("reduced_food_intake_or_assimilation", "inflammation_or_disease_burden")
    )
    malnutrition = phenotypic and etiologic
    if not malnutrition:
        severity = "not classified"
    elif _boolean_flag(inputs, "severe_phenotypic_criterion"):
        severity = "severe"
    else:
        severity = "moderate"
    value = {"malnutrition": malnutrition, "severity": severity}
    interpretation = f"GLIM malnutrition criteria: {severity}."
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=interpretation,
    )


def mayo_score_ulcerative_colitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _integer_range(inputs, key, 0, 3)
        for key in (
            "stool_frequency",
            "rectal_bleeding",
            "endoscopic_findings",
            "physician_global_assessment",
        )
    )
    if score <= 2:
        activity = "remission or minimal activity"
    elif score <= 5:
        activity = "mild activity"
    elif score <= 10:
        activity = "moderate activity"
    else:
        activity = "severe activity"
    return result(metadata, score, "points", f"Mayo ulcerative colitis activity: {activity}.")


def partial_mayo_score_ulcerative_colitis(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = sum(
        _integer_range(inputs, key, 0, 3)
        for key in (
            "stool_frequency",
            "rectal_bleeding",
            "physician_global_assessment",
        )
    )
    if score <= 1:
        activity = "remission or minimal activity"
    elif score <= 4:
        activity = "mild activity"
    elif score <= 6:
        activity = "moderate activity"
    else:
        activity = "severe activity"
    return result(metadata, score, "points", f"Partial Mayo ulcerative colitis activity: {activity}.")


def simple_clinical_colitis_activity_index(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = (
        _integer_range(inputs, "daytime_stool_frequency", 0, 3)
        + _integer_range(inputs, "nocturnal_stool_frequency", 0, 2)
        + _integer_range(inputs, "urgency", 0, 3)
        + _integer_range(inputs, "blood_in_stool", 0, 3)
        + _integer_range(inputs, "general_wellbeing", 0, 4)
        + _integer_range(inputs, "extracolonic_manifestations", 0, 4)
    )
    activity = "active disease likely" if score >= 5 else "clinical remission more likely"
    return result(metadata, score, "points", f"SCCAI ulcerative colitis activity: {activity}.")


def harvey_bradshaw_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_range(inputs, "general_wellbeing", 0, 4)
        + _integer_range(inputs, "abdominal_pain", 0, 3)
        + _integer_range(inputs, "liquid_stools_per_day", 0, 99)
        + _integer_range(inputs, "abdominal_mass", 0, 3)
        + _integer_range(inputs, "complications_count", 0, 99)
    )
    if score < 5:
        activity = "remission"
    elif score <= 7:
        activity = "mild activity"
    elif score <= 16:
        activity = "moderate activity"
    else:
        activity = "severe activity"
    return result(metadata, score, "points", f"Harvey-Bradshaw Crohn disease activity: {activity}.")


def modified_ct_severity_index_acute_pancreatitis(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    inflammation = _integer_range(inputs, "pancreatic_inflammation", 0, 4)
    if inflammation not in {0, 2, 4}:
        raise ValueError("pancreatic_inflammation must be one of: 0, 2, 4")

    necrosis_percent = _non_negative_number(inputs, "pancreatic_necrosis_percent")
    if necrosis_percent > 100:
        raise ValueError("pancreatic_necrosis_percent must be between 0 and 100")
    if necrosis_percent == 0:
        necrosis = 0
    elif necrosis_percent <= 30:
        necrosis = 2
    else:
        necrosis = 4

    score = inflammation + necrosis
    if _boolean_flag(inputs, "extrapancreatic_complications"):
        score += 2

    if score <= 2:
        severity = "mild"
    elif score <= 6:
        severity = "moderate"
    else:
        severity = "severe"
    return result(metadata, score, "points", f"Modified CT Severity Index acute pancreatitis: {severity}.")


def revised_atlanta_acute_pancreatitis_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    organ_failure = str(inputs.get("organ_failure", "")).strip().lower()
    if organ_failure not in {"none", "transient", "persistent"}:
        raise ValueError("organ_failure must be one of: none, transient, persistent")
    complications = _boolean_flag(inputs, "local_or_systemic_complications")

    if organ_failure == "persistent":
        classification = "severe"
    elif organ_failure == "transient" or complications:
        classification = "moderately severe"
    else:
        classification = "mild"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"classification": classification, "organ_failure": organ_failure, "complications": complications},
        unit="",
        interpretation=f"Revised Atlanta acute pancreatitis classification: {classification}.",
    )


def ulcerative_colitis_baron_endoscopic_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_range(inputs, "grade", 0, 3)
    labels = {
        0: "normal mucosa",
        1: "mild abnormality",
        2: "moderate abnormality",
        3: "severe abnormality",
    }
    return result(metadata, grade, "grade", f"Baron endoscopic score grade {grade}: {labels[grade]}.")


def west_haven_hepatic_encephalopathy_grade(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grade = _integer_range(inputs, "grade", 0, 4)
    labels = {
        0: "minimal or no clinically apparent encephalopathy",
        1: "mild hepatic encephalopathy",
        2: "moderate hepatic encephalopathy",
        3: "severe hepatic encephalopathy",
        4: "coma",
    }
    return result(metadata, grade, "grade", f"West Haven hepatic encephalopathy grade {grade}: {labels[grade]}.")


def kings_college_criteria_acute_liver_failure(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    etiology_group = str(inputs.get("etiology_group", "")).strip().lower()
    if etiology_group not in {"acetaminophen", "non_acetaminophen"}:
        raise ValueError("etiology_group must be 'acetaminophen' or 'non_acetaminophen'")

    if etiology_group == "acetaminophen":
        arterial_ph = _positive_number(inputs, "arterial_ph")
        inr = _positive_number(inputs, "inr")
        creatinine = _positive_number(inputs, "creatinine_mg_dl")
        encephalopathy_grade = _integer_range(inputs, "encephalopathy_grade", 0, 4)
        ph_criterion = arterial_ph < 7.3
        triad_criterion = inr > 6.5 and creatinine > 3.4 and encephalopathy_grade >= 3
        criteria_met = ph_criterion or triad_criterion
        value = {
            "criteria_met": criteria_met,
            "ph_criterion": ph_criterion,
            "triad_criterion": triad_criterion,
        }
    else:
        inr = _positive_number(inputs, "inr")
        direct_inr_criterion = inr > 6.5
        age = _non_negative_number(inputs, "age_years")
        minor_criteria = 0
        if age < 10 or age > 40:
            minor_criteria += 1
        if _boolean_flag(inputs, "unfavorable_etiology"):
            minor_criteria += 1
        if _non_negative_number(inputs, "jaundice_to_encephalopathy_days") > 7:
            minor_criteria += 1
        if inr > 3.5:
            minor_criteria += 1
        if _positive_number(inputs, "bilirubin_mg_dl") > 17.5:
            minor_criteria += 1
        criteria_met = direct_inr_criterion or minor_criteria >= 3
        value = {
            "criteria_met": criteria_met,
            "direct_inr_criterion": direct_inr_criterion,
            "minor_criteria_met": minor_criteria,
        }

    interpretation = (
        "King's College Criteria met; poor prognosis and urgent transplant-center assessment."
        if criteria_met
        else "King's College Criteria not met."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="criteria",
        interpretation=interpretation,
    )


def forns_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _positive_number(inputs, "age_years")
    ggt = _positive_number(inputs, "ggt_u_l")
    cholesterol = _positive_number(inputs, "cholesterol_mg_dl")
    platelets = _positive_number(inputs, "platelets_10e9_l")
    score = 7.811 - (3.131 * math.log(platelets)) + (0.781 * math.log(ggt)) + (3.467 * math.log(age)) - (
        0.014 * cholesterol
    )

    if score < 4.2:
        interpretation = "Forns Index: low probability of significant fibrosis."
    elif score > 6.9:
        interpretation = "Forns Index: higher probability of significant fibrosis."
    else:
        interpretation = "Forns Index: indeterminate zone for significant fibrosis."
    return result(metadata, score, "points", interpretation)


def adenoma_detection_rate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    adenoma_colonoscopies = _integer_range(inputs, "colonoscopies_with_at_least_one_adenoma", 0, 10_000_000)
    total_colonoscopies = _integer_range(inputs, "total_screening_colonoscopies", 1, 10_000_000)
    if adenoma_colonoscopies > total_colonoscopies:
        raise ValueError("colonoscopies_with_at_least_one_adenoma cannot exceed total_screening_colonoscopies")
    value = adenoma_colonoscopies / total_colonoscopies * 100
    return result(metadata, value, "%", "adenoma detection rate for screening colonoscopy quality monitoring")


def tokyo_guidelines_cholangitis_severity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    organ_keys = (
        "cardiovascular_dysfunction",
        "neurologic_dysfunction",
        "respiratory_dysfunction",
        "renal_dysfunction",
        "hepatic_dysfunction",
        "hematologic_dysfunction",
    )
    moderate_keys = (
        "wbc_abnormal",
        "fever_39c_or_higher",
        "age_75_or_older",
        "bilirubin_mg_dl_5_or_higher",
        "albumin_low",
    )
    organ_dysfunction = any(_boolean_flag(inputs, key) for key in organ_keys)
    moderate_criteria = sum(_boolean_flag(inputs, key) for key in moderate_keys)

    if organ_dysfunction:
        grade = "III"
        severity = "severe"
    elif moderate_criteria >= 2:
        grade = "II"
        severity = "moderate"
    else:
        grade = "I"
        severity = "mild"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "grade": grade,
            "organ_dysfunction_present": organ_dysfunction,
            "moderate_criteria_met": moderate_criteria,
        },
        unit="grade",
        interpretation=f"Tokyo Guidelines acute cholangitis severity Grade {grade}: {severity}.",
    )


def tokyo_guidelines_cholecystitis_severity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    organ_keys = (
        "cardiovascular_dysfunction",
        "neurologic_dysfunction",
        "respiratory_dysfunction",
        "renal_dysfunction",
        "hepatic_dysfunction",
        "hematologic_dysfunction",
    )
    moderate_keys = (
        "wbc_over_18000",
        "palpable_tender_mass_right_upper_quadrant",
        "symptom_duration_over_72h",
        "marked_local_inflammation",
    )
    organ_dysfunction = any(_boolean_flag(inputs, key) for key in organ_keys)
    moderate_criteria = sum(_boolean_flag(inputs, key) for key in moderate_keys)

    if organ_dysfunction:
        grade = "III"
        severity = "severe"
    elif moderate_criteria >= 1:
        grade = "II"
        severity = "moderate"
    else:
        grade = "I"
        severity = "mild"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "grade": grade,
            "organ_dysfunction_present": organ_dysfunction,
            "moderate_criteria_met": moderate_criteria,
        },
        unit="grade",
        interpretation=f"Tokyo Guidelines acute cholecystitis severity Grade {grade}: {severity}.",
    )


def ibs_severity_scoring_system(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    domain_keys = (
        "abdominal_pain_severity",
        "abdominal_pain_frequency",
        "abdominal_distension",
        "bowel_habit_dissatisfaction",
        "life_interference",
    )
    scores = {key: _integer_range(inputs, key, 0, 100) for key in domain_keys}
    total_score = sum(scores.values())
    if total_score < 75:
        severity = "remission or minimal symptoms"
    elif total_score < 175:
        severity = "mild IBS severity"
    elif total_score < 300:
        severity = "moderate IBS severity"
    else:
        severity = "severe IBS severity"
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=total_score,
        unit="points",
        interpretation=f"IBS-SSS total {total_score}: {severity}.",
    )


def hisort_autoimmune_pancreatitis_criteria(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    histology = _boolean_flag(inputs, "histology_diagnostic")
    typical_imaging = _boolean_flag(inputs, "typical_pancreatic_imaging")
    elevated_igg4 = _boolean_flag(inputs, "elevated_igg4")
    atypical_imaging = _boolean_flag(inputs, "atypical_pancreatic_imaging_after_negative_malignancy_workup")
    other_organ = _boolean_flag(inputs, "other_organ_involvement")
    steroid_response = _boolean_flag(inputs, "steroid_response_after_negative_malignancy_workup")

    typical_imaging_and_serology = typical_imaging and elevated_igg4
    steroid_response_pathway = atypical_imaging and steroid_response and (elevated_igg4 or other_organ)
    diagnostic_support = histology or typical_imaging_and_serology or steroid_response_pathway
    value = {
        "diagnostic_support": diagnostic_support,
        "histology_diagnostic": histology,
        "typical_imaging_and_serology": typical_imaging_and_serology,
        "steroid_response_pathway": steroid_response_pathway,
    }
    interpretation = (
        "HISORt criteria supports autoimmune pancreatitis."
        if diagnostic_support
        else "HISORt criteria do not support autoimmune pancreatitis from the supplied coded findings."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="criteria",
        interpretation=interpretation,
    )


def tips_survival_from_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    risk_score = number(inputs, "risk_score")
    days = _integer_range(inputs, "days", 1, 365)
    baseline_survival = {90: 0.8937267354472074, 365: 0.8243888922170506}
    if days not in baseline_survival:
        raise ValueError("days must be one of the supported baseline horizons: 90 or 365")
    survival = baseline_survival[days] ** math.exp(risk_score)
    return result(metadata, survival, "probability", f"TIPS predicted {days}-day survival probability.")


def tips_survival_probability(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    creatinine = _positive_number(inputs, "creatinine_mg_dl")
    bilirubin = _positive_number(inputs, "bilirubin_mg_dl")
    inr = _positive_number(inputs, "inr")
    cause = str(inputs["cause"]).strip().lower()
    if cause not in {"viral_or_other", "alcoholic_or_cholestatic"}:
        raise ValueError("cause must be 'viral_or_other' or 'alcoholic_or_cholestatic'")
    cause_term = 0.6425877148153819 if cause == "viral_or_other" else 0.0
    risk_score = 0.957 * math.log(creatinine) + 0.378 * math.log(bilirubin) + 1.12 * math.log(inr) + cause_term
    days = _integer_range(inputs, "days", 1, 365)
    survival_result = tips_survival_from_risk_score(metadata, {"risk_score": risk_score, "days": days})
    value = {"risk_score": round(risk_score, 4), "survival_probability": survival_result.value}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="probability",
        interpretation=f"TIPS predicted {days}-day survival probability.",
    )


def severe_lower_gi_bleeding_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    keys = (
        "pulse_100_or_more",
        "systolic_bp_115_or_less",
        "syncope",
        "nontender_abdomen",
        "rectal_bleeding_first_4_hours",
        "aspirin_use",
        "three_or_more_comorbidities",
    )
    score = sum(_boolean_flag(inputs, key) for key in keys)
    risk_by_score = {0: 6, 1: 10, 2: 21, 3: 43, 4: 65, 5: 79, 6: 84, 7: 84}
    if score >= 4:
        category = "high risk"
    elif score >= 2:
        category = "moderate risk"
    else:
        category = "low risk"
    value = {"score": score, "risk_percent": risk_by_score[score]}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="points",
        interpretation=f"Severe lower GI bleeding risk score: {category}.",
    )


def bclc_hepatocellular_carcinoma_stage(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ecog = _integer_range(inputs, "ecog_performance_status", 0, 4)
    child_pugh = str(inputs["child_pugh_class"]).strip().upper()
    if child_pugh not in {"A", "B", "C"}:
        raise ValueError("child_pugh_class must be A, B, or C")
    single_tumor = _boolean_flag(inputs, "single_tumor")
    tumor_count = _integer_range(inputs, "tumor_count", 0, 100)
    largest_tumor = _positive_number(inputs, "largest_tumor_cm")
    portal_invasion = _boolean_flag(inputs, "portal_invasion")
    extrahepatic_spread = _boolean_flag(inputs, "extrahepatic_spread")

    if ecog > 2 or child_pugh == "C":
        stage, label = "D", "terminal stage"
    elif portal_invasion or extrahepatic_spread or ecog in {1, 2}:
        stage, label = "C", "advanced stage"
    elif not single_tumor and tumor_count > 3:
        stage, label = "B", "intermediate stage"
    elif single_tumor and tumor_count == 1 and largest_tumor <= 2 and ecog == 0 and child_pugh == "A":
        stage, label = "0", "very early stage"
    else:
        stage, label = "A", "early stage"

    value = {"stage": stage, "label": label}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="stage",
        interpretation=f"BCLC hepatocellular carcinoma {label}.",
    )
