from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from clinical_calculators.calculators._helpers import result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    numeric_value = float(value)
    if numeric_value < 0:
        raise ValueError(f"{key} must be nonnegative")
    return numeric_value


def _signed_number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _positive_number(inputs: dict[str, Any], key: str) -> float:
    numeric_value = _number(inputs, key)
    if numeric_value <= 0:
        raise ValueError(f"{key} must be positive")
    return numeric_value


def _boolean(inputs: dict[str, Any], key: str) -> bool:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _string_choice(inputs: dict[str, Any], key: str, choices: set[str]) -> str:
    if key not in inputs:
        raise KeyError(key)

    value = str(inputs[key]).strip().lower()
    if value not in choices:
        raise ValueError(f"{key} must be one of {sorted(choices)}")
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


def _integer_in_set(inputs: dict[str, Any], key: str, accepted_values: set[int]) -> int:
    if key not in inputs:
        raise KeyError(key)

    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")

    integer_value = int(numeric_value)
    if integer_value not in accepted_values:
        raise ValueError(f"{key} must be one of {sorted(accepted_values)}")
    return integer_value


def _component_score(value: Any, key: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    numeric_value = float(value)
    if not numeric_value.is_integer():
        raise ValueError(f"{key} must be an integer from {minimum} to {maximum}")

    integer_value = int(numeric_value)
    if integer_value < minimum or integer_value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return integer_value


def apgar_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    if "components" not in inputs:
        raise KeyError("components")

    components = inputs["components"]
    if isinstance(components, (str, bytes)) or not isinstance(components, Sequence):
        raise ValueError("components must be a sequence of five integer scores")
    if len(components) != 5:
        raise ValueError("components must contain exactly five scores")

    score = sum(_component_score(value, "components", 0, 2) for value in components)
    if score >= 7:
        interpretation = "reassuring/normal Apgar score"
    elif score >= 4:
        interpretation = "moderately abnormal Apgar score"
    else:
        interpretation = "low/critical Apgar score"

    return result(metadata, score, "points", interpretation)


def bishop_cervix_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "dilation", 0, 3)
        + _integer_in_range(inputs, "effacement", 0, 3)
        + _integer_in_range(inputs, "station", 0, 3)
        + _integer_in_range(inputs, "consistency", 0, 2)
        + _integer_in_range(inputs, "position", 0, 2)
    )

    if score >= 8:
        interpretation = "favorable Bishop score"
    elif score >= 6:
        interpretation = "intermediate Bishop score"
    else:
        interpretation = "unfavorable Bishop score"

    return result(metadata, score, "points", interpretation)


def braden_pressure_ulcer_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "sensory_perception", 1, 4)
        + _integer_in_range(inputs, "moisture", 1, 4)
        + _integer_in_range(inputs, "activity", 1, 4)
        + _integer_in_range(inputs, "mobility", 1, 4)
        + _integer_in_range(inputs, "nutrition", 1, 4)
        + _integer_in_range(inputs, "friction_shear", 1, 3)
    )

    if score <= 9:
        interpretation = "very high pressure ulcer risk by Braden score"
    elif score <= 12:
        interpretation = "high pressure ulcer risk by Braden score"
    elif score <= 14:
        interpretation = "moderate pressure ulcer risk by Braden score"
    elif score <= 18:
        interpretation = "mild pressure ulcer risk by Braden score"
    else:
        interpretation = "no/low risk by Braden score"

    return result(metadata, score, "points", interpretation)


def morse_fall_risk_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_set(inputs, "history_of_falling", {0, 25})
        + _integer_in_set(inputs, "secondary_diagnosis", {0, 15})
        + _integer_in_set(inputs, "ambulatory_aid", {0, 15, 30})
        + _integer_in_set(inputs, "iv_or_heparin_lock", {0, 20})
        + _integer_in_set(inputs, "gait", {0, 10, 20})
        + _integer_in_set(inputs, "mental_status", {0, 15})
    )

    if score <= 24:
        interpretation = "low fall risk by Morse score"
    elif score <= 44:
        interpretation = "moderate fall risk by Morse score"
    else:
        interpretation = "high fall risk by Morse score"

    return result(metadata, score, "points", interpretation)


