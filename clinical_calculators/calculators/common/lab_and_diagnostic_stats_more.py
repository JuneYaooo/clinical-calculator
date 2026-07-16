from __future__ import annotations

from collections.abc import Sequence
import math
import statistics
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _positive(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _fraction(inputs: dict[str, Any], key: str) -> float:
    value = number(inputs, key)
    if value < 0 or value > 1:
        raise ValueError(f"{key} must be a fraction from 0 to 1")
    return value


def _percent_count(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return 100 * numerator / denominator


def absolute_neutrophil_count(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "wbc_10e9_l") * (
        number(inputs, "segmented_neutrophils_percent") / 100 + number(inputs, "bands_percent") / 100
    )
    return result(metadata, value, "10^9/L", "absolute neutrophil count")


def absolute_eosinophil_count(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "wbc_10e9_l") * number(inputs, "eosinophils_percent") / 100
    return result(metadata, value, "10^9/L", "absolute eosinophil count")


def absolute_lymphocyte_count(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "wbc_10e9_l") * number(inputs, "lymphocytes_percent") / 100
    return result(metadata, value, "10^9/L", "absolute lymphocyte count")


def absolute_reticulocyte_count(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "reticulocytes_percent") * number(inputs, "hematocrit_percent") / 45
    return result(metadata, value, "% corrected", "absolute/corrected reticulocyte count estimate")


def reticulocyte_production_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (
        number(inputs, "hematocrit_percent")
        / 45
        * number(inputs, "reticulocytes_percent")
        / _positive(inputs, "maturation_correction")
    )
    return result(metadata, value, "index", "reticulocyte production index")


def positive_likelihood_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _fraction(inputs, "sensitivity") / (1 - _fraction(inputs, "specificity"))
    return result(metadata, value, "ratio", "positive likelihood ratio")


def negative_likelihood_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (1 - _fraction(inputs, "sensitivity")) / _fraction(inputs, "specificity")
    return result(metadata, value, "ratio", "negative likelihood ratio")


def likelihood_ratios_from_sensitivity_specificity(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    sensitivity = _fraction(inputs, "sensitivity")
    specificity = _fraction(inputs, "specificity")
    if specificity == 1:
        raise ValueError("specificity must be less than 1 for LR+")
    if specificity == 0:
        raise ValueError("specificity must be greater than 0 for LR-")
    value = {
        "positive_likelihood_ratio": round(sensitivity / (1 - specificity), 4),
        "negative_likelihood_ratio": round((1 - sensitivity) / specificity, 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="ratio",
        interpretation="likelihood ratios from sensitivity and specificity",
    )


def sensitivity_from_counts(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "true_positive"), number(inputs, "true_positive") + number(inputs, "false_negative"))
    return result(metadata, value, "%", "sensitivity")


def specificity_from_counts(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "true_negative"), number(inputs, "true_negative") + number(inputs, "false_positive"))
    return result(metadata, value, "%", "specificity")


def positive_predictive_value(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "true_positive"), number(inputs, "true_positive") + number(inputs, "false_positive"))
    return result(metadata, value, "%", "positive predictive value")


def negative_predictive_value(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "true_negative"), number(inputs, "true_negative") + number(inputs, "false_negative"))
    return result(metadata, value, "%", "negative predictive value")


def false_negative_rate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "false_negative"), number(inputs, "true_positive") + number(inputs, "false_negative"))
    return result(metadata, value, "%", "false negative rate")


def false_positive_rate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _percent_count(number(inputs, "false_positive"), number(inputs, "false_positive") + number(inputs, "true_negative"))
    return result(metadata, value, "%", "false positive rate")


