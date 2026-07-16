import unittest

from clinical_calculators.calculators.common.critical_care_scores import (
    akin_acute_kidney_injury_stage,
    apache_ii_score,
    asa_physical_status_classification,
    dn4_neuropathic_pain_screen,
    extrip_lithium_ectr_indication,
    icdsc_delirium_screening_checklist,
    news2_early_warning_score,
    nutric_score,
    peradeniya_organophosphorus_poisoning_scale,
    rass_sedation_agitation_score,
    rifle_acute_kidney_injury_classification,
    revised_trauma_score,
    saps_ii_score,
    sofa_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="critical care",
        scenario="unit test",
        name_cn=name_cn,
        name_en=name_en,
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


class CommonCriticalCareScoresTest(unittest.TestCase):
    def test_news2_severe_example_scores_nineteen(self):
        result = news2_early_warning_score(
            metadata("NEWS2早期预警评分", "NEWS2 Early Warning Score"),
            {
                "respiratory_rate": 30,
                "oxygen_saturation_percent": 90,
                "supplemental_oxygen": True,
                "temperature_c": 39.5,
                "systolic_bp": 85,
                "heart_rate": 140,
                "consciousness": "pain",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 19)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_peradeniya_organophosphorus_poisoning_scale_classifies_moderate_poisoning(self):
        result = peradeniya_organophosphorus_poisoning_scale(
            metadata("有机磷中毒严重度", "Organophosphate Poisoning Severity"),
            {
                "pupil_size": 1,
                "respiratory_rate": 2,
                "heart_rate": 1,
                "fasciculations": 1,
                "level_of_consciousness": 1,
                "seizures": 0,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 6)
        self.assertEqual(result.value["severity"], "moderate")
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_peradeniya_organophosphorus_poisoning_scale_rejects_binary_component_above_one(self):
        with self.assertRaisesRegex(ValueError, "seizures must be between 0 and 1"):
            peradeniya_organophosphorus_poisoning_scale(
                metadata("有机磷中毒严重度", "Organophosphate Poisoning Severity"),
                {
                    "pupil_size": 0,
                    "respiratory_rate": 0,
                    "heart_rate": 0,
                    "fasciculations": 0,
                    "level_of_consciousness": 0,
                    "seizures": 3,
                },
            )

    def test_sofa_component_scores_all_four_total_twenty_four(self):
        result = sofa_score(
            metadata("SOFA评分", "Sequential Organ Failure Assessment"),
            {
                "respiration": 4,
                "coagulation": 4,
                "liver": 4,
                "cardiovascular": 4,
                "cns": 4,
                "renal": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 24)
        self.assertEqual(result.unit, "points")
        self.assertIn("greater organ dysfunction", result.interpretation)

    def test_revised_trauma_score_normal_components_is_weighted_maximum(self):
        result = revised_trauma_score(
            metadata("修正创伤评分", "Revised Trauma Score"),
            {"gcs": 15, "systolic_bp": 120, "respiratory_rate": 20},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 7.8408)
        self.assertEqual(result.unit, "points")

    def test_rass_minus_three_is_moderate_sedation(self):
        result = rass_sedation_agitation_score(
            metadata("RASS镇静躁动评分", "Richmond Agitation-Sedation Scale"),
            {"score": -3},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, -3)
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate sedation", result.interpretation)

    def test_asa_class_three_emergency_keeps_class_and_mentions_modifier(self):
        result = asa_physical_status_classification(
            metadata("ASA体格状态分级", "ASA Physical Status Classification"),
            {"class": 3, "emergency": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "class")
        self.assertIn("emergency", result.interpretation.lower())

    def test_akin_stage_three_by_renal_replacement_therapy(self):
        result = akin_acute_kidney_injury_stage(
            metadata("AKIN急性肾损伤分期", "AKIN Acute Kidney Injury Stage"),
            {
                "baseline_creatinine_mg_dl": 1.0,
                "current_creatinine_mg_dl": 1.4,
                "urine_output_ml_kg_hr": 0.6,
                "urine_output_duration_hours": 0,
                "anuria_duration_hours": 0,
                "renal_replacement_therapy": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["stage"], 3)
        self.assertIn("stage 3", result.interpretation)

    def test_rifle_classifies_failure_by_low_urine_output_duration(self):
        result = rifle_acute_kidney_injury_classification(
            metadata("RIFLE急性肾损伤标准", "RIFLE Acute Kidney Injury Criteria"),
            {
                "baseline_creatinine_mg_dl": 1.0,
                "current_creatinine_mg_dl": 1.5,
                "urine_output_ml_kg_hr": 0.2,
                "urine_output_duration_hours": 24,
                "anuria_duration_hours": 0,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["class"], "failure")
        self.assertIn("failure", result.interpretation)

    def test_apache_ii_adds_age_and_chronic_health_to_acute_physiology(self):
        result = apache_ii_score(
            metadata("APACHE II评分", "APACHE II Score"),
            {"acute_physiology_score": 20, "age_years": 70, "chronic_health_points": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 30)
        self.assertEqual(result.value["age_points"], 5)
        self.assertEqual(result.unit, "points")

    def test_saps_ii_sums_precoded_components_and_reports_mortality_probability(self):
        result = saps_ii_score(
            metadata("SAPS II评分", "Simplified Acute Physiology Score II"),
            {"component_points": [4] * 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 40)
        self.assertAlmostEqual(result.value["mortality_probability_percent"], 24.7, places=1)
        self.assertEqual(result.unit, "points")

    def test_nutric_score_without_il6_uses_modified_threshold(self):
        result = nutric_score(
            metadata("NUTRIC评分", "NUTRIC Score"),
            {
                "age_years": 76,
                "apache_ii_score": 29,
                "sofa_score": 10,
                "comorbidities": 2,
                "days_from_hospital_to_icu": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 9)
        self.assertEqual(result.value["max_score"], 9)
        self.assertTrue(result.value["high_nutrition_risk"])
        self.assertIn("modified", result.interpretation.lower())

    def test_icdsc_counts_eight_precoded_delirium_features(self):
        result = icdsc_delirium_screening_checklist(
            metadata("ICDSC谵妄筛查量表", "Intensive Care Delirium Screening Checklist"),
            {"item_scores": [1, 0, 1, 0, 1, 0, 1, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("positive", result.interpretation.lower())

    def test_extrip_lithium_recommends_ectr_for_impaired_kidney_function_and_lithium_above_four(self):
        result = extrip_lithium_ectr_indication(
            metadata("锂中毒EXTRIP透析建议", "EXTRIP Lithium Poisoning ECTR Indication"),
            {
                "lithium_mmol_l": 4.1,
                "impaired_kidney_function": True,
                "decreased_level_of_consciousness": False,
                "seizure": False,
                "life_threatening_dysrhythmia": False,
                "significant_confusion": False,
                "expected_time_to_lithium_below_1_mmol_l_hours": 24,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["recommendation"], "recommended")
        self.assertIn("impaired_kidney_function_and_lithium_gt_4", result.value["criteria_met"])
        self.assertIn("recommended", result.interpretation)

    def test_extrip_lithium_suggests_ectr_for_expected_clearance_time_above_thirty_six_hours(self):
        result = extrip_lithium_ectr_indication(
            metadata("锂中毒EXTRIP透析建议", "EXTRIP Lithium Poisoning ECTR Indication"),
            {
                "lithium_mmol_l": 2.0,
                "impaired_kidney_function": False,
                "decreased_level_of_consciousness": False,
                "seizure": False,
                "life_threatening_dysrhythmia": False,
                "significant_confusion": False,
                "expected_time_to_lithium_below_1_mmol_l_hours": 36.1,
            },
        )

        self.assertEqual(result.value["recommendation"], "suggested")
        self.assertIn("expected_clearance_time_gt_36_hours", result.value["criteria_met"])

    def test_dn4_neuropathic_pain_screen_positive_at_four_of_ten(self):
        result = dn4_neuropathic_pain_screen(
            metadata("DN4神经病理性疼痛问卷", "Douleur Neuropathique 4 Questions"),
            {"item_scores": [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("positive", result.interpretation.lower())

    def test_dn4_neuropathic_pain_screen_rejects_non_binary_item(self):
        with self.assertRaises(ValueError):
            dn4_neuropathic_pain_screen(
                metadata("DN4神经病理性疼痛问卷", "Douleur Neuropathique 4 Questions"),
                {"item_scores": [1, 0, 0, 0, 0, 0, 0, 0, 0, 2]},
            )


if __name__ == "__main__":
    unittest.main()