def gestational_diabetes_screening_interpretation(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    if "strategy" not in inputs:
        raise KeyError("strategy")

    strategy = str(inputs["strategy"]).strip().lower()
    if strategy == "one_step_75g_iadpsg":
        values = {
            "fasting_mg_dl": _number(inputs, "fasting_mg_dl"),
            "one_hour_mg_dl": _number(inputs, "one_hour_mg_dl"),
            "two_hour_mg_dl": _number(inputs, "two_hour_mg_dl"),
        }
        thresholds = {
            "fasting_mg_dl": 92,
            "one_hour_mg_dl": 180,
            "two_hour_mg_dl": 153,
        }
        abnormal = {
            key: values[key] >= threshold
            for key, threshold in thresholds.items()
        }
        abnormal_count = sum(abnormal.values())
        diagnostic = abnormal_count >= 1
        interpretation = (
            "diagnostic for gestational diabetes by one-step 75-g IADPSG thresholds"
            if diagnostic
            else "not diagnostic for gestational diabetes by one-step 75-g IADPSG thresholds"
        )
        value = {
            "strategy": strategy,
            "thresholds_mg_dl": thresholds,
            "abnormal_values": abnormal,
            "abnormal_count": abnormal_count,
            "diagnostic_for_gdm": diagnostic,
        }
    elif strategy == "two_step_carpenter_coustan":
        screen_value = _number(inputs, "screen_one_hour_mg_dl")
        screen_threshold = 140
        screen_positive = screen_value >= screen_threshold
        thresholds = {
            "fasting_mg_dl": 95,
            "one_hour_mg_dl": 180,
            "two_hour_mg_dl": 155,
            "three_hour_mg_dl": 140,
        }
        if screen_positive:
            values = {key: _number(inputs, key) for key in thresholds}
            abnormal = {
                key: values[key] >= threshold
                for key, threshold in thresholds.items()
            }
            abnormal_count = sum(abnormal.values())
            diagnostic = abnormal_count >= 2
            interpretation = (
                "diagnostic for gestational diabetes by two-step Carpenter-Coustan thresholds"
                if diagnostic
                else "screen positive but not diagnostic by two-step Carpenter-Coustan thresholds"
            )
        else:
            abnormal = {key: False for key in thresholds}
            abnormal_count = 0
            diagnostic = False
            interpretation = "screen negative by two-step 50-g glucose challenge threshold"
        value = {
            "strategy": strategy,
            "screen_threshold_mg_dl": screen_threshold,
            "screen_positive": screen_positive,
            "thresholds_mg_dl": thresholds,
            "abnormal_values": abnormal,
            "abnormal_count": abnormal_count,
            "diagnostic_for_gdm": diagnostic,
        }
    else:
        raise ValueError("strategy must be one_step_75g_iadpsg or two_step_carpenter_coustan")

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="",
        interpretation=interpretation,
    )


def estimated_fetal_weight_hadlock(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bpd_cm = _positive_number(inputs, "bpd_cm")
    hc_cm = _positive_number(inputs, "hc_cm")
    ac_cm = _positive_number(inputs, "ac_cm")
    fl_cm = _positive_number(inputs, "fl_cm")

    log10_efw = (
        1.3596
        - 0.00386 * ac_cm * fl_cm
        + 0.0064 * hc_cm
        + 0.00061 * bpd_cm * ac_cm
        + 0.0424 * ac_cm
        + 0.174 * fl_cm
    )
    efw_g = 10 ** log10_efw

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "formula": "hadlock_bpd_hc_ac_fl",
            "log10_efw": round(log10_efw, 4),
            "estimated_fetal_weight_g": round(efw_g, 1),
        },
        unit="g",
        interpretation="Hadlock BPD-HC-AC-FL estimated fetal weight",
    )


def amniotic_fluid_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    afi_cm = (
        _number(inputs, "quadrant_1_cm")
        + _number(inputs, "quadrant_2_cm")
        + _number(inputs, "quadrant_3_cm")
        + _number(inputs, "quadrant_4_cm")
    )

    if afi_cm <= 5:
        interpretation = "oligohydramnios range by amniotic fluid index"
    elif afi_cm >= 24:
        interpretation = "polyhydramnios range by amniotic fluid index"
    else:
        interpretation = "normal amniotic fluid index range"

    return result(metadata, afi_cm, "cm", interpretation)


