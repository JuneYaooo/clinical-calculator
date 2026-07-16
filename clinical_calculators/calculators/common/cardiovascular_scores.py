from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _bool_input(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    raise ValueError(f"{key} must be a boolean or 0/1")


def _non_negative_number(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def _integer_input(inputs: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = _non_negative_number(inputs, key)
    if not value.is_integer():
        raise ValueError(f"{key} must be an integer")
    integer_value = int(value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def _sex_input(inputs: dict[str, Any], key: str = "sex") -> str:
    if key not in inputs:
        raise KeyError(key)

    sex = str(inputs[key]).strip().lower()
    if sex not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female'")
    return sex


def _cha2ds2_vasc_interpretation(score: int, sex: str) -> str:
    if score == 0 or (sex == "female" and score == 1):
        risk_group = "low stroke risk"
    elif score == 1 or (sex == "female" and score == 2):
        risk_group = "intermediate stroke risk"
    else:
        risk_group = "high stroke risk"

    return (
        f"{risk_group} support by CHA2DS2-VASc score; anticoagulation decision depends on current guidelines, "
        "patient context, and bleeding risk assessment"
    )


def cha2ds2_vasc_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")
    sex = _sex_input(inputs)

    score = 0
    score += int(_bool_input(inputs, "congestive_heart_failure"))
    score += int(_bool_input(inputs, "hypertension"))
    if age_years >= 75:
        score += 2
    elif age_years >= 65:
        score += 1
    score += int(_bool_input(inputs, "diabetes"))
    score += 2 * int(_bool_input(inputs, "stroke_tia_thromboembolism"))
    score += int(_bool_input(inputs, "vascular_disease"))
    score += int(sex == "female")

    return result(metadata, score, "points", _cha2ds2_vasc_interpretation(score, sex))


def has_bled_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age_years = number(inputs, "age_years")

    score = 0
    score += int(_bool_input(inputs, "hypertension"))
    score += int(_bool_input(inputs, "abnormal_renal_function"))
    score += int(_bool_input(inputs, "abnormal_liver_function"))
    score += int(_bool_input(inputs, "stroke_history"))
    score += int(_bool_input(inputs, "bleeding_history_or_predisposition"))
    score += int(_bool_input(inputs, "labile_inr"))
    score += int(age_years > 65)
    score += int(_bool_input(inputs, "drugs_predisposing_bleeding"))
    score += int(_bool_input(inputs, "alcohol_use"))

    if score >= 3:
        interpretation = (
            "high bleeding risk by HAS-BLED score; identify and address modifiable bleeding risks, "
            "but this score is not a reason alone to withhold anticoagulation"
        )
    else:
        interpretation = (
            "not high bleeding risk by HAS-BLED score; continue individualized anticoagulation assessment"
        )

    return result(metadata, score, "points", interpretation)


def ankle_brachial_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    ankle_pressures = [
        number(inputs, key)
        for key in ("dorsalis_pedis_sbp", "posterior_tibial_sbp")
        if key in inputs
    ]
    if not ankle_pressures:
        ankle_pressures = [
            number(inputs, key)
            for key in (
                "left_dorsalis_pedis_sbp",
                "left_posterior_tibial_sbp",
                "right_dorsalis_pedis_sbp",
                "right_posterior_tibial_sbp",
            )
            if key in inputs
        ]
    brachial_pressures = [
        number(inputs, key)
        for key in ("brachial_sbp", "left_brachial_sbp", "right_brachial_sbp")
        if key in inputs
    ]
    if not ankle_pressures:
        raise KeyError("ankle systolic pressure")
    if not brachial_pressures:
        raise KeyError("brachial systolic pressure")

    ankle = max(ankle_pressures)
    brachial = max(brachial_pressures)
    if brachial <= 0:
        raise ValueError("brachial systolic pressure must be positive")
    abi = ankle / brachial
    if abi < 0.9:
        interpretation = "abnormal ABI compatible with peripheral artery disease"
    elif abi <= 1.4:
        interpretation = "normal or borderline ABI range; interpret with clinical context"
    else:
        interpretation = "high ABI suggests noncompressible vessels"
    return result(metadata, abi, "ratio", interpretation)


def simon_broome_familial_hypercholesterolemia_criteria(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    age_years = number(inputs, "age_years")
    if age_years < 0:
        raise ValueError("age_years must be non-negative")

    cholesterol_high = False
    if "total_cholesterol_mmol_l" in inputs:
        total_cholesterol = number(inputs, "total_cholesterol_mmol_l")
        if total_cholesterol < 0:
            raise ValueError("total_cholesterol_mmol_l must be non-negative")
        cholesterol_high = cholesterol_high or (
            total_cholesterol > 6.7 if age_years < 16 else total_cholesterol > 7.5
        )
    if "ldl_cholesterol_mmol_l" in inputs:
        ldl_cholesterol = number(inputs, "ldl_cholesterol_mmol_l")
        if ldl_cholesterol < 0:
            raise ValueError("ldl_cholesterol_mmol_l must be non-negative")
        cholesterol_high = cholesterol_high or (
            ldl_cholesterol > 4.0 if age_years < 16 else ldl_cholesterol > 4.9
        )
    if "total_cholesterol_mmol_l" not in inputs and "ldl_cholesterol_mmol_l" not in inputs:
        raise KeyError("total_cholesterol_mmol_l or ldl_cholesterol_mmol_l")

    if not cholesterol_high:
        return result(
            metadata,
            0,
            "classification",
            "Simon Broome criteria not met: cholesterol threshold is not met.",
        )

    definite_feature = _bool_input(inputs, "tendon_xanthomas_patient_or_relative") or _bool_input(
        inputs, "pathogenic_mutation"
    )
    if definite_feature:
        return result(
            metadata,
            2,
            "classification",
            "Simon Broome definite familial hypercholesterolemia criteria met.",
        )

    possible_feature = _bool_input(inputs, "family_history_premature_mi") or _bool_input(
        inputs, "family_history_high_cholesterol"
    )
    if possible_feature:
        return result(
            metadata,
            1,
            "classification",
            "Simon Broome possible familial hypercholesterolemia criteria met.",
        )

    return result(
        metadata,
        0,
        "classification",
        "Simon Broome criteria not met: cholesterol threshold met without qualifying genetic, xanthoma, or family-history criteria.",
    )


def rutherford_chronic_limb_ischemia_classification(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    category = _integer_input(inputs, "category", 0, 6)
    labels = {
        0: "asymptomatic",
        1: "mild claudication",
        2: "moderate claudication",
        3: "severe claudication",
        4: "ischemic rest pain",
        5: "minor tissue loss",
        6: "major tissue loss",
    }
    return result(
        metadata,
        category,
        "category",
        f"Rutherford chronic limb ischemia category {category}: {labels[category]}.",
    )


def _severity_rank(label: str) -> int:
    return {"none": 0, "mild": 1, "moderate": 2, "severe": 3}[label]


def aortic_stenosis_severity_grading(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grades: list[str] = []

    if "peak_velocity_m_s" in inputs:
        velocity = _non_negative_number(inputs, "peak_velocity_m_s")
        if velocity >= 4.0:
            grades.append("severe")
        elif velocity >= 3.0:
            grades.append("moderate")
        elif velocity >= 2.6:
            grades.append("mild")
        else:
            grades.append("none")

    if "mean_gradient_mm_hg" in inputs:
        gradient = _non_negative_number(inputs, "mean_gradient_mm_hg")
        if gradient >= 40:
            grades.append("severe")
        elif gradient >= 20:
            grades.append("moderate")
        else:
            grades.append("mild")

    if "aortic_valve_area_cm2" in inputs:
        valve_area = _non_negative_number(inputs, "aortic_valve_area_cm2")
        if valve_area <= 1.0:
            grades.append("severe")
        elif valve_area <= 1.5:
            grades.append("moderate")
        else:
            grades.append("mild")

    if not grades:
        raise KeyError("peak_velocity_m_s, mean_gradient_mm_hg, or aortic_valve_area_cm2")

    severity = max(grades, key=_severity_rank)
    discordant = len(set(grades)) > 1
    note = " Discordant parameters; integrate flow state and full echocardiographic context." if discordant else ""
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"severity": severity, "discordant": discordant},
        unit="classification",
        interpretation=f"Aortic stenosis severity grading: {severity}.{note}",
    )


def mitral_regurgitation_severity_grading(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    grades: list[str] = []

    if "vena_contracta_width_cm" in inputs:
        width = _non_negative_number(inputs, "vena_contracta_width_cm")
        if width >= 0.7:
            grades.append("severe")
        elif width < 0.3:
            grades.append("mild")
        else:
            grades.append("moderate")

    if "eroa_cm2" in inputs:
        eroa = _non_negative_number(inputs, "eroa_cm2")
        if eroa >= 0.4:
            grades.append("severe")
        elif eroa < 0.2:
            grades.append("mild")
        else:
            grades.append("moderate")

    if "regurgitant_volume_ml" in inputs:
        volume = _non_negative_number(inputs, "regurgitant_volume_ml")
        if volume >= 60:
            grades.append("severe")
        elif volume < 30:
            grades.append("mild")
        else:
            grades.append("moderate")

    if "regurgitant_fraction_percent" in inputs:
        fraction = _non_negative_number(inputs, "regurgitant_fraction_percent")
        if fraction >= 50:
            grades.append("severe")
        elif fraction < 30:
            grades.append("mild")
        else:
            grades.append("moderate")

    if not grades:
        raise KeyError(
            "vena_contracta_width_cm, eroa_cm2, regurgitant_volume_ml, or regurgitant_fraction_percent"
        )

    severity = max(grades, key=_severity_rank)
    discordant = len(set(grades)) > 1
    note = " Discordant parameters; integrate mechanism, image quality, and clinical context." if discordant else ""
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"severity": severity, "discordant": discordant},
        unit="classification",
        interpretation=f"Mitral regurgitation severity grading: {severity}.{note}",
    )


def ehra_atrial_fibrillation_symptom_scale(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "class" not in inputs:
        raise KeyError("class")

    ehra_class = str(inputs["class"]).strip().lower()
    labels = {
        "1": "no symptoms",
        "2a": "mild symptoms not affecting normal daily activity",
        "2b": "moderate troublesome symptoms; normal daily activity is not affected",
        "3": "severe symptoms affecting normal daily activity",
        "4": "disabling symptoms; normal daily activity discontinued",
    }
    if ehra_class not in labels:
        raise ValueError("class must be one of: 1, 2a, 2b, 3, 4")

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=ehra_class,
        unit="class",
        interpretation=f"EHRA atrial fibrillation symptom class {ehra_class}: {labels[ehra_class]}.",
    )


def adult_blood_pressure_category(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    systolic = _non_negative_number(inputs, "systolic_bp_mm_hg")
    diastolic = _non_negative_number(inputs, "diastolic_bp_mm_hg")
    if systolic == 0 or diastolic == 0:
        raise ValueError("blood pressure values must be positive")

    if systolic > 180 or diastolic > 120:
        category = "severe hypertension"
    elif systolic >= 140 or diastolic >= 90:
        category = "stage 2 hypertension"
    elif systolic >= 130 or diastolic >= 80:
        category = "stage 1 hypertension"
    elif systolic >= 120 and diastolic < 80:
        category = "elevated blood pressure"
    else:
        category = "normal blood pressure"

    value = {"category": category, "systolic_bp_mm_hg": systolic, "diastolic_bp_mm_hg": diastolic}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="classification",
        interpretation=f"Adult blood pressure category: {category}.",
    )
