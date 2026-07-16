import unittest

from clinical_calculators.calculators.common.respiratory_scores import (
    asthma_control_test_score,
    berlin_questionnaire_sleep_apnea_risk,
    bode_index,
    cat_score,
    childhood_asthma_control_test_score,
    decaf_score,
    gap_index_ipf,
    hemoglobin_corrected_dlco,
    mmrc_dyspnea_grade,
    pneumonia_severity_index,
    predicted_postoperative_fev1_anatomic,
    predicted_postoperative_fev1_perfusion,
    rhinitis_control_assessment_test_score,
    stop_bang_sleep_apnea_screening,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="respiratory",
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


class CommonRespiratoryScoresTest(unittest.TestCase):
    def test_stop_bang_all_risk_factors_is_high_risk(self):
        result = stop_bang_sleep_apnea_screening(
            metadata("STOP-Bang睡眠呼吸暂停筛查", "STOP-Bang Sleep Apnea Screening"),
            {
                "snoring": True,
                "tired": True,
                "observed_apnea": True,
                "high_blood_pressure": True,
                "bmi": 36,
                "age_years": 60,
                "neck_circumference_cm": 42,
                "sex": "male",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_bode_index_scores_component_thresholds(self):
        result = bode_index(
            metadata("BODE指数", "BODE Index"),
            {
                "fev1_percent_predicted": 40,
                "six_min_walk_m": 200,
                "mmrc_grade": 3,
                "bmi": 20,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "points")

    def test_pneumonia_severity_index_scores_points_and_risk_class(self):
        result = pneumonia_severity_index(
            metadata("成人社区获得性肺炎严重程度评分", "Pneumonia Severity Index"),
            {
                "age_years": 72,
                "sex": "female",
                "nursing_home_resident": True,
                "neoplastic_disease": False,
                "liver_disease": False,
                "congestive_heart_failure": True,
                "cerebrovascular_disease": False,
                "renal_disease": False,
                "altered_mental_status": True,
                "respiratory_rate": 32,
                "systolic_bp": 88,
                "temperature_c": 34.8,
                "pulse": 130,
                "arterial_ph": 7.30,
                "bun_mg_dl": 35,
                "sodium_mEq_l": 128,
                "glucose_mg_dl": 260,
                "hematocrit_percent": 29,
                "pao2_mm_hg": 55,
                "pleural_effusion": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 277)
        self.assertEqual(result.value["risk_class"], "V")
        self.assertEqual(result.unit, "points")

    def test_hemoglobin_corrected_dlco_uses_sex_age_coefficient(self):
        male = hemoglobin_corrected_dlco(
            metadata("纠正贫血后的一氧化碳弥散功能试验（DLCO）", "Hemoglobin-Corrected DLCO"),
            {"sex": "male", "age_years": 40, "hemoglobin_g_dl": 10.0, "predicted_dlco": 25.0},
        )
        female = hemoglobin_corrected_dlco(
            metadata("纠正贫血后的一氧化碳弥散功能试验（DLCO）", "Hemoglobin-Corrected DLCO"),
            {"sex": "female", "age_years": 40, "hemoglobin_g_dl": 10.0, "predicted_dlco": 25.0},
        )

        self.assertAlmostEqual(male.value, 21.0188, places=4)
        self.assertAlmostEqual(female.value, 21.9298, places=4)
        self.assertEqual(male.unit, "same as input DLCO")

    def test_cat_score_maximum_is_very_high_impact(self):
        result = cat_score(
            metadata("CAT评分", "COPD Assessment Test"),
            {"items": [5] * 8},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 40)
        self.assertEqual(result.unit, "points")
        self.assertIn("very high impact", result.interpretation)

    def test_mmrc_grade_two_returns_grade_and_label(self):
        result = mmrc_dyspnea_grade(
            metadata("mMRC呼吸困难分级", "Modified Medical Research Council Dyspnea Scale"),
            {"grade": 2},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 2)
        self.assertEqual(result.unit, "points")
        self.assertIn("grade 2", result.interpretation)

    def test_predicted_postoperative_fev1_perfusion_uses_removed_fraction(self):
        result = predicted_postoperative_fev1_perfusion(
            metadata("预测肺切除术后FEV1（灌注法）", "Predicted Postoperative FEV1 by Perfusion"),
            {"preoperative_fev1_l": 2.0, "fraction_perfusion_removed": 0.25},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1.5)
        self.assertEqual(result.unit, "L")

    def test_predicted_postoperative_fev1_anatomic_uses_removed_segments(self):
        result = predicted_postoperative_fev1_anatomic(
            metadata("预测肺切除术后FEV1（解剖法）", "Predicted Postoperative FEV1 by Anatomic Segments"),
            {"preoperative_fev1_l": 2.0, "segments_removed": 5, "total_segments": 19},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 1.4737, places=4)
        self.assertEqual(result.unit, "L")

    def test_decaf_score_sums_all_derivation_components(self):
        result = decaf_score(
            metadata("DECAF COPD急性加重死亡风险", "DECAF Score"),
            {
                "emrcd_grade": "5b",
                "eosinophils_10e9_l": 0.04,
                "consolidation": True,
                "arterial_ph": 7.29,
                "atrial_fibrillation": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 6)
        self.assertEqual(result.value["risk_group"], "high")
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_decaf_score_low_risk_with_no_markers(self):
        result = decaf_score(
            metadata("DECAF COPD急性加重死亡风险", "DECAF Score"),
            {
                "emrcd_grade": "3",
                "eosinophils_10e9_l": 0.2,
                "consolidation": False,
                "arterial_ph": 7.38,
                "atrial_fibrillation": False,
            },
        )

        self.assertEqual(result.value["score"], 0)
        self.assertEqual(result.value["risk_group"], "low")

    def test_gap_index_ipf_stage_three_when_maximal_points(self):
        result = gap_index_ipf(
            metadata("GAP特发性肺纤维化分期", "GAP Index for IPF"),
            {
                "age_years": 70,
                "sex": "male",
                "fvc_percent_predicted": 48,
                "dlco_percent_predicted": 30,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 7)
        self.assertEqual(result.value["stage"], "III")
        self.assertEqual(result.unit, "points")
        self.assertIn("stage III", result.interpretation)

    def test_gap_index_ipf_allows_missing_dlco_as_three_points(self):
        result = gap_index_ipf(
            metadata("GAP特发性肺纤维化分期", "GAP Index for IPF"),
            {
                "age_years": 62,
                "sex": "female",
                "fvc_percent_predicted": 74,
                "dlco_unable": True,
            },
        )

        self.assertEqual(result.value["score"], 5)
        self.assertEqual(result.value["stage"], "II")

    def test_asthma_control_test_score_well_controlled_at_twenty(self):
        result = asthma_control_test_score(
            metadata("哮喘控制测试", "Asthma Control Test"),
            {"items": [4, 4, 4, 4, 4]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 20)
        self.assertEqual(result.unit, "points")
        self.assertIn("well controlled", result.interpretation)

    def test_asthma_control_test_score_very_poorly_controlled_at_fifteen(self):
        result = asthma_control_test_score(
            metadata("哮喘控制测试", "Asthma Control Test"),
            {"items": [3, 3, 3, 3, 3]},
        )

        self.assertEqual(result.value, 15)
        self.assertIn("very poorly controlled", result.interpretation)

    def test_berlin_questionnaire_high_risk_with_two_positive_categories(self):
        result = berlin_questionnaire_sleep_apnea_risk(
            metadata("柏林睡眠呼吸暂停问卷", "Berlin Questionnaire"),
            {
                "category_1_positive": True,
                "category_2_positive": False,
                "category_3_positive": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["positive_categories"], 2)
        self.assertEqual(result.value["risk"], "high")
        self.assertEqual(result.unit, "categories")
        self.assertIn("high", result.interpretation)

    def test_berlin_questionnaire_low_risk_with_one_positive_category(self):
        result = berlin_questionnaire_sleep_apnea_risk(
            metadata("柏林睡眠呼吸暂停问卷", "Berlin Questionnaire"),
            {
                "category_1_positive": False,
                "category_2_positive": True,
                "category_3_positive": False,
            },
        )

        self.assertEqual(result.value["positive_categories"], 1)
        self.assertEqual(result.value["risk"], "low")

    def test_rhinitis_control_assessment_test_score_uncontrolled_at_twenty_one(self):
        result = rhinitis_control_assessment_test_score(
            metadata("过敏性鼻炎控制测试", "Rhinitis Control Assessment Test"),
            {"items": [4, 4, 4, 3, 3, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 21)
        self.assertEqual(result.unit, "points")
        self.assertIn("not well controlled", result.interpretation)

    def test_rhinitis_control_assessment_test_score_controlled_above_twenty_one(self):
        result = rhinitis_control_assessment_test_score(
            metadata("过敏性鼻炎控制测试", "Rhinitis Control Assessment Test"),
            {"items": [4, 4, 4, 4, 4, 4]},
        )

        self.assertEqual(result.value, 24)
        self.assertIn("well controlled", result.interpretation)

    def test_childhood_asthma_control_test_sums_seven_prescored_items(self):
        result = childhood_asthma_control_test_score(
            metadata("儿童哮喘控制测试", "Childhood Asthma Control Test"),
            {"items": [3, 3, 3, 3, 2, 2, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 18)
        self.assertEqual(result.unit, "points")
        self.assertIn("not well controlled", result.interpretation)


if __name__ == "__main__":
    unittest.main()