def single_deepest_pocket(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    pocket_cm = _number(inputs, "single_deepest_pocket_cm")

    if pocket_cm < 2:
        interpretation = "oligohydramnios range by single deepest pocket"
    elif pocket_cm >= 8:
        interpretation = "polyhydramnios range by single deepest pocket"
    else:
        interpretation = "normal single deepest pocket range"

    return result(metadata, pocket_cm, "cm", interpretation)


def preeclampsia_severe_features_checklist(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    platelets = _number(inputs, "platelets_per_microliter")
    serum_creatinine = _number(inputs, "serum_creatinine_mg_dl")

    feature_flags = {
        "severe_range_blood_pressure": _boolean(inputs, "severe_range_blood_pressure_confirmed"),
        "thrombocytopenia": platelets < 100000,
        "renal_insufficiency": serum_creatinine > 1.1
        or _boolean(inputs, "creatinine_doubled_from_baseline"),
        "impaired_liver_function": _boolean(inputs, "liver_transaminases_twice_normal")
        or _boolean(inputs, "severe_persistent_ruq_epigastric_pain"),
        "pulmonary_edema": _boolean(inputs, "pulmonary_edema"),
        "new_onset_headache_unresponsive": _boolean(inputs, "new_onset_headache_unresponsive"),
        "visual_symptoms": _boolean(inputs, "visual_symptoms"),
    }
    severe_features = [key for key, present in feature_flags.items() if present]
    has_severe_features = bool(severe_features)
    interpretation = (
        "preeclampsia severe features identified"
        if has_severe_features
        else "preeclampsia severe features not identified"
    )

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "has_severe_features": has_severe_features,
            "severe_feature_count": len(severe_features),
            "severe_features": severe_features,
            "criteria": feature_flags,
        },
        unit="",
        interpretation=interpretation,
    )


def downes_respiratory_distress_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = (
        _integer_in_range(inputs, "respiratory_rate", 0, 2)
        + _integer_in_range(inputs, "cyanosis", 0, 2)
        + _integer_in_range(inputs, "air_entry", 0, 2)
        + _integer_in_range(inputs, "grunting", 0, 2)
        + _integer_in_range(inputs, "retractions", 0, 2)
    )

    if score >= 7:
        interpretation = "severe respiratory distress by Downes score"
    elif score >= 4:
        interpretation = "moderate respiratory distress by Downes score"
    else:
        interpretation = "mild respiratory distress by Downes score"

    return result(metadata, score, "points", interpretation)


def snappe_ii_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    mean_bp = _number(inputs, "mean_blood_pressure_mm_hg")
    temperature = _number(inputs, "lowest_temperature_c")
    pao2_fio2 = _number(inputs, "pao2_fio2_ratio")
    serum_ph = _number(inputs, "lowest_serum_ph")
    urine_output = _number(inputs, "urine_output_ml_kg_hr")
    five_minute_apgar = _integer_in_range(inputs, "five_minute_apgar", 0, 10)
    birth_weight = _number(inputs, "birth_weight_g")
    if birth_weight <= 0:
        raise ValueError("birth_weight_g must be positive")

    if mean_bp < 20:
        mean_bp_points = 19
    elif mean_bp <= 29:
        mean_bp_points = 9
    else:
        mean_bp_points = 0

    if temperature < 35:
        temperature_points = 15
    elif temperature <= 35.6:
        temperature_points = 8
    else:
        temperature_points = 0

    if pao2_fio2 < 0.3:
        pao2_fio2_points = 28
    elif pao2_fio2 < 1:
        pao2_fio2_points = 16
    elif pao2_fio2 <= 2.49:
        pao2_fio2_points = 5
    else:
        pao2_fio2_points = 0
    if serum_ph < 7.10:
        ph_points = 16
    elif serum_ph <= 7.19:
        ph_points = 7
    else:
        ph_points = 0
    seizure_points = 19 if _boolean(inputs, "multiple_seizures") else 0
    if urine_output < 0.1:
        urine_points = 18
    elif urine_output <= 0.9:
        urine_points = 5
    else:
        urine_points = 0
    if birth_weight < 750:
        birth_weight_points = 17
    elif birth_weight <= 999:
        birth_weight_points = 10
    else:
        birth_weight_points = 0
    sga_points = 12 if _boolean(inputs, "small_for_gestational_age_below_3rd_percentile") else 0
    apgar_points = 18 if five_minute_apgar < 7 else 0

    component_points = {
        "mean_blood_pressure": mean_bp_points,
        "lowest_temperature": temperature_points,
        "pao2_fio2_ratio": pao2_fio2_points,
        "lowest_serum_ph": ph_points,
        "multiple_seizures": seizure_points,
        "urine_output": urine_points,
        "birth_weight": birth_weight_points,
        "small_for_gestational_age": sga_points,
        "five_minute_apgar": apgar_points,
    }
    score = sum(component_points.values())
    if score >= 80:
        interpretation = "very high SNAPPE-II physiologic/perinatal severity score"
    elif score >= 40:
        interpretation = "high SNAPPE-II physiologic/perinatal severity score"
    else:
        interpretation = "lower SNAPPE-II physiologic/perinatal severity score"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "component_points": component_points},
        unit="points",
        interpretation=interpretation,
    )


