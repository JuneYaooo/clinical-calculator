import unittest

from clinical_calculators.calculators.common.nursing_obstetric_scores import (
    amniotic_fluid_index,
    apgar_score,
    bishop_cervix_score,
    braden_pressure_ulcer_risk_score,
    downes_respiratory_distress_score,
    estimated_fetal_weight_hadlock,
    gardner_blastocyst_grading,
    preeclampsia_severe_features_checklist,
    gestational_diabetes_screening_interpretation,
    iota_simple_rules,
    modified_ferriman_gallwey_score,
    modified_obstetric_early_warning_score,
    morse_fall_risk_score,
    ovarian_reserve_assessment_afc_amh,
    pop_q_stage,
    poseidon_criteria,
    roma_ovarian_malignancy_algorithm,
    rotterdam_pcos_criteria,
    single_deepest_pocket,
    snappe_ii_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="nursing_obstetric_neonatal",
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


class CommonNursingObstetricScoresTest(unittest.TestCase):
    def test_apgar_all_twos_is_reassuring(self):
        result = apgar_score(
            metadata("Apgar Score", "Apgar Score"),
            {"components": [2, 2, 2, 2, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("reassuring", result.interpretation)

    def test_bishop_high_component_points_is_favorable(self):
        result = bishop_cervix_score(
            metadata("Bishop宫颈评分", "Bishop Score"),
            {
                "dilation": 3,
                "effacement": 3,
                "station": 2,
                "consistency": 2,
                "position": 2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("favorable", result.interpretation)

    def test_braden_minimum_score_is_very_high_risk(self):
        result = braden_pressure_ulcer_risk_score(
            metadata("Braden压疮风险评分", "Braden Scale for Predicting Pressure Sore Risk"),
            {
                "sensory_perception": 1,
                "moisture": 1,
                "activity": 1,
                "mobility": 1,
                "nutrition": 1,
                "friction_shear": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("very high", result.interpretation)

    def test_braden_maximum_score_is_low_risk(self):
        result = braden_pressure_ulcer_risk_score(
            metadata("Braden压疮风险评分", "Braden Scale for Predicting Pressure Sore Risk"),
            {
                "sensory_perception": 4,
                "moisture": 4,
                "activity": 4,
                "mobility": 4,
                "nutrition": 4,
                "friction_shear": 3,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 23)
        self.assertEqual(result.unit, "points")
        self.assertIn("low risk", result.interpretation)

    def test_morse_maximum_score_is_high_risk(self):
        result = morse_fall_risk_score(
            metadata("Morse跌倒风险评分", "Morse Fall Scale"),
            {
                "history_of_falling": 25,
                "secondary_diagnosis": 15,
                "ambulatory_aid": 30,
                "iv_or_heparin_lock": 20,
                "gait": 20,
                "mental_status": 15,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 125)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_morse_all_zero_is_low_risk(self):
        result = morse_fall_risk_score(
            metadata("Morse跌倒风险评分", "Morse Fall Scale"),
            {
                "history_of_falling": 0,
                "secondary_diagnosis": 0,
                "ambulatory_aid": 0,
                "iv_or_heparin_lock": 0,
                "gait": 0,
                "mental_status": 0,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("low", result.interpretation)

    def test_gdm_one_step_any_abnormal_value_diagnoses_gdm(self):
        result = gestational_diabetes_screening_interpretation(
            metadata("妊娠期糖尿病筛查解释", "Gestational Diabetes Screening Interpretation"),
            {
                "strategy": "one_step_75g_iadpsg",
                "fasting_mg_dl": 91,
                "one_hour_mg_dl": 180,
                "two_hour_mg_dl": 140,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["abnormal_count"], 1)
        self.assertTrue(result.value["diagnostic_for_gdm"])
        self.assertIn("diagnostic", result.interpretation)

    def test_gdm_two_step_screen_positive_with_two_abnormal_ogtt_values(self):
        result = gestational_diabetes_screening_interpretation(
            metadata("妊娠期糖尿病筛查解释", "Gestational Diabetes Screening Interpretation"),
            {
                "strategy": "two_step_carpenter_coustan",
                "screen_one_hour_mg_dl": 140,
                "fasting_mg_dl": 95,
                "one_hour_mg_dl": 170,
                "two_hour_mg_dl": 155,
                "three_hour_mg_dl": 120,
            },
        )

        self.assertEqual(result.value["screen_positive"], True)
        self.assertEqual(result.value["abnormal_count"], 2)
        self.assertTrue(result.value["diagnostic_for_gdm"])
        self.assertIn("diagnostic", result.interpretation)

    def test_gdm_two_step_negative_screen_does_not_require_ogtt(self):
        result = gestational_diabetes_screening_interpretation(
            metadata("妊娠期糖尿病筛查解释", "Gestational Diabetes Screening Interpretation"),
            {
                "strategy": "two_step_carpenter_coustan",
                "screen_one_hour_mg_dl": 129,
            },
        )

        self.assertEqual(result.value["screen_positive"], False)
        self.assertEqual(result.value["abnormal_count"], 0)
        self.assertFalse(result.value["diagnostic_for_gdm"])
        self.assertIn("screen negative", result.interpretation)

    def test_gdm_rejects_negative_glucose(self):
        with self.assertRaises(ValueError):
            gestational_diabetes_screening_interpretation(
                metadata("妊娠期糖尿病筛查解释", "Gestational Diabetes Screening Interpretation"),
                {
                    "strategy": "one_step_75g_iadpsg",
                    "fasting_mg_dl": -1,
                    "one_hour_mg_dl": 100,
                    "two_hour_mg_dl": 100,
                },
            )

    def test_hadlock_four_parameter_estimates_fetal_weight_in_grams(self):
        result = estimated_fetal_weight_hadlock(
            metadata("估计胎儿体重Hadlock公式", "Hadlock Estimated Fetal Weight"),
            {
                "bpd_cm": 9.0,
                "hc_cm": 32.0,
                "ac_cm": 30.0,
                "fl_cm": 6.5,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.unit, "g")
        self.assertAlmostEqual(result.value["estimated_fetal_weight_g"], 2395.5, places=1)
        self.assertAlmostEqual(result.value["log10_efw"], 3.3794, places=4)
        self.assertEqual(result.value["formula"], "hadlock_bpd_hc_ac_fl")
        self.assertIn("Hadlock", result.interpretation)

    def test_amniotic_fluid_index_sums_quadrants_and_flags_oligohydramnios(self):
        result = amniotic_fluid_index(
            metadata("羊水指数", "Amniotic Fluid Index"),
            {
                "quadrant_1_cm": 2.0,
                "quadrant_2_cm": 1.0,
                "quadrant_3_cm": 1.0,
                "quadrant_4_cm": 0.8,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 4.8, places=1)
        self.assertEqual(result.unit, "cm")
        self.assertIn("oligohydramnios", result.interpretation)

    def test_amniotic_fluid_index_flags_five_cm_as_oligohydramnios(self):
        result = amniotic_fluid_index(
            metadata("羊水指数", "Amniotic Fluid Index"),
            {
                "quadrant_1_cm": 2.0,
                "quadrant_2_cm": 1.0,
                "quadrant_3_cm": 1.0,
                "quadrant_4_cm": 1.0,
            },
        )

        self.assertEqual(result.value, 5.0)
        self.assertIn("oligohydramnios", result.interpretation)

    def test_single_deepest_pocket_flags_polyhydramnios_at_eight_cm(self):
        result = single_deepest_pocket(
            metadata("单最大羊水池深度", "Single Deepest Pocket"),
            {"single_deepest_pocket_cm": 8.0},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8.0)
        self.assertEqual(result.unit, "cm")
        self.assertIn("polyhydramnios", result.interpretation)

    def test_preeclampsia_severe_features_detects_acog_severe_feature(self):
        result = preeclampsia_severe_features_checklist(
            metadata("子痫前期严重特征判断", "Preeclampsia Severe Features Checklist"),
            {
                "severe_range_blood_pressure_confirmed": False,
                "platelets_per_microliter": 99000,
                "serum_creatinine_mg_dl": 0.9,
                "creatinine_doubled_from_baseline": False,
                "liver_transaminases_twice_normal": False,
                "severe_persistent_ruq_epigastric_pain": False,
                "pulmonary_edema": False,
                "new_onset_headache_unresponsive": False,
                "visual_symptoms": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertTrue(result.value["has_severe_features"])
        self.assertEqual(result.value["severe_feature_count"], 1)
        self.assertEqual(result.value["severe_features"], ["thrombocytopenia"])
        self.assertIn("severe features", result.interpretation)

    def test_preeclampsia_severe_features_reports_absent_when_no_criteria_met(self):
        result = preeclampsia_severe_features_checklist(
            metadata("子痫前期严重特征判断", "Preeclampsia Severe Features Checklist"),
            {
                "severe_range_blood_pressure_confirmed": False,
                "platelets_per_microliter": 150000,
                "serum_creatinine_mg_dl": 1.0,
                "creatinine_doubled_from_baseline": False,
                "liver_transaminases_twice_normal": False,
                "severe_persistent_ruq_epigastric_pain": False,
                "pulmonary_edema": False,
                "new_onset_headache_unresponsive": False,
                "visual_symptoms": False,
            },
        )

        self.assertFalse(result.value["has_severe_features"])
        self.assertEqual(result.value["severe_feature_count"], 0)
        self.assertEqual(result.value["severe_features"], [])
        self.assertIn("not identified", result.interpretation)

    def test_preeclampsia_severe_features_accepts_confirmed_severe_range_bp(self):
        result = preeclampsia_severe_features_checklist(
            metadata("子痫前期严重特征判断", "Preeclampsia Severe Features Checklist"),
            {
                "severe_range_blood_pressure_confirmed": True,
                "platelets_per_microliter": 150000,
                "serum_creatinine_mg_dl": 1.0,
                "creatinine_doubled_from_baseline": False,
                "liver_transaminases_twice_normal": False,
                "severe_persistent_ruq_epigastric_pain": False,
                "pulmonary_edema": False,
                "new_onset_headache_unresponsive": False,
                "visual_symptoms": False,
            },
        )

        self.assertTrue(result.value["has_severe_features"])
        self.assertEqual(result.value["severe_features"], ["severe_range_blood_pressure"])

    def test_downes_all_severe_component_points_scores_ten(self):
        result = downes_respiratory_distress_score(
            metadata("Downes儿童呼吸窘迫评分", "Downes Score"),
            {
                "respiratory_rate": 2,
                "cyanosis": 2,
                "air_entry": 2,
                "grunting": 2,
                "retractions": 2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_snappe_ii_sums_all_high_risk_point_categories(self):
        result = snappe_ii_score(
            metadata("新生儿急性生理评分围产扩展版", "SNAPPE-II"),
            {
                "mean_blood_pressure_mm_hg": 19,
                "lowest_temperature_c": 34.9,
                "pao2_fio2_ratio": 0.2,
                "lowest_serum_ph": 7.09,
                "multiple_seizures": True,
                "urine_output_ml_kg_hr": 0.05,
                "five_minute_apgar": 6,
                "birth_weight_g": 700,
                "small_for_gestational_age_below_3rd_percentile": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 162)
        self.assertEqual(result.unit, "points")
        self.assertEqual(result.value["component_points"]["birth_weight"], 17)
        self.assertIn("very high", result.interpretation)

    def test_snappe_ii_counts_intermediate_temperature_pao2_fio2_ph_urine_and_birth_weight(self):
        result = snappe_ii_score(
            metadata("新生儿急性生理评分围产扩展版", "SNAPPE-II"),
            {
                "mean_blood_pressure_mm_hg": 25,
                "lowest_temperature_c": 35.2,
                "pao2_fio2_ratio": 0.5,
                "lowest_serum_ph": 7.15,
                "multiple_seizures": False,
                "urine_output_ml_kg_hr": 0.5,
                "five_minute_apgar": 7,
                "birth_weight_g": 800,
                "small_for_gestational_age_below_3rd_percentile": False,
            },
        )

        self.assertEqual(result.value["score"], 55)
        self.assertEqual(result.value["component_points"]["lowest_temperature"], 8)
        self.assertEqual(result.value["component_points"]["pao2_fio2_ratio"], 16)

    def test_roma_premenopausal_uses_ln_equation_and_cutoff(self):
        result = roma_ovarian_malignancy_algorithm(
            metadata("ROMA卵巢癌风险算法", "Risk of Ovarian Malignancy Algorithm"),
            {
                "menopausal_status": "premenopausal",
                "he4_pmol_l": 150,
                "ca125_u_ml": 100,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.unit, "%")
        self.assertAlmostEqual(result.value["predictive_index"], 0.2136, places=4)
        self.assertAlmostEqual(result.value["roma_percent"], 55.3197, places=4)
        self.assertTrue(result.value["high_risk"])

    def test_modified_ferriman_gallwey_sums_nine_regions(self):
        result = modified_ferriman_gallwey_score(
            metadata("多毛症Ferriman-Gallwey评分", "Modified Ferriman-Gallwey Score"),
            {
                "upper_lip": 2,
                "chin": 2,
                "chest": 2,
                "upper_back": 2,
                "lower_back": 2,
                "upper_abdomen": 2,
                "lower_abdomen": 2,
                "upper_arms": 2,
                "thighs": 2,
            },
        )

        self.assertEqual(result.value, 18)
        self.assertEqual(result.unit, "points")
        self.assertIn("hirsutism range", result.interpretation)

    def test_ovarian_reserve_flags_abnormal_afc_or_amh(self):
        result = ovarian_reserve_assessment_afc_amh(
            metadata("卵巢储备评估AFC-AMH", "Ovarian Reserve Assessment"),
            {"afc": 4, "amh_ng_ml": 0.4},
        )

        self.assertTrue(result.value["abnormal_ovarian_reserve_test"])
        self.assertEqual(result.value["afc_cutoff"], 7)
        self.assertEqual(result.value["amh_cutoff_ng_ml"], 1.1)
        self.assertIn("reduced ovarian reserve marker", result.interpretation)

    def test_poseidon_classifies_group_one_b_for_young_normal_reserve_suboptimal_response(self):
        result = poseidon_criteria(
            metadata("POSEIDON低预后分类", "POSEIDON Criteria"),
            {"age_years": 34, "afc": 8, "amh_ng_ml": 2.0, "previous_oocytes_retrieved": 6},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["group"], "1B")
        self.assertEqual(result.value["reserve_status"], "adequate")
        self.assertIn("POSEIDON group 1B", result.interpretation)

    def test_poseidon_uses_either_afc_or_amh_to_identify_adequate_reserve(self):
        result = poseidon_criteria(
            metadata("POSEIDON低预后分类", "POSEIDON Criteria"),
            {"age_years": 34, "afc": 6, "amh_ng_ml": 0.8, "previous_oocytes_retrieved": 3},
        )

        self.assertEqual(result.value["group"], "1A")
        self.assertEqual(result.value["reserve_status"], "adequate")

    def test_poseidon_classifies_group_four_for_older_low_reserve(self):
        result = poseidon_criteria(
            metadata("POSEIDON低预后分类", "POSEIDON Criteria"),
            {"age_years": 37, "afc": 4, "amh_ng_ml": 0.8},
        )

        self.assertEqual(result.value["group"], "4")
        self.assertEqual(result.value["reserve_status"], "low")

    def test_gardner_blastocyst_grading_formats_expansion_icm_and_te(self):
        result = gardner_blastocyst_grading(
            metadata("Gardner囊胚评分", "Gardner Blastocyst Grading"),
            {"expansion_grade": 5, "inner_cell_mass_grade": "A", "trophectoderm_grade": "B"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["grade"], "5AB")
        self.assertEqual(result.value["stage"], "hatching blastocyst")
        self.assertEqual(result.unit, "grade")

    def test_modified_obstetric_early_warning_score_high_vitals_scores_high_concern(self):
        result = modified_obstetric_early_warning_score(
            metadata("改良产科早期预警评分", "Modified Obstetric Early Warning Score"),
            {
                "respiratory_rate": 25,
                "oxygen_saturation_percent": 92,
                "temperature_c": 37.5,
                "pulse_bpm": 122,
                "systolic_bp_mm_hg": 145,
                "diastolic_bp_mm_hg": 97,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_iota_simple_rules_classifies_malignant_when_only_m_features_present(self):
        result = iota_simple_rules(
            metadata("IOTA简单规则", "IOTA Simple Rules"),
            {
                "irregular_solid_tumor": True,
                "ascites": True,
                "at_least_four_papillary_structures": False,
                "irregular_multilocular_solid_tumor_ge_100mm": False,
                "very_strong_blood_flow": False,
                "unilocular_cyst": False,
                "solid_components_under_7mm": False,
                "acoustic_shadows": False,
                "smooth_multilocular_tumor_under_100mm": False,
                "no_blood_flow": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["classification"], "malignant")
        self.assertEqual(result.value["malignant_feature_count"], 2)
        self.assertEqual(result.value["benign_feature_count"], 0)
        self.assertIn("malignant", result.interpretation)

    def test_iota_simple_rules_reports_inconclusive_when_benign_and_malignant_features_present(self):
        result = iota_simple_rules(
            metadata("IOTA简单规则", "IOTA Simple Rules"),
            {
                "irregular_solid_tumor": False,
                "ascites": False,
                "at_least_four_papillary_structures": False,
                "irregular_multilocular_solid_tumor_ge_100mm": False,
                "very_strong_blood_flow": True,
                "unilocular_cyst": True,
                "solid_components_under_7mm": False,
                "acoustic_shadows": False,
                "smooth_multilocular_tumor_under_100mm": False,
                "no_blood_flow": False,
            },
        )

        self.assertEqual(result.value["classification"], "inconclusive")
        self.assertIn("very_strong_blood_flow", result.value["malignant_features"])
        self.assertIn("unilocular_cyst", result.value["benign_features"])

    def test_rotterdam_pcos_criteria_requires_two_of_three_after_exclusions(self):
        result = rotterdam_pcos_criteria(
            metadata("Rotterdam多囊卵巢综合征判定", "Rotterdam PCOS Criteria"),
            {
                "oligo_or_anovulation": True,
                "clinical_or_biochemical_hyperandrogenism": True,
                "polycystic_ovarian_morphology": False,
                "other_causes_excluded": True,
            },
        )

        self.assertTrue(result.value["meets_rotterdam_pcos"])
        self.assertEqual(result.value["criteria_count"], 2)
        self.assertIn("meets", result.interpretation)

    def test_rotterdam_pcos_criteria_does_not_diagnose_without_exclusions(self):
        result = rotterdam_pcos_criteria(
            metadata("Rotterdam多囊卵巢综合征判定", "Rotterdam PCOS Criteria"),
            {
                "oligo_or_anovulation": True,
                "clinical_or_biochemical_hyperandrogenism": True,
                "polycystic_ovarian_morphology": True,
                "other_causes_excluded": False,
            },
        )

        self.assertFalse(result.value["meets_rotterdam_pcos"])
        self.assertIn("requires exclusion", result.interpretation)

    def test_pop_q_stage_uses_most_distal_point_for_stage_three(self):
        result = pop_q_stage(
            metadata("盆腔器官脱垂POP-Q分期", "Pelvic Organ Prolapse Quantification"),
            {"aa_cm": 1, "ba_cm": 2, "c_cm": -3, "ap_cm": -2, "bp_cm": -1, "tvl_cm": 9},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["stage"], "III")
        self.assertEqual(result.value["leading_edge_cm"], 2.0)
        self.assertIn("stage III", result.interpretation)

    def test_pop_q_stage_zero_requires_all_points_three_cm_above_hymen(self):
        result = pop_q_stage(
            metadata("盆腔器官脱垂POP-Q分期", "Pelvic Organ Prolapse Quantification"),
            {"aa_cm": -3, "ba_cm": -3, "c_cm": -8, "ap_cm": -3, "bp_cm": -3, "tvl_cm": 8},
        )

        self.assertEqual(result.value["stage"], "0")
        self.assertIn("no prolapse", result.interpretation)


if __name__ == "__main__":
    unittest.main()
