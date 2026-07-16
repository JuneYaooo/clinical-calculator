import unittest

from clinical_calculators.calculators.common.lab_and_diagnostic_stats_more import (
    absolute_eosinophil_count,
    absolute_lymphocyte_count,
    absolute_neutrophil_count,
    absolute_reticulocyte_count,
    absolute_benefit_increase,
    ast_alt_ratio,
    cadd_score_interpretation,
    diagnostic_accuracy_from_proportions,
    false_negative_rate,
    false_negative_from_sensitivity_prevalence,
    false_positive_from_specificity_prevalence,
    false_positive_rate,
    gerp_conservation_score_interpretation,
    likelihood_ratios_from_sensitivity_specificity,
    mentzer_index,
    negative_likelihood_ratio,
    negative_predictive_value,
    negative_predictive_value_from_prevalence,
    noise_dose_and_8_hour_twa,
    number_needed_to_treat,
    odds_from_probability,
    posttest_odds_from_likelihood_ratio,
    positive_likelihood_ratio,
    positive_predictive_value,
    positive_predictive_value_from_prevalence,
    probability_from_odds,
    revel_score_interpretation,
    relative_benefit_increase,
    number_needed_to_treat_or_harm_from_event_rates,
    sample_size_two_proportions,
    sensitivity_from_counts,
    soluble_transferrin_receptor_index,
    specificity_from_counts,
    true_negative_from_specificity_prevalence,
    true_positive_from_sensitivity_prevalence,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str = "calculator") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_cn}",
        category="common",
        subspecialty="",
        scenario="",
        name_cn=name_cn,
        name_en="Calculator",
        inputs="",
        output="",
        formula="",
        interpretation="",
        purpose="",
        source_type="",
        source="",
        source_url="",
        channel="",
        evidence_tier="",
        commonness="",
        coverage_note="",
        clinical_note="",
        version="",
        entry_source="",
        source_group="",
        notes="",
    )