def iota_simple_rules(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    malignant_feature_keys = (
        "irregular_solid_tumor",
        "ascites",
        "at_least_four_papillary_structures",
        "irregular_multilocular_solid_tumor_ge_100mm",
        "very_strong_blood_flow",
    )
    benign_feature_keys = (
        "unilocular_cyst",
        "solid_components_under_7mm",
        "acoustic_shadows",
        "smooth_multilocular_tumor_under_100mm",
        "no_blood_flow",
    )

    malignant_features = [key for key in malignant_feature_keys if _boolean(inputs, key)]
    benign_features = [key for key in benign_feature_keys if _boolean(inputs, key)]
    has_malignant = bool(malignant_features)
    has_benign = bool(benign_features)

    if has_malignant and not has_benign:
        classification = "malignant"
        interpretation = "IOTA Simple Rules classify the adnexal mass as malignant."
    elif has_benign and not has_malignant:
        classification = "benign"
        interpretation = "IOTA Simple Rules classify the adnexal mass as benign."
    else:
        classification = "inconclusive"
        interpretation = "IOTA Simple Rules are inconclusive with the supplied features."

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "classification": classification,
            "malignant_feature_count": len(malignant_features),
            "benign_feature_count": len(benign_features),
            "malignant_features": malignant_features,
            "benign_features": benign_features,
        },
        unit="classification",
        interpretation=interpretation,
    )


def roma_ovarian_malignancy_algorithm(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    status = _string_choice(inputs, "menopausal_status", {"premenopausal", "postmenopausal"})
    he4 = _positive_number(inputs, "he4_pmol_l")
    ca125 = _positive_number(inputs, "ca125_u_ml")

    if status == "premenopausal":
        predictive_index = -12.0 + 2.38 * math.log(he4) + 0.0626 * math.log(ca125)
        cutoff = 11.4
    else:
        predictive_index = -8.09 + 1.04 * math.log(he4) + 0.732 * math.log(ca125)
        cutoff = 29.9
    roma_percent = math.exp(predictive_index) / (1 + math.exp(predictive_index)) * 100
    high_risk = roma_percent >= cutoff

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "menopausal_status": status,
            "predictive_index": round(predictive_index, 4),
            "roma_percent": round(roma_percent, 4),
            "high_risk_cutoff_percent": cutoff,
            "high_risk": high_risk,
        },
        unit="%",
        interpretation=(
            "high risk ROMA result for epithelial ovarian malignancy"
            if high_risk
            else "low risk ROMA result for epithelial ovarian malignancy"
        ),
    )


