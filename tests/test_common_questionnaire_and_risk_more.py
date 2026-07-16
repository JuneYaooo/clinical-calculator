import unittest

from clinical_calculators.calculators.common.questionnaire_and_risk_more import (
    aldrete_recovery_score,
    apfel_ponv_score,
    critical_care_pain_observation_tool,
    drug_abuse_screening_test_10,
    eating_assessment_tool_10,
    edmonton_symptom_assessment_system,
    flacc_pediatric_pain_score,
    follicular_lymphoma_international_prognostic_index,
    gerd_q_prescored,
    iciq_ui_short_form_prescored,
    incontinence_impact_questionnaire_7_prescored,
    international_prognostic_index_lymphoma,
    jankovic_rating_scale,
    lanss_pain_scale,
    numeric_rating_scale_pain,
    ocular_surface_disease_index,
    opioid_risk_tool,
    pain_catastrophizing_scale,
    pelvic_floor_distress_inventory_20_prescored,
    brief_pain_inventory_prescored,
    premature_ejaculation_diagnostic_tool_prescored,
    post_anesthetic_discharge_scoring_system,
    patient_oriented_eczema_measure,
    ramsay_sedation_scale,
    reflux_symptom_index,
    robson_ten_group_classification,
    sinonasal_outcome_test_22,
    speed_dry_eye_questionnaire_prescored,
    visual_function_index_14_prescored,
    voice_handicap_index_10,
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


class CommonQuestionnaireAndRiskMoreTest(unittest.TestCase):
    def test_osdi_uses_sum_times_25_over_answered_items(self):
        result = ocular_surface_disease_index(metadata("干眼症状指数"), {"items": [2] * 12})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 50)
        self.assertIn("severe", result.interpretation)

    def test_vhi10_eat10_rsi_and_poem_sum_precoded_item_scores(self):
        self.assertEqual(voice_handicap_index_10(metadata("嗓音障碍指数10项"), {"items": [2] * 10}).value, 20)
        self.assertEqual(eating_assessment_tool_10(metadata("吞咽障碍筛查量表"), {"items": [1] * 10}).value, 10)
        self.assertEqual(reflux_symptom_index(metadata("反流症状指数"), {"items": [2] * 9}).value, 18)
        self.assertEqual(patient_oriented_eczema_measure(metadata("患者导向湿疹量表"), {"items": [2] * 7}).value, 14)

    def test_apfel_ponv_score_counts_four_risk_factors(self):
        result = apfel_ponv_score(
            metadata("Apfel术后恶心呕吐风险评分"),
            {"female": True, "non_smoker": True, "history_ponv_or_motion_sickness": True, "postoperative_opioids": False},
        )

        self.assertEqual(result.value, 3)
        self.assertIn("high", result.interpretation)

    def test_aldrete_score_sums_five_zero_to_two_components(self):
        result = aldrete_recovery_score(
            metadata("Aldrete麻醉恢复评分"),
            {"activity": 2, "respiration": 2, "circulation": 2, "consciousness": 2, "oxygen_saturation": 1},
        )

        self.assertEqual(result.value, 9)
        self.assertIn("discharge", result.interpretation)

    def test_padss_sums_five_zero_to_two_components(self):
        result = post_anesthetic_discharge_scoring_system(
            metadata("PADSS日间手术离院评分"),
            {"vital_signs": 2, "activity": 2, "nausea_vomiting": 2, "pain": 1, "surgical_bleeding": 2},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 9)
        self.assertEqual(result.unit, "points")
        self.assertIn("discharge", result.interpretation)

    def test_cpot_sums_four_zero_to_two_components(self):
        result = critical_care_pain_observation_tool(
            metadata("行为疼痛观察工具"),
            {"facial_expression": 1, "body_movements": 2, "muscle_tension": 1, "ventilator_compliance_or_vocalization": 2},
        )

        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")

    def test_flacc_sums_five_zero_to_two_components(self):
        result = flacc_pediatric_pain_score(
            metadata("FLACC儿童疼痛评分"),
            {"face": 2, "legs": 1, "activity": 2, "cry": 1, "consolability": 2},
        )

        self.assertEqual(result.value, 8)
        self.assertIn("severe", result.interpretation)

    def test_numeric_rating_scale_pain_classifies_severity(self):
        result = numeric_rating_scale_pain(metadata("数字疼痛评分"), {"score": 7})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_ramsay_sedation_scale_grade_four_is_brisk_response(self):
        result = ramsay_sedation_scale(metadata("Ramsay镇静评分"), {"grade": 4})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "grade")
        self.assertIn("brisk", result.interpretation)

    def test_flipi_counts_five_adverse_factors(self):
        result = follicular_lymphoma_international_prognostic_index(
            metadata("FLIPI滤泡淋巴瘤指数"),
            {
                "age_years": 61,
                "ann_arbor_stage": 4,
                "hemoglobin_g_dl": 11,
                "nodal_areas": 5,
                "ldh_above_normal": True,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertIn("high", result.interpretation)

    def test_ipi_counts_five_adverse_factors(self):
        result = international_prognostic_index_lymphoma(
            metadata("IPI淋巴瘤预后指数"),
            {
                "age_years": 70,
                "ann_arbor_stage": 3,
                "ldh_above_normal": True,
                "ecog_performance_status": 2,
                "extranodal_sites": 2,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertIn("high", result.interpretation)

    def test_robson_group_five_for_previous_cesarean_single_cephalic_term(self):
        result = robson_ten_group_classification(
            metadata("Robson十组剖宫产分类"),
            {
                "parity": "multiparous",
                "previous_cesarean": True,
                "fetal_presentation": "cephalic",
                "fetal_count": 1,
                "gestational_age_weeks": 39,
                "labor_onset": "spontaneous",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["group"], 5)
        self.assertIn("previous cesarean", result.interpretation)

    def test_robson_group_ten_for_single_cephalic_preterm(self):
        result = robson_ten_group_classification(
            metadata("Robson十组剖宫产分类"),
            {
                "parity": "nulliparous",
                "previous_cesarean": False,
                "fetal_presentation": "cephalic",
                "fetal_count": 1,
                "gestational_age_weeks": 35,
                "labor_onset": "prelabor_cesarean",
            },
        )

        self.assertEqual(result.value["group"], 10)

    def test_sinonasal_outcome_test_22_sums_twenty_two_zero_to_five_items(self):
        result = sinonasal_outcome_test_22(
            metadata("鼻腔鼻窦结局测试22项"),
            {"items": [5] * 10 + [0] * 12},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 50)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher sinonasal", result.interpretation)

    def test_jankovic_rating_scale_sums_severity_and_frequency_zero_to_four(self):
        result = jankovic_rating_scale(
            metadata("Jankovic评分"),
            {"severity": 3, "frequency": 4},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 7)
        self.assertEqual(result.value["severity"], 3)
        self.assertEqual(result.value["frequency"], 4)
        self.assertEqual(result.unit, "points")

    def test_dast_10_scores_coded_boolean_responses_with_item_three_reverse_scored(self):
        result = drug_abuse_screening_test_10(
            metadata("DAST-10药物滥用筛查"),
            {"items": [True, True, False, True, True, False, False, False, False, False]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_lanss_sums_seven_coded_component_points(self):
        result = lanss_pain_scale(
            metadata("LANSS神经病理性疼痛量表"),
            {"component_points": [5, 5, 3, 2, 1, 5, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 24)
        self.assertIn("neuropathic", result.interpretation.lower())

    def test_pain_catastrophizing_scale_sums_thirteen_precoded_items(self):
        result = pain_catastrophizing_scale(
            metadata("疼痛灾难化量表"),
            {"items": [2] * 13},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 26)
        self.assertEqual(result.unit, "points")

    def test_brief_pain_inventory_reports_severity_and_interference_means(self):
        result = brief_pain_inventory_prescored(
            metadata("简明疼痛量表"),
            {"severity_items": [2, 4, 6, 8], "interference_items": [1, 2, 3, 4, 5, 6, 7]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["severity_mean"], 5)
        self.assertEqual(result.value["interference_mean"], 4)
        self.assertEqual(result.unit, "points")

    def test_gerd_q_prescored_sums_six_zero_to_three_items(self):
        result = gerd_q_prescored(
            metadata("GERD问卷"),
            {"items": [2, 2, 1, 1, 1, 1]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertIn("GERD likelihood", result.interpretation)

    def test_iciq_ui_short_form_sums_three_scored_domains(self):
        result = iciq_ui_short_form_prescored(
            metadata("ICIQ尿失禁简表"),
            {"frequency": 4, "amount": 4, "life_impact": 8},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 16)
        self.assertEqual(result.unit, "points")

    def test_iiq7_transforms_seven_zero_to_three_prescored_items(self):
        result = incontinence_impact_questionnaire_7_prescored(
            metadata("IIQ-7尿失禁影响问卷"),
            {"items": [0, 1, 2, 3, 0, 1, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 42.8571)
        self.assertEqual(result.unit, "score")
        self.assertIn("0-100", result.interpretation)

    def test_pfdi20_reports_three_scaled_subscores_and_summary_total(self):
        result = pelvic_floor_distress_inventory_20_prescored(
            metadata("PFDI-20盆底困扰量表"),
            {
                "popdi_6_items": [0, 1, 2, 3, 4, 2],
                "cradi_8_items": [1, 1, 2, 2, 3, 3, 4, 4],
                "udi_6_items": [4, 4, 3, 3, 2, 2],
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["popdi_6_score"], 50)
        self.assertEqual(result.value["cradi_8_score"], 62.5)
        self.assertEqual(result.value["udi_6_score"], 75)
        self.assertEqual(result.value["total_score"], 187.5)
        self.assertEqual(result.unit, "score")

    def test_vf14_excludes_not_applicable_items_and_scales_to_100(self):
        result = visual_function_index_14_prescored(
            metadata("VF-14视觉功能指数"),
            {"item_scores": [4, 3, None, 2, 1, 0, None, 4, 3, 2, 1, 0, 4, None]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["answered_items"], 11)
        self.assertAlmostEqual(result.value["score"], 54.5455)
        self.assertEqual(result.unit, "score")

    def test_speed_sums_frequency_and_severity_components(self):
        result = speed_dry_eye_questionnaire_prescored(
            metadata("SPEED干眼问卷"),
            {"frequency_scores": [0, 1, 2, 3], "severity_scores": [1, 2, 3, 4]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["frequency_total"], 6)
        self.assertEqual(result.value["severity_total"], 10)
        self.assertEqual(result.value["total_score"], 16)
        self.assertEqual(result.unit, "points")

    def test_new_prescored_questionnaires_validate_lengths_and_ranges(self):
        with self.assertRaises(ValueError):
            incontinence_impact_questionnaire_7_prescored(metadata("IIQ-7"), {"items": [0] * 6})
        with self.assertRaises(ValueError):
            pelvic_floor_distress_inventory_20_prescored(
                metadata("PFDI-20"),
                {"popdi_6_items": [0] * 6, "cradi_8_items": [0] * 8, "udi_6_items": [5] * 6},
            )
        with self.assertRaises(ValueError):
            visual_function_index_14_prescored(metadata("VF-14"), {"item_scores": [None] * 14})
        with self.assertRaises(ValueError):
            speed_dry_eye_questionnaire_prescored(
                metadata("SPEED"),
                {"frequency_scores": [0, 1, 2, 4], "severity_scores": [0, 1, 2, 3]},
            )

    def test_pedt_prescored_classifies_likely_premature_ejaculation(self):
        result = premature_ejaculation_diagnostic_tool_prescored(
            metadata("早泄诊断工具"),
            {"items": [3, 3, 2, 2, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertIn("likely", result.interpretation)

    def test_opioid_risk_tool_applies_sex_specific_points(self):
        result = opioid_risk_tool(
            metadata("阿片风险工具"),
            {
                "sex": "female",
                "family_history_alcohol": True,
                "family_history_illegal_drugs": True,
                "family_history_prescription_drugs": False,
                "personal_history_alcohol": False,
                "personal_history_illegal_drugs": True,
                "personal_history_prescription_drugs": False,
                "age_16_to_45": True,
                "preadolescent_sexual_abuse": True,
                "psychological_disease": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13)
        self.assertIn("high", result.interpretation.lower())

    def test_esas_sums_nine_core_symptom_scores(self):
        result = edmonton_symptom_assessment_system(
            metadata("ESAS症状评估量表"),
            {"symptom_scores": [3] * 9, "optional_wellbeing_score": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["core_total"], 27)
        self.assertEqual(result.value["total_with_optional"], 32)
        self.assertEqual(result.unit, "points")


if __name__ == "__main__":
    unittest.main()