def diagnostic_accuracy_from_proportions(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 100 * (_fraction(inputs, "true_positive") + _fraction(inputs, "true_negative"))
    return result(metadata, value, "%", "diagnostic accuracy from true positive and true negative proportions")


def true_positive_from_sensitivity_prevalence(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _fraction(inputs, "sensitivity") * _fraction(inputs, "prevalence")
    return result(metadata, value, "proportion", "true positive proportion")


def false_negative_from_sensitivity_prevalence(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (1 - _fraction(inputs, "sensitivity")) * _fraction(inputs, "prevalence")
    return result(metadata, value, "proportion", "false negative proportion")


def false_positive_from_specificity_prevalence(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = (1 - _fraction(inputs, "specificity")) * (1 - _fraction(inputs, "prevalence"))
    return result(metadata, value, "proportion", "false positive proportion")


def true_negative_from_specificity_prevalence(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _fraction(inputs, "specificity") * (1 - _fraction(inputs, "prevalence"))
    return result(metadata, value, "proportion", "true negative proportion")


def odds_from_probability(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    probability = _fraction(inputs, "probability")
    if probability == 1:
        raise ValueError("probability must be less than 1")
    return result(metadata, probability / (1 - probability), "odds", "odds from probability")


def probability_from_odds(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    odds = _positive(inputs, "odds")
    return result(metadata, odds / (1 + odds), "probability", "probability from odds")


def posttest_odds_from_likelihood_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _positive(inputs, "pretest_odds") * _positive(inputs, "likelihood_ratio")
    return result(metadata, value, "odds", "post-test odds")


def positive_predictive_value_from_prevalence(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    prevalence = _fraction(inputs, "prevalence")
    sensitivity = _fraction(inputs, "sensitivity")
    specificity = _fraction(inputs, "specificity")
    numerator = prevalence * sensitivity
    denominator = numerator + ((1 - prevalence) * (1 - specificity))
    return result(metadata, 100 * numerator / denominator, "%", "positive predictive value")


def negative_predictive_value_from_prevalence(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    prevalence = _fraction(inputs, "prevalence")
    sensitivity = _fraction(inputs, "sensitivity")
    specificity = _fraction(inputs, "specificity")
    numerator = (1 - prevalence) * specificity
    denominator = numerator + (prevalence * (1 - sensitivity))
    return result(metadata, 100 * numerator / denominator, "%", "negative predictive value")


def number_needed_to_treat(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = 1 / _positive(inputs, "absolute_benefit_increase")
    return result(metadata, value, "patients", "number needed to treat")


def number_needed_to_treat_or_harm_from_event_rates(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    control_event_rate = _fraction(inputs, "control_event_rate")
    treatment_event_rate = _fraction(inputs, "treatment_event_rate")
    absolute_risk_difference = control_event_rate - treatment_event_rate
    if absolute_risk_difference == 0:
        raise ValueError("event rates must differ to calculate NNT or NNH")
    value = {
        "absolute_risk_difference": round(absolute_risk_difference, 4),
        "type": "NNT" if absolute_risk_difference > 0 else "NNH",
        "number_needed": round(1 / abs(absolute_risk_difference), 4),
    }
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="patients",
        interpretation="number needed to treat or harm from event rates",
    )


def sample_size_two_proportions(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    alpha = _fraction(inputs, "alpha")
    power = _fraction(inputs, "power")
    p1 = _fraction(inputs, "proportion_1")
    p2 = _fraction(inputs, "proportion_2")
    if alpha <= 0 or alpha >= 1:
        raise ValueError("alpha must be between 0 and 1")
    if power <= 0 or power >= 1:
        raise ValueError("power must be between 0 and 1")
    if p1 == p2:
        raise ValueError("proportion_1 and proportion_2 must differ")

    normal = statistics.NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_beta = normal.inv_cdf(power)
    pooled = (p1 + p2) / 2
    numerator = (
        z_alpha * math.sqrt(2 * pooled * (1 - pooled))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    n_per_group = math.ceil(numerator / ((p1 - p2) ** 2))
    value = {"n_per_group": n_per_group, "total_n": n_per_group * 2}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="participants",
        interpretation="normal-approximation sample size for comparing two independent proportions",
    )


def absolute_benefit_increase(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _fraction(inputs, "control_event_rate") - _fraction(inputs, "experimental_event_rate")
    return result(metadata, value, "proportion", "absolute benefit increase")


def relative_benefit_increase(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _fraction(inputs, "absolute_benefit_increase") / _positive(inputs, "control_event_rate")
    return result(metadata, value, "proportion", "relative benefit increase")


def ast_alt_ratio(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "ast_u_l") / _positive(inputs, "alt_u_l")
    return result(metadata, value, "ratio", "AST to ALT ratio")


def mentzer_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = number(inputs, "mcv_fl") / _positive(inputs, "rbc_10e12_l")
    if value < 13:
        interpretation = "less than 13; thalassemia trait pattern is more likely than iron deficiency pattern"
    elif value > 13:
        interpretation = "greater than 13; iron deficiency pattern is more likely than thalassemia trait pattern"
    else:
        interpretation = "borderline value; interpret with confirmatory testing"
    return result(metadata, value, "index", interpretation)


def soluble_transferrin_receptor_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    value = _positive(inputs, "stfr_mg_l") / math.log10(_positive(inputs, "ferritin_ng_ml"))
    return result(metadata, value, "index", "soluble transferrin receptor/log ferritin index")


def noise_dose_and_8_hour_twa(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    segments = inputs.get("segments")
    if not isinstance(segments, Sequence) or isinstance(segments, (str, bytes)):
        raise ValueError("segments must be a sequence of noise exposure segments")
    if not segments:
        raise ValueError("segments must contain at least one exposure segment")

    dose_fraction = 0.0
    included_segments = 0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segments[{index}] must be a mapping")
        level = float(segment["level_db_a"])
        duration = float(segment["duration_hours"])
        if duration < 0:
            raise ValueError(f"segments[{index}].duration_hours must be nonnegative")
        if level < 80 or duration == 0:
            continue
        allowed_hours = 8 * (2 ** ((90 - level) / 5))
        dose_fraction += duration / allowed_hours
        included_segments += 1

    dose_percent = 100 * dose_fraction
    twa = None if dose_percent == 0 else 16.61 * math.log10(dose_percent / 100) + 90
    value = {
        "dose_percent": round(dose_percent, 4),
        "twa_db_a": None if twa is None else round(twa, 4),
        "included_segments": included_segments,
    }
    interpretation = (
        "OSHA noise dose and 8-hour TWA using the 5 dB exchange rate."
        if twa is not None
        else "OSHA noise dose is 0% for the supplied segments at or above the integration threshold."
    )
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="% and dBA",
        interpretation=interpretation,
    )


def cadd_score_interpretation(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = number(inputs, "score")
    if score < 0:
        raise ValueError("score must be nonnegative")
    top_fraction = 10 ** (-score / 10)
    if score >= 30:
        label = "top 0.1% most deleterious scaled CADD scores"
    elif score >= 20:
        label = "top 1% most deleterious scaled CADD scores"
    elif score >= 10:
        label = "top 10% most deleterious scaled CADD scores"
    else:
        label = "below the top 10% scaled CADD threshold"
    value = {"score": round(score, 4), "top_fraction": round(top_fraction, 6)}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="PHRED-like scaled score",
        interpretation=f"CADD score interpretation: {label}.",
    )


def revel_score_interpretation(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    score = _fraction(inputs, "score")
    if score >= 0.75:
        classification = "supports pathogenicity"
    elif score <= 0.15:
        classification = "supports benignity"
    else:
        classification = "indeterminate by these rule thresholds"
    value = {"score": round(score, 4), "classification": classification}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="score",
        interpretation=f"REVEL score interpretation: {classification}.",
    )


def gerp_conservation_score_interpretation(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    score = number(inputs, "score")
    if score > 0:
        classification = "constrained/conserved"
    elif score < 0:
        classification = "not constrained by rejected-substitution score"
    else:
        classification = "neutral rejected-substitution score"
    value = {"score": round(score, 4), "classification": classification}
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=value,
        unit="rejected substitutions",
        interpretation=f"GERP conservation score interpretation: {classification}.",
    )