def rotterdam_pcos_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    criteria = {
        "oligo_or_anovulation": _boolean(inputs, "oligo_or_anovulation"),
        "clinical_or_biochemical_hyperandrogenism": _boolean(inputs, "clinical_or_biochemical_hyperandrogenism"),
        "polycystic_ovarian_morphology": _boolean(inputs, "polycystic_ovarian_morphology"),
    }
    other_causes_excluded = _boolean(inputs, "other_causes_excluded")
    met_criteria = [key for key, present in criteria.items() if present]
    criteria_count = len(met_criteria)
    meets_rotterdam = other_causes_excluded and criteria_count >= 2

    if meets_rotterdam:
        interpretation = "meets Rotterdam PCOS criteria after exclusion of other causes"
    elif not other_causes_excluded:
        interpretation = "Rotterdam PCOS criteria requires exclusion of other causes"
    else:
        interpretation = "does not meet Rotterdam PCOS criteria"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "meets_rotterdam_pcos": meets_rotterdam,
            "criteria_count": criteria_count,
            "met_criteria": met_criteria,
            "other_causes_excluded": other_causes_excluded,
            "criteria": criteria,
        },
        unit="",
        interpretation=interpretation,
    )


def modified_ferriman_gallwey_score(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    regions = (
        "upper_lip",
        "chin",
        "chest",
        "upper_back",
        "lower_back",
        "upper_abdomen",
        "lower_abdomen",
        "upper_arms",
        "thighs",
    )
    score = sum(_integer_in_range(inputs, region, 0, 4) for region in regions)
    interpretation = (
        "hirsutism range by modified Ferriman-Gallwey score"
        if score >= 8
        else "below common hirsutism threshold by modified Ferriman-Gallwey score"
    )
    return result(metadata, score, "points", interpretation)


def pop_q_stage(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    tvl = _positive_number(inputs, "tvl_cm")
    required_points = {
        "aa_cm": _signed_number(inputs, "aa_cm"),
        "ba_cm": _signed_number(inputs, "ba_cm"),
        "c_cm": _signed_number(inputs, "c_cm"),
        "ap_cm": _signed_number(inputs, "ap_cm"),
        "bp_cm": _signed_number(inputs, "bp_cm"),
    }
    points = dict(required_points)
    if "d_cm" in inputs:
        points["d_cm"] = _signed_number(inputs, "d_cm")

    leading_edge = max(points.values())
    stage_zero = (
        required_points["aa_cm"] == -3
        and required_points["ba_cm"] == -3
        and required_points["ap_cm"] == -3
        and required_points["bp_cm"] == -3
        and required_points["c_cm"] <= -(tvl - 2)
    )

    if stage_zero:
        stage = "0"
        description = "no prolapse"
    elif leading_edge < -1:
        stage = "I"
        description = "leading edge more than 1 cm above the hymen"
    elif leading_edge <= 1:
        stage = "II"
        description = "leading edge within 1 cm proximal or distal to the hymen"
    elif leading_edge < tvl - 2:
        stage = "III"
        description = "leading edge more than 1 cm beyond the hymen but less than TVL minus 2 cm"
    else:
        stage = "IV"
        description = "complete or near-complete vaginal eversion"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "stage": stage,
            "leading_edge_cm": leading_edge,
            "tvl_cm": tvl,
            "points_cm": points,
        },
        unit="stage",
        interpretation=f"POP-Q stage {stage}: {description}.",
    )


def ovarian_reserve_assessment_afc_amh(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    afc = _integer_in_range(inputs, "afc", 0, 200)
    amh = _number(inputs, "amh_ng_ml")
    if amh < 0:
        raise ValueError("amh_ng_ml must be nonnegative")

    afc_cutoff = int(inputs.get("afc_cutoff", 7))
    amh_cutoff = float(inputs.get("amh_cutoff_ng_ml", 1.1))
    if afc_cutoff < 0 or amh_cutoff < 0:
        raise ValueError("cutoffs must be nonnegative")

    low_afc = afc < afc_cutoff
    low_amh = amh < amh_cutoff
    abnormal = low_afc or low_amh
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "afc": afc,
            "amh_ng_ml": amh,
            "afc_cutoff": afc_cutoff,
            "amh_cutoff_ng_ml": amh_cutoff,
            "low_afc": low_afc,
            "low_amh": low_amh,
            "abnormal_ovarian_reserve_test": abnormal,
        },
        unit="",
        interpretation=(
            "reduced ovarian reserve marker present by AFC/AMH thresholds"
            if abnormal
            else "AFC/AMH thresholds do not indicate reduced ovarian reserve"
        ),
    )


