import unittest

from clinical_calculators.calculators.common.pediatric_infectious_more import (
    bacterial_meningitis_score_children,
    bedside_pediatric_early_warning_system,
    cdc_severe_malaria_criteria,
    covid_4c_mortality_score,
    duke_infective_endocarditis_criteria,
    harada_kawasaki_coronary_aneurysm_score,
    kobayashi_kawasaki_ivig_resistance_score,
    mascc_febrile_neutropenia_risk_index,
    pediatric_appendicitis_score,
    pediatric_early_warning_score,
    pediatric_respiratory_assessment_measure,
    philadelphia_criteria_febrile_infant,
    rochester_criteria_febrile_infant,
    westley_croup_score,
    who_dengue_warning_signs,
    who_rabies_exposure_category,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str = "Pediatric infectious calculator") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="pediatric_infectious",
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


class CommonPediatricInfectiousMoreTest(unittest.TestCase):
    def test_westley_all_minimum_components_scores_zero_mild(self):
        calculation = westley_croup_score(
            metadata("Westley哮吼评分"),
            {
                "level_of_consciousness": 0,
                "cyanosis": 0,
                "stridor": 0,
                "air_entry": 0,
                "retractions": 0,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("mild", calculation.interpretation)

    def test_westley_maximum_components_scores_seventeen_impending_failure(self):
        calculation = westley_croup_score(
            metadata("Westley哮吼评分"),
            {
                "level_of_consciousness": 5,
                "cyanosis": 5,
                "stridor": 2,
                "air_entry": 2,
                "retractions": 3,
            },
        )

        self.assertEqual(calculation.value, 17)
        self.assertIn("impending respiratory failure", calculation.interpretation)

    def test_westley_rejects_component_points_not_in_allowed_set(self):
        with self.assertRaises(ValueError):
            westley_croup_score(
                metadata("Westley哮吼评分"),
                {
                    "level_of_consciousness": 1,
                    "cyanosis": 0,
                    "stridor": 0,
                    "air_entry": 0,
                    "retractions": 0,
                },
            )

    def test_pram_scores_pediatric_asthma_severity_components(self):
        result = pediatric_respiratory_assessment_measure(
            metadata("PRAM儿童哮喘严重度", "Pediatric Respiratory Assessment Measure"),
            {
                "suprasternal_retractions": 2,
                "scalene_muscle_contraction": 2,
                "air_entry": 2,
                "wheezing": 2,
                "oxygen_saturation": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 9)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_pram_rejects_invalid_component_value(self):
        with self.assertRaises(ValueError):
            pediatric_respiratory_assessment_measure(
                metadata("PRAM儿童哮喘严重度", "Pediatric Respiratory Assessment Measure"),
                {
                    "suprasternal_retractions": 1,
                    "scalene_muscle_contraction": 0,
                    "air_entry": 0,
                    "wheezing": 0,
                    "oxygen_saturation": 0,
                },
            )

    def test_pediatric_appendicitis_all_positive_scores_ten_high(self):
        calculation = pediatric_appendicitis_score(
            metadata("儿童阑尾炎评分"),
            {
                "cough_percussion_hopping_tenderness": True,
                "anorexia": True,
                "fever": True,
                "nausea_vomiting": True,
                "rlq_tenderness": True,
                "leukocytosis": True,
                "neutrophilia": True,
                "migration_pain": True,
            },
        )

        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high", calculation.interpretation)

    def test_pediatric_appendicitis_four_to_six_is_equivocal(self):
        calculation = pediatric_appendicitis_score(
            metadata("儿童阑尾炎评分"),
            {
                "cough_percussion_hopping_tenderness": True,
                "anorexia": False,
                "fever": True,
                "nausea_vomiting": False,
                "rlq_tenderness": True,
                "leukocytosis": False,
                "neutrophilia": False,
                "migration_pain": False,
            },
        )

        self.assertEqual(calculation.value, 5)
        self.assertIn("equivocal", calculation.interpretation)

    def test_pediatric_appendicitis_rejects_non_boolean_input(self):
        with self.assertRaises(ValueError):
            pediatric_appendicitis_score(
                metadata("儿童阑尾炎评分"),
                {
                    "cough_percussion_hopping_tenderness": "yes",
                    "anorexia": False,
                    "fever": False,
                    "nausea_vomiting": False,
                    "rlq_tenderness": False,
                    "leukocytosis": False,
                    "neutrophilia": False,
                    "migration_pain": False,
                },
            )

    def test_duke_two_major_criteria_classifies_definite(self):
        calculation = duke_infective_endocarditis_criteria(
            metadata("Duke感染性心内膜炎标准"),
            {"major_criteria_count": 2, "minor_criteria_count": 0},
        )

        self.assertEqual(
            calculation.value,
            {"major": 2, "minor": 0, "classification": "definite"},
        )
        self.assertEqual(calculation.unit, "")
        self.assertIn("definite", calculation.interpretation)

    def test_duke_one_major_one_minor_classifies_possible(self):
        calculation = duke_infective_endocarditis_criteria(
            metadata("Duke感染性心内膜炎标准"),
            {"major_criteria_count": 1, "minor_criteria_count": 1},
        )

        self.assertEqual(calculation.value["classification"], "possible")

    def test_duke_no_criteria_classifies_rejected(self):
        calculation = duke_infective_endocarditis_criteria(
            metadata("Duke感染性心内膜炎标准"),
            {"major_criteria_count": 0, "minor_criteria_count": 0},
        )

        self.assertEqual(calculation.value["classification"], "rejected")

    def test_duke_rejects_major_count_outside_zero_to_two(self):
        with self.assertRaises(ValueError):
            duke_infective_endocarditis_criteria(
                metadata("Duke感染性心内膜炎标准"),
                {"major_criteria_count": 3, "minor_criteria_count": 0},
            )

    def test_mascc_low_risk_threshold_at_twenty_one(self):
        calculation = mascc_febrile_neutropenia_risk_index(
            metadata("MASCC发热性中性粒细胞减少风险"),
            {
                "burden_of_illness": "moderate",
                "no_hypotension": True,
                "no_copd": True,
                "solid_tumor_or_no_fungal_infection": True,
                "no_dehydration": True,
                "outpatient_status": False,
                "age_less_than_60": True,
            },
        )

        self.assertEqual(calculation.value, 21)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("low risk", calculation.interpretation)

    def test_mascc_severe_burden_and_no_points_is_high_risk(self):
        calculation = mascc_febrile_neutropenia_risk_index(
            metadata("MASCC发热性中性粒细胞减少风险"),
            {
                "burden_of_illness": "severe",
                "no_hypotension": False,
                "no_copd": False,
                "solid_tumor_or_no_fungal_infection": False,
                "no_dehydration": False,
                "outpatient_status": False,
                "age_less_than_60": False,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("high risk", calculation.interpretation)

    def test_mascc_rejects_unknown_burden_category(self):
        with self.assertRaises(ValueError):
            mascc_febrile_neutropenia_risk_index(
                metadata("MASCC发热性中性粒细胞减少风险"),
                {
                    "burden_of_illness": "mild",
                    "no_hypotension": True,
                    "no_copd": True,
                    "solid_tumor_or_no_fungal_infection": True,
                    "no_dehydration": True,
                    "outpatient_status": True,
                    "age_less_than_60": True,
                },
            )

    def test_covid_4c_maximum_profile_scores_twenty_one_very_high(self):
        calculation = covid_4c_mortality_score(
            metadata("4C COVID-19死亡率评分"),
            {
                "age_years": 80,
                "sex": "male",
                "comorbidity_count": 2,
                "respiratory_rate": 30,
                "oxygen_saturation_percent": 91,
                "gcs": 14,
                "urea_mmol_l": 15,
                "crp_mg_l": 100,
            },
        )

        self.assertEqual(calculation.value, 21)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("very high", calculation.interpretation)

    def test_covid_4c_boundary_profile_scores_six_intermediate(self):
        calculation = covid_4c_mortality_score(
            metadata("4C COVID-19死亡率评分"),
            {
                "age_years": 59,
                "sex": "female",
                "comorbidity_count": 1,
                "respiratory_rate": 29,
                "oxygen_saturation_percent": 92,
                "gcs": 15,
                "urea_mmol_l": 14,
                "crp_mg_l": 99,
            },
        )

        self.assertEqual(calculation.value, 6)
        self.assertIn("intermediate", calculation.interpretation)

    def test_covid_4c_rejects_negative_comorbidity_count(self):
        with self.assertRaises(ValueError):
            covid_4c_mortality_score(
                metadata("4C COVID-19死亡率评分"),
                {
                    "age_years": 50,
                    "sex": "female",
                    "comorbidity_count": -1,
                    "respiratory_rate": 20,
                    "oxygen_saturation_percent": 95,
                    "gcs": 15,
                    "urea_mmol_l": 7,
                    "crp_mg_l": 50,
                },
            )

    def test_pews_high_score_recommends_escalation(self):
        calculation = pediatric_early_warning_score(
            metadata("PEWS儿童早期预警评分", "Pediatric Early Warning Score"),
            {
                "behavior": 3,
                "cardiovascular": 2,
                "respiratory": 2,
                "quarter_hourly_nebulizers": True,
                "persistent_postoperative_vomiting": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 8)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("escalation", calculation.interpretation)

    def test_pews_zero_to_two_is_lower_risk(self):
        calculation = pediatric_early_warning_score(
            metadata("PEWS儿童早期预警评分", "Pediatric Early Warning Score"),
            {
                "behavior": 0,
                "cardiovascular": 1,
                "respiratory": 0,
                "quarter_hourly_nebulizers": False,
                "persistent_postoperative_vomiting": False,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("lower risk", calculation.interpretation)

    def test_pews_rejects_component_outside_zero_to_three(self):
        with self.assertRaises(ValueError):
            pediatric_early_warning_score(
                metadata("PEWS儿童早期预警评分", "Pediatric Early Warning Score"),
                {
                    "behavior": 4,
                    "cardiovascular": 0,
                    "respiratory": 0,
                    "quarter_hourly_nebulizers": False,
                    "persistent_postoperative_vomiting": False,
                },
            )

    def test_bedside_pews_maximum_source_table_profile_scores_26(self):
        calculation = bedside_pediatric_early_warning_system(
            metadata(
                "儿童早期预警评分扩展版",
                "Bedside Pediatric Early Warning System",
            ),
            {
                "age_months": 2,
                "heart_rate_bpm": 190,
                "systolic_bp_mm_hg": 130,
                "capillary_refill_seconds": 3,
                "respiratory_rate_breaths_min": 91,
                "respiratory_effort": "severe_or_apnea",
                "oxygen_saturation_percent": 80,
                "oxygen_therapy": "high",
            },
        )

        self.assertEqual(calculation.value, 26)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("at or above 8", calculation.interpretation)

    def test_bedside_pews_preserves_published_strict_boundary(self):
        calculation = bedside_pediatric_early_warning_system(
            metadata(
                "儿童早期预警评分扩展版",
                "Bedside Pediatric Early Warning System",
            ),
            {
                "age_months": 48,
                "heart_rate_bpm": 150,
                "systolic_bp_mm_hg": 120,
                "capillary_refill_seconds": 2.9,
                "respiratory_rate_breaths_min": 31,
                "respiratory_effort": "mild",
                "oxygen_saturation_percent": 94,
                "oxygen_therapy": "low",
            },
        )

        # In the published 4–12 year row, HR >150 scores 4; exactly 150 scores 2.
        self.assertEqual(calculation.value, 8)

    def test_bedside_pews_age_band_boundary_and_normal_profile(self):
        common = {
            "heart_rate_bpm": 101,
            "systolic_bp_mm_hg": 90,
            "capillary_refill_seconds": 2,
            "respiratory_rate_breaths_min": 30,
            "respiratory_effort": "normal",
            "oxygen_saturation_percent": 95,
            "oxygen_therapy": "room_air",
        }

        under_three_months = bedside_pediatric_early_warning_system(
            metadata("儿童早期预警评分扩展版"),
            {**common, "age_months": 2.99},
        )
        three_months = bedside_pediatric_early_warning_system(
            metadata("儿童早期预警评分扩展版"),
            {**common, "age_months": 3},
        )

        self.assertEqual(under_three_months.value, 2)
        self.assertEqual(three_months.value, 0)

    def test_bedside_pews_rejects_invalid_coded_category(self):
        with self.assertRaises(ValueError):
            bedside_pediatric_early_warning_system(
                metadata("儿童早期预警评分扩展版"),
                {
                    "age_months": 24,
                    "heart_rate_bpm": 100,
                    "systolic_bp_mm_hg": 100,
                    "capillary_refill_seconds": 2,
                    "respiratory_rate_breaths_min": 25,
                    "respiratory_effort": "unknown",
                    "oxygen_saturation_percent": 95,
                    "oxygen_therapy": "room_air",
                },
            )

    def test_rochester_criteria_all_low_risk_features_is_low_risk(self):
        result = rochester_criteria_febrile_infant(
            metadata("罗切斯特婴儿发热低危标准", "Rochester Criteria"),
            {
                "age_days": 45,
                "well_appearing": True,
                "previously_healthy": True,
                "wbc_10e9_l": 10,
                "absolute_band_count_10e9_l": 1.0,
                "urine_wbc_per_hpf": 5,
                "diarrhea": True,
                "stool_wbc_per_hpf": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["low_risk"], True)
        self.assertEqual(result.value["criteria_failed"], 0)
        self.assertEqual(result.unit, "criteria")
        self.assertIn("low risk", result.interpretation)

    def test_rochester_criteria_flags_failed_laboratory_cutoffs(self):
        result = rochester_criteria_febrile_infant(
            metadata("罗切斯特婴儿发热低危标准", "Rochester Criteria"),
            {
                "age_days": 45,
                "well_appearing": True,
                "previously_healthy": True,
                "wbc_10e9_l": 16,
                "absolute_band_count_10e9_l": 1.6,
                "urine_wbc_per_hpf": 11,
                "diarrhea": False,
                "stool_wbc_per_hpf": 99,
            },
        )

        self.assertFalse(result.value["low_risk"])
        self.assertEqual(result.value["criteria_failed"], 3)
        self.assertIn("not low risk", result.interpretation)

    def test_philadelphia_criteria_all_low_risk_features_is_low_risk(self):
        result = philadelphia_criteria_febrile_infant(
            metadata("费城婴儿发热标准", "Philadelphia Criteria"),
            {
                "age_days": 40,
                "well_appearing": True,
                "wbc_10e9_l": 10,
                "band_to_neutrophil_ratio": 0.1,
                "urine_wbc_per_hpf": 5,
                "csf_wbc_per_uL": 7,
                "csf_gram_stain_positive": False,
                "chest_radiograph_infiltrate": False,
                "diarrhea": True,
                "stool_wbc_per_hpf": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertTrue(result.value["low_risk"])
        self.assertEqual(result.value["criteria_failed"], 0)
        self.assertIn("low risk", result.interpretation)

    def test_philadelphia_criteria_positive_csf_gram_stain_is_not_low_risk(self):
        result = philadelphia_criteria_febrile_infant(
            metadata("费城婴儿发热标准", "Philadelphia Criteria"),
            {
                "age_days": 40,
                "well_appearing": True,
                "wbc_10e9_l": 10,
                "band_to_neutrophil_ratio": 0.1,
                "urine_wbc_per_hpf": 5,
                "csf_wbc_per_uL": 7,
                "csf_gram_stain_positive": True,
                "chest_radiograph_infiltrate": False,
                "diarrhea": False,
                "stool_wbc_per_hpf": 99,
            },
        )

        self.assertFalse(result.value["low_risk"])
        self.assertEqual(result.value["criteria_failed"], 1)
        self.assertIn("not low risk", result.interpretation)

    def test_philadelphia_criteria_urine_wbc_ten_fails_low_risk_cutoff(self):
        result = philadelphia_criteria_febrile_infant(
            metadata("费城婴儿发热标准", "Philadelphia Criteria"),
            {
                "age_days": 40,
                "well_appearing": True,
                "wbc_10e9_l": 10,
                "band_to_neutrophil_ratio": 0.1,
                "urine_wbc_per_hpf": 10,
                "csf_wbc_per_uL": 7,
                "csf_gram_stain_positive": False,
                "chest_radiograph_infiltrate": False,
                "diarrhea": False,
                "stool_wbc_per_hpf": 0,
            },
        )

        self.assertFalse(result.value["low_risk"])
        self.assertEqual(result.value["criteria_failed"], 1)

    def test_bacterial_meningitis_score_counts_all_predictors_with_gram_stain_weighted_two(self):
        result = bacterial_meningitis_score_children(
            metadata("脑膜炎细菌性预测评分", "Bacterial Meningitis Score"),
            {
                "positive_csf_gram_stain": True,
                "csf_anc_cells_per_uL": 1000,
                "csf_protein_mg_dl": 80,
                "peripheral_anc_cells_per_uL": 10000,
                "seizure_at_or_before_presentation": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "criteria")
        self.assertIn("not very low risk", result.interpretation)

    def test_bacterial_meningitis_score_zero_predictors_is_very_low_risk(self):
        result = bacterial_meningitis_score_children(
            metadata("脑膜炎细菌性预测评分", "Bacterial Meningitis Score"),
            {
                "positive_csf_gram_stain": False,
                "csf_anc_cells_per_uL": 999,
                "csf_protein_mg_dl": 79,
                "peripheral_anc_cells_per_uL": 9999,
                "seizure_at_or_before_presentation": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("very low risk", result.interpretation)

    def test_kobayashi_kawasaki_score_counts_weighted_ivig_resistance_predictors(self):
        result = kobayashi_kawasaki_ivig_resistance_score(
            metadata("Kobayashi IVIG无反应评分", "Kobayashi Score"),
            {
                "sodium_mmol_l": 133,
                "ast_iu_l": 100,
                "days_of_illness_at_initial_treatment": 4,
                "neutrophils_percent": 80,
                "crp_mg_dl": 10,
                "age_months": 12,
                "platelets_10e3_per_uL": 300,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 11)
        self.assertEqual(result.unit, "points")
        self.assertTrue(result.value["high_risk"])
        self.assertIn("high risk", result.interpretation)

    def test_kobayashi_kawasaki_score_cutoff_four_is_high_risk(self):
        result = kobayashi_kawasaki_ivig_resistance_score(
            metadata("Kobayashi IVIG无反应评分", "Kobayashi Score"),
            {
                "sodium_mmol_l": 133,
                "ast_iu_l": 99,
                "days_of_illness_at_initial_treatment": 4,
                "neutrophils_percent": 79,
                "crp_mg_dl": 9,
                "age_months": 13,
                "platelets_10e3_per_uL": 301,
            },
        )

        self.assertEqual(result.value["score"], 4)
        self.assertTrue(result.value["high_risk"])

    def test_harada_kawasaki_score_counts_coronary_aneurysm_risk_factors(self):
        result = harada_kawasaki_coronary_aneurysm_score(
            metadata("Harada冠脉病变风险评分", "Harada Score"),
            {
                "wbc_per_uL": 12001,
                "platelets_10e3_per_uL": 349,
                "crp_mg_dl": 3.1,
                "hematocrit_percent": 34.9,
                "albumin_g_dl": 3.4,
                "age_months": 12,
                "sex": "male",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 7)
        self.assertEqual(result.unit, "points")
        self.assertTrue(result.value["high_risk"])
        self.assertIn("high risk", result.interpretation)

    def test_who_dengue_warning_signs_absent_classifies_no_warning_signs(self):
        result = who_dengue_warning_signs(
            metadata("WHO登革热警示征象", "WHO Dengue Warning Signs"),
            {
                "abdominal_pain_or_tenderness": False,
                "persistent_vomiting": False,
                "clinical_fluid_accumulation": False,
                "mucosal_bleeding": False,
                "lethargy_or_restlessness": False,
                "liver_enlargement_gt_2cm": False,
                "hematocrit_increase_with_rapid_platelet_decrease": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertFalse(result.value["warning_signs_present"])
        self.assertEqual(result.value["warning_sign_count"], 0)
        self.assertIn("without warning signs", result.interpretation)

    def test_who_dengue_warning_signs_counts_any_present_warning_sign(self):
        result = who_dengue_warning_signs(
            metadata("WHO登革热警示征象", "WHO Dengue Warning Signs"),
            {
                "abdominal_pain_or_tenderness": True,
                "persistent_vomiting": False,
                "clinical_fluid_accumulation": False,
                "mucosal_bleeding": True,
                "lethargy_or_restlessness": False,
                "liver_enlargement_gt_2cm": False,
                "hematocrit_increase_with_rapid_platelet_decrease": False,
            },
        )

        self.assertTrue(result.value["warning_signs_present"])
        self.assertEqual(result.value["warning_sign_count"], 2)
        self.assertIn("with warning signs", result.interpretation)

    def test_who_rabies_exposure_category_uses_highest_applicable_category(self):
        result = who_rabies_exposure_category(
            metadata("WHO狂犬病暴露分类", "WHO Rabies Exposure Category"),
            {
                "touching_or_feeding_animals": True,
                "licks_on_intact_skin": False,
                "nibbling_uncovered_skin": True,
                "minor_scratch_or_abrasion_without_bleeding": False,
                "transdermal_bite_or_scratch": False,
                "mucous_membrane_saliva_contact": False,
                "lick_on_broken_skin": False,
                "bat_exposure": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["category"], 3)
        self.assertIn("immunoglobulin", result.interpretation.lower())

    def test_who_rabies_exposure_category_two_recommends_vaccination(self):
        result = who_rabies_exposure_category(
            metadata("WHO狂犬病暴露分类", "WHO Rabies Exposure Category"),
            {
                "touching_or_feeding_animals": False,
                "licks_on_intact_skin": False,
                "nibbling_uncovered_skin": False,
                "minor_scratch_or_abrasion_without_bleeding": True,
                "transdermal_bite_or_scratch": False,
                "mucous_membrane_saliva_contact": False,
                "lick_on_broken_skin": False,
                "bat_exposure": False,
            },
        )

        self.assertEqual(result.value["category"], 2)
        self.assertIn("vaccination", result.interpretation.lower())

    def test_cdc_severe_malaria_criteria_flags_parasitemia_at_five_percent(self):
        result = cdc_severe_malaria_criteria(
            metadata("CDC重症疟疾标准", "CDC Severe Malaria Criteria"),
            {
                "parasitemia_percent": 5,
                "hemoglobin_g_dl": 8,
                "impaired_consciousness": False,
                "seizures": False,
                "shock": False,
                "pulmonary_edema_or_ards": False,
                "acidosis": False,
                "acute_kidney_injury": False,
                "abnormal_bleeding_or_dic": False,
                "jaundice": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertTrue(result.value["severe_malaria"])
        self.assertIn("high_parasitemia", result.value["criteria_met"])

    def test_cdc_severe_malaria_criteria_requires_jaundice_with_another_sign(self):
        result = cdc_severe_malaria_criteria(
            metadata("CDC重症疟疾标准", "CDC Severe Malaria Criteria"),
            {
                "parasitemia_percent": 4.9,
                "hemoglobin_g_dl": 7,
                "impaired_consciousness": False,
                "seizures": False,
                "shock": False,
                "pulmonary_edema_or_ards": False,
                "acidosis": False,
                "acute_kidney_injury": False,
                "abnormal_bleeding_or_dic": False,
                "jaundice": True,
            },
        )

        self.assertFalse(result.value["severe_malaria"])
        self.assertEqual(result.value["criteria_met"], [])
        self.assertIn("not met", result.interpretation)


if __name__ == "__main__":
    unittest.main()