class CommonLabAndDiagnosticStatsMoreTest(unittest.TestCase):
    def test_absolute_blood_cell_counts(self):
        meta = metadata("cell count")

        self.assertAlmostEqual(
            absolute_neutrophil_count(
                meta, {"wbc_10e9_l": 8, "segmented_neutrophils_percent": 55, "bands_percent": 5}
            ).value,
            4.8,
            places=4,
        )
        self.assertAlmostEqual(absolute_eosinophil_count(meta, {"wbc_10e9_l": 8, "eosinophils_percent": 4}).value, 0.32)
        self.assertAlmostEqual(absolute_lymphocyte_count(meta, {"wbc_10e9_l": 8, "lymphocytes_percent": 30}).value, 2.4)
        self.assertAlmostEqual(
            absolute_reticulocyte_count(meta, {"reticulocytes_percent": 2.5, "hematocrit_percent": 30}).value,
            1.6667,
            places=4,
        )

    def test_reticulocyte_production_index_uses_maturation_correction(self):
        from clinical_calculators.calculators.common.lab_and_diagnostic_stats_more import reticulocyte_production_index

        calculation = reticulocyte_production_index(
            metadata("网织红细胞生成指数"),
            {"hematocrit_percent": 30, "reticulocytes_percent": 3, "maturation_correction": 1.5},
        )

        self.assertAlmostEqual(calculation.value, 1.3333, places=4)
        self.assertEqual(calculation.unit, "index")

    def test_likelihood_ratios_from_sensitivity_and_specificity(self):
        meta = metadata("likelihood")

        self.assertAlmostEqual(positive_likelihood_ratio(meta, {"sensitivity": 0.9, "specificity": 0.8}).value, 4.5)
        self.assertAlmostEqual(negative_likelihood_ratio(meta, {"sensitivity": 0.9, "specificity": 0.8}).value, 0.125)

    def test_predictive_values_from_prevalence_sensitivity_and_specificity(self):
        meta = metadata("predictive")

        self.assertAlmostEqual(
            positive_predictive_value_from_prevalence(
                meta, {"prevalence": 0.1, "sensitivity": 0.9, "specificity": 0.8}
            ).value,
            33.3333,
            places=4,
        )
        self.assertAlmostEqual(
            negative_predictive_value_from_prevalence(
                meta, {"prevalence": 0.1, "sensitivity": 0.9, "specificity": 0.8}
            ).value,
            98.6301,
            places=4,
        )

    def test_raw_count_diagnostic_statistics(self):
        meta = metadata("raw")

        self.assertEqual(sensitivity_from_counts(meta, {"true_positive": 90, "false_negative": 10}).value, 90)
        self.assertEqual(specificity_from_counts(meta, {"true_negative": 80, "false_positive": 20}).value, 80)
        self.assertEqual(positive_predictive_value(meta, {"true_positive": 90, "false_positive": 20}).value, 81.8182)
        self.assertEqual(negative_predictive_value(meta, {"true_negative": 80, "false_negative": 10}).value, 88.8889)
        self.assertEqual(false_negative_rate(meta, {"true_positive": 90, "false_negative": 10}).value, 10)
        self.assertEqual(false_positive_rate(meta, {"false_positive": 20, "true_negative": 80}).value, 20)

    def test_odds_probability_and_nnt(self):
        meta = metadata("odds")

        self.assertEqual(odds_from_probability(meta, {"probability": 0.2}).value, 0.25)
        self.assertEqual(probability_from_odds(meta, {"odds": 0.25}).value, 0.2)
        self.assertEqual(number_needed_to_treat(meta, {"absolute_benefit_increase": 0.2}).value, 5)

    def test_nnt_or_nnh_from_event_rates(self):
        meta = metadata("nnt")

        benefit = number_needed_to_treat_or_harm_from_event_rates(
            meta, {"control_event_rate": 0.3, "treatment_event_rate": 0.1}
        )
        harm = number_needed_to_treat_or_harm_from_event_rates(
            meta, {"control_event_rate": 0.1, "treatment_event_rate": 0.3}
        )

        self.assertEqual(benefit.value, {"absolute_risk_difference": 0.2, "type": "NNT", "number_needed": 5.0})
        self.assertEqual(harm.value, {"absolute_risk_difference": -0.2, "type": "NNH", "number_needed": 5.0})

    def test_prevalence_table_components_and_posttest_odds(self):
        meta = metadata("bayes")

        self.assertEqual(true_positive_from_sensitivity_prevalence(meta, {"sensitivity": 0.9, "prevalence": 0.1}).value, 0.09)
        self.assertEqual(false_negative_from_sensitivity_prevalence(meta, {"sensitivity": 0.9, "prevalence": 0.1}).value, 0.01)
        self.assertEqual(false_positive_from_specificity_prevalence(meta, {"specificity": 0.8, "prevalence": 0.1}).value, 0.18)
        self.assertEqual(true_negative_from_specificity_prevalence(meta, {"specificity": 0.8, "prevalence": 0.1}).value, 0.72)
        self.assertEqual(posttest_odds_from_likelihood_ratio(meta, {"pretest_odds": 0.25, "likelihood_ratio": 4}).value, 1.0)

    def test_combined_likelihood_ratios_and_accuracy(self):
        meta = metadata("diagnostic")

        lrs = likelihood_ratios_from_sensitivity_specificity(meta, {"sensitivity": 0.9, "specificity": 0.8})
        accuracy = diagnostic_accuracy_from_proportions(meta, {"true_positive": 0.09, "true_negative": 0.72})

        self.assertEqual(lrs.value, {"positive_likelihood_ratio": 4.5, "negative_likelihood_ratio": 0.125})
        self.assertEqual(accuracy.value, 81)
        self.assertEqual(accuracy.unit, "%")

    def test_sample_size_two_proportions_equal_allocation(self):
        result = sample_size_two_proportions(
            metadata("样本量：两比例比较"),
            {"alpha": 0.05, "power": 0.8, "proportion_1": 0.3, "proportion_2": 0.2},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["n_per_group"], 294)
        self.assertEqual(result.value["total_n"], 588)

    def test_benefit_ratios(self):
        meta = metadata("benefit")

        self.assertEqual(absolute_benefit_increase(meta, {"control_event_rate": 0.25, "experimental_event_rate": 0.15}).value, 0.1)
        self.assertEqual(relative_benefit_increase(meta, {"absolute_benefit_increase": 0.1, "control_event_rate": 0.25}).value, 0.4)

    def test_simple_hematology_and_liver_ratios(self):
        meta = metadata("ratios")

        self.assertEqual(ast_alt_ratio(meta, {"ast_u_l": 80, "alt_u_l": 40}).value, 2)
        self.assertEqual(mentzer_index(meta, {"mcv_fl": 70, "rbc_10e12_l": 5.6}).value, 12.5)
        self.assertEqual(soluble_transferrin_receptor_index(meta, {"stfr_mg_l": 5, "ferritin_ng_ml": 100}).value, 2.5)

    def test_noise_dose_and_8_hour_twa_uses_osha_five_db_exchange_rate(self):
        result = noise_dose_and_8_hour_twa(
            metadata("噪声剂量与8小时TWA"),
            {"segments": [{"level_db_a": 95, "duration_hours": 2}, {"level_db_a": 90, "duration_hours": 4}]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["dose_percent"], 100.0, places=4)
        self.assertAlmostEqual(result.value["twa_db_a"], 90.0, places=4)
        self.assertEqual(result.unit, "% and dBA")

    def test_cadd_score_interpretation_uses_phred_like_thresholds(self):
        result = cadd_score_interpretation(metadata("CADD评分解读"), {"score": 20})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 20)
        self.assertEqual(result.value["top_fraction"], 0.01)
        self.assertIn("top 1%", result.interpretation)

    def test_revel_score_interpretation_reports_pathogenic_support_threshold(self):
        result = revel_score_interpretation(metadata("REVEL评分解读"), {"score": 0.75})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 0.75)
        self.assertEqual(result.value["classification"], "supports pathogenicity")
        self.assertIn("pathogenicity", result.interpretation)

    def test_gerp_conservation_score_interpretation_reports_positive_constraint(self):
        result = gerp_conservation_score_interpretation(metadata("GERP保守性评分解读"), {"score": 4.2})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 4.2)
        self.assertEqual(result.value["classification"], "constrained/conserved")
        self.assertIn("conservation", result.interpretation)


if __name__ == "__main__":
    unittest.main()