def poseidon_criteria(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    age = _number(inputs, "age_years")
    afc = _integer_in_range(inputs, "afc", 0, 200)
    amh = _number(inputs, "amh_ng_ml")
    if age < 0 or amh < 0:
        raise ValueError("age_years and amh_ng_ml must be nonnegative")

    low_reserve = afc < 5 or amh < 1.2
    older = age >= 35
    previous_oocytes = None
    subgroup = ""
    if "previous_oocytes_retrieved" in inputs:
        previous_oocytes = _integer_in_range(inputs, "previous_oocytes_retrieved", 0, 200)
        if previous_oocytes < 4:
            subgroup = "A"
        elif previous_oocytes <= 9:
            subgroup = "B"

    if low_reserve:
        group = "4" if older else "3"
    elif subgroup:
        group = ("2" if older else "1") + subgroup
    else:
        group = None

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "group": group,
            "age_category": ">=35" if older else "<35",
            "reserve_status": "low" if low_reserve else "adequate",
            "previous_oocytes_retrieved": previous_oocytes,
            "afc_low_threshold": 5,
            "amh_low_threshold_ng_ml": 1.2,
        },
        unit="group",
        interpretation=(
            f"POSEIDON group {group} low-prognosis category"
            if group
            else "not classified as a POSEIDON low-prognosis group by supplied criteria"
        ),
    )


def gardner_blastocyst_grading(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    expansion = _integer_in_range(inputs, "expansion_grade", 1, 6)
    icm = _string_choice(inputs, "inner_cell_mass_grade", {"a", "b", "c"}).upper()
    te = _string_choice(inputs, "trophectoderm_grade", {"a", "b", "c"}).upper()
    stages = {
        1: "early blastocyst",
        2: "blastocyst",
        3: "full blastocyst",
        4: "expanded blastocyst",
        5: "hatching blastocyst",
        6: "hatched blastocyst",
    }
    grade = f"{expansion}{icm}{te}"
    if icm == "A" and te == "A":
        quality = "top morphology"
    elif "C" in {icm, te}:
        quality = "lower morphology"
    else:
        quality = "intermediate morphology"

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={
            "grade": grade,
            "expansion_grade": expansion,
            "stage": stages[expansion],
            "inner_cell_mass_grade": icm,
            "trophectoderm_grade": te,
            "morphology_category": quality,
        },
        unit="grade",
        interpretation=f"Gardner blastocyst grade {grade}: {stages[expansion]}, {quality}.",
    )


def modified_obstetric_early_warning_score(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    respiratory_rate = _number(inputs, "respiratory_rate")
    spo2 = _number(inputs, "oxygen_saturation_percent")
    temperature = _number(inputs, "temperature_c")
    pulse = _number(inputs, "pulse_bpm")
    systolic = _number(inputs, "systolic_bp_mm_hg")
    diastolic = _number(inputs, "diastolic_bp_mm_hg")

    if spo2 < 0 or spo2 > 100:
        raise ValueError("oxygen_saturation_percent must be between 0 and 100")

    respiratory_points = 2 if respiratory_rate >= 21 or respiratory_rate < 10 else 0
    spo2_points = 2 if spo2 < 95 else 0
    temperature_points = 2 if temperature >= 37.5 or temperature < 36 else 0
    pulse_points = 2 if pulse >= 120 or pulse < 50 else 0
    systolic_points = 2 if systolic >= 140 or systolic < 90 else 0
    diastolic_points = 2 if diastolic >= 90 else 0
    component_points = {
        "respiratory_rate": respiratory_points,
        "oxygen_saturation": spo2_points,
        "temperature": temperature_points,
        "pulse": pulse_points,
        "systolic_bp": systolic_points,
        "diastolic_bp": diastolic_points,
    }
    score = sum(component_points.values())
    interpretation = (
        "high concern by modified obstetric early warning score"
        if score >= 2
        else "no modified obstetric early warning trigger from supplied vitals"
    )

    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value={"score": score, "component_points": component_points},
        unit="points",
        interpretation=interpretation,
    )
