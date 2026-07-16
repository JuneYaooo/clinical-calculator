import unittest

from clinical_calculators.calculators.common import behavioral_scores
from clinical_calculators.calculators.common.behavioral_scores import (
    audit_alcohol_use_disorders_prescored,
    audit_c_alcohol_use_screening,
    columbia_suicide_severity_screen_prescored,
    clinical_institute_withdrawal_assessment_alcohol_revised_prescored,
    epworth_sleepiness_scale,
    gad_7_anxiety_score,
    karolinska_sleepiness_scale,
    madrs_depression_rating_scale,
    mini_mental_state_examination_prescored,
    morningness_eveningness_questionnaire_score,
    panss_prescored,
    phq_9_depression_score,
    pittsburgh_sleep_quality_index_prescored,
    yale_brown_obsessive_compulsive_scale,
    young_mania_rating_scale,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="behavioral",
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


class CommonBehavioralScoresTest(unittest.TestCase):
    def test_cssrs_prescored_flags_recent_suicidal_behavior_as_high_acuity(self):
        result = columbia_suicide_severity_screen_prescored(
            metadata("哥伦比亚自杀严重度量表", "Columbia-Suicide Severity Rating Scale"),
            {"ideation_severity": 4, "suicidal_behavior": True, "recent_behavior": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["risk_level"], "high_acuity")
        self.assertEqual(result.value["ideation_severity"], 4)
        self.assertEqual(result.unit, "classification")
        self.assertIn("urgent", result.interpretation)

    def test_cssrs_prescored_rejects_ideation_severity_above_five(self):
        with self.assertRaises(ValueError):
            columbia_suicide_severity_screen_prescored(
                metadata("哥伦比亚自杀严重度量表", "Columbia-Suicide Severity Rating Scale"),
                {"ideation_severity": 6, "suicidal_behavior": False, "recent_behavior": False},
            )

    def test_cssrs_prescored_requires_ideation_severity(self):
        with self.assertRaises(KeyError):
            columbia_suicide_severity_screen_prescored(
                metadata("哥伦比亚自杀严重度量表", "Columbia-Suicide Severity Rating Scale"),
                {"suicidal_behavior": False, "recent_behavior": False},
            )

    def test_audit_prescored_sums_ten_zero_to_four_item_scores(self):
        result = audit_alcohol_use_disorders_prescored(
            metadata("AUDIT酒精使用障碍识别测试", "Alcohol Use Disorders Identification Test"),
            {"item_scores": [2, 2, 2, 1, 1, 0, 0, 0, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("hazardous", result.interpretation)

    def test_audit_prescored_score_twenty_is_possible_dependence_range(self):
        result = audit_alcohol_use_disorders_prescored(
            metadata("AUDIT酒精使用障碍识别测试", "Alcohol Use Disorders Identification Test"),
            {"item_scores": [2] * 10},
        )

        self.assertEqual(result.value, 20)
        self.assertIn("possible dependence", result.interpretation)

    def test_geriatric_depression_scale_15_scores_binary_coded_items(self):
        calculator = getattr(behavioral_scores, "geriatric_depression_scale_15", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("老年抑郁量表", "Geriatric Depression Scale-15"),
            {"items": [1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "points")
        self.assertIn("suggestive", result.interpretation)

    def test_confusion_assessment_method_requires_features_one_two_and_three_or_four(self):
        calculator = getattr(behavioral_scores, "confusion_assessment_method", None)
        self.assertIsNotNone(calculator)

        positive = calculator(
            metadata("CAM谵妄评估", "Confusion Assessment Method"),
            {
                "acute_onset_or_fluctuating_course": True,
                "inattention": True,
                "disorganized_thinking": False,
                "altered_level_of_consciousness": True,
            },
        )
        negative = calculator(
            metadata("CAM谵妄评估", "Confusion Assessment Method"),
            {
                "acute_onset_or_fluctuating_course": True,
                "inattention": False,
                "disorganized_thinking": True,
                "altered_level_of_consciousness": True,
            },
        )

        self.assertTrue(positive.value["cam_positive"])
        self.assertFalse(negative.value["cam_positive"])
        self.assertIn("positive", positive.interpretation)
        self.assertIn("negative", negative.interpretation)

    def test_insomnia_severity_index_score_twenty_two_is_severe(self):
        calculator = getattr(behavioral_scores, "insomnia_severity_index", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("失眠严重度指数", "Insomnia Severity Index"),
            {"items": [4, 4, 4, 4, 3, 2, 1]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 22)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_phq_9_score_four_is_minimal(self):
        result = phq_9_depression_score(
            metadata("PHQ-9抑郁评分", "Patient Health Questionnaire-9"),
            {"items": [0, 1, 1, 1, 1, 0, 0, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("minimal", result.interpretation)

    def test_phq_9_score_twenty_seven_is_severe(self):
        result = phq_9_depression_score(
            metadata("PHQ-9抑郁评分", "Patient Health Questionnaire-9"),
            {"items": [3] * 9},
        )

        self.assertEqual(result.value, 27)
        self.assertIn("severe", result.interpretation)

    def test_gad_7_score_fourteen_is_moderate(self):
        result = gad_7_anxiety_score(
            metadata("GAD-7焦虑评分", "Generalized Anxiety Disorder-7"),
            {"items": [2] * 7},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 14)
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_audit_c_male_score_four_is_positive(self):
        result = audit_c_alcohol_use_screening(
            metadata("AUDIT-C酒精使用筛查", "AUDIT-C Alcohol Use Screening"),
            {"items": [2, 1, 1], "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("positive", result.interpretation)
        self.assertIn(">=4 men", result.interpretation)

    def test_audit_c_female_score_three_is_positive(self):
        result = audit_c_alcohol_use_screening(
            metadata("AUDIT-C酒精使用筛查", "AUDIT-C Alcohol Use Screening"),
            {"items": [1, 1, 1], "sex": "female"},
        )

        self.assertEqual(result.value, 3)
        self.assertIn("positive", result.interpretation)
        self.assertIn(">=3 women", result.interpretation)

    def test_epworth_score_eight_is_normal_range(self):
        result = epworth_sleepiness_scale(
            metadata("EPWORTH睡眠量表（ESS）", "Epworth Sleepiness Scale"),
            {"items": [1] * 8},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("normal range", result.interpretation)

    def test_epworth_score_sixteen_is_severe(self):
        result = epworth_sleepiness_scale(
            metadata("EPWORTH睡眠量表（ESS）", "Epworth Sleepiness Scale"),
            {"items": [2] * 8},
        )

        self.assertEqual(result.value, 16)
        self.assertIn("severe", result.interpretation)

    def test_karolinska_sleepiness_scale_grade_nine_is_fighting_sleep(self):
        result = karolinska_sleepiness_scale(
            metadata("Karolinska嗜睡量表", "Karolinska Sleepiness Scale"),
            {"score": 9},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 9)
        self.assertEqual(result.unit, "grade")
        self.assertIn("fighting sleep", result.interpretation)

    def test_young_mania_rating_scale_sums_eleven_prescored_components(self):
        result = young_mania_rating_scale(
            metadata("Young躁狂量表", "Young Mania Rating Scale"),
            {"component_points": [4, 4, 4, 4, 8, 8, 4, 8, 8, 4, 4]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 60)
        self.assertEqual(result.unit, "points")

    def test_madrs_sums_ten_zero_to_six_item_scores(self):
        result = madrs_depression_rating_scale(
            metadata("蒙哥马利抑郁评定量表", "Montgomery-Asberg Depression Rating Scale"),
            {"items": [3] * 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 30)
        self.assertEqual(result.unit, "points")

    def test_ybocs_sums_ten_zero_to_four_item_scores(self):
        result = yale_brown_obsessive_compulsive_scale(
            metadata("耶鲁布朗强迫量表", "Yale-Brown Obsessive Compulsive Scale"),
            {"items": [3] * 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 30)
        self.assertIn("severe", result.interpretation)

    def test_panss_prescored_reports_subscale_and_total_scores(self):
        result = panss_prescored(
            metadata("阳性与阴性症状量表", "Positive and Negative Syndrome Scale"),
            {"positive_items": [4] * 7, "negative_items": [3] * 7, "general_items": [2] * 16},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["positive_score"], 28)
        self.assertEqual(result.value["negative_score"], 21)
        self.assertEqual(result.value["general_score"], 32)
        self.assertEqual(result.value["total_score"], 81)

    def test_psqi_prescored_sums_seven_component_scores(self):
        result = pittsburgh_sleep_quality_index_prescored(
            metadata("匹兹堡睡眠质量指数", "Pittsburgh Sleep Quality Index"),
            {"component_scores": [1, 0, 2, 1, 1, 0, 1]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("poor", result.interpretation)

    def test_meq_score_classifies_morning_evening_preference(self):
        result = morningness_eveningness_questionnaire_score(
            metadata("MEQ晨晚型问卷", "Morningness-Eveningness Questionnaire"),
            {"score": 72},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 72)
        self.assertIn("definite morning", result.interpretation)

    def test_mmse_prescored_total_uses_common_cognitive_screening_cutoffs(self):
        result = mini_mental_state_examination_prescored(
            metadata("简易精神状态检查", "Mini-Mental State Examination"),
            {"score": 23},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 23)
        self.assertIn("possible cognitive impairment", result.interpretation)

    def test_ciwa_ar_prescored_sums_ten_component_scores(self):
        result = clinical_institute_withdrawal_assessment_alcohol_revised_prescored(
            metadata(
                "CIWA-Ar的临床研究所的戒断反应评估量表",
                "Clinical Institute Withdrawal Assessment for Alcohol, Revised",
            ),
            {"component_scores": [2, 2, 2, 0, 2, 2, 2, 2, 2, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 18)
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_ciwa_ar_prescored_rejects_tactile_disturbances_above_seven(self):
        with self.assertRaises(ValueError):
            clinical_institute_withdrawal_assessment_alcohol_revised_prescored(
                metadata(
                    "CIWA-Ar的临床研究所的戒断反应评估量表",
                    "Clinical Institute Withdrawal Assessment for Alcohol, Revised",
                ),
                {"component_scores": [0, 0, 8, 0, 0, 0, 0, 0, 0, 0]},
            )


if __name__ == "__main__":
    unittest.main()
