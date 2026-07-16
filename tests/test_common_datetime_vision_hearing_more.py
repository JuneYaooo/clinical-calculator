import unittest

from clinical_calculators.calculators.common.datetime_vision_hearing_more import (
    brodsky_tonsil_grading_scale,
    diabetic_retinopathy_severity_scale,
    estimated_due_date_and_gestational_age,
    friedman_staging_system,
    house_brackmann_facial_nerve_grade,
    iol_power_srk_formula,
    lund_kennedy_endoscopic_score,
    lund_mackay_ct_score,
    nei_visual_function_questionnaire_25,
    ocular_trauma_score,
    pure_tone_average,
    retinopathy_of_prematurity_classification,
    visual_acuity_from_logmar,
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


class CommonDatetimeVisionHearingMoreTest(unittest.TestCase):
    def test_estimated_due_date_and_gestational_age_from_lmp(self):
        calculation = estimated_due_date_and_gestational_age(
            metadata("预产期与孕周计算"),
            {"lmp_date": "2026-01-01", "as_of_date": "2026-03-12"},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["estimated_due_date"], "2026-10-08")
        self.assertEqual(calculation.value["gestational_age_days"], 70)
        self.assertEqual(calculation.value["gestational_age"], "10w0d")

    def test_estimated_due_date_from_ultrasound_exam(self):
        calculation = estimated_due_date_and_gestational_age(
            metadata("预产期与孕周计算"),
            {
                "ultrasound_exam_date": "2026-03-12",
                "gestational_age_days_at_ultrasound": 70,
                "as_of_date": "2026-03-19",
            },
        )

        self.assertEqual(calculation.value["estimated_due_date"], "2026-10-08")
        self.assertEqual(calculation.value["gestational_age"], "11w0d")

    def test_visual_acuity_from_logmar(self):
        calculation = visual_acuity_from_logmar(metadata("视力LogMAR换算"), {"logmar": 0.3})

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["decimal_acuity"], 0.5012)
        self.assertEqual(calculation.value["snellen_20_denominator"], 39.9052)
        self.assertEqual(calculation.value["etdrs_letters"], 70)

    def test_ocular_trauma_score_subtracts_risk_factor_points_and_assigns_category(self):
        calculation = ocular_trauma_score(
            metadata("眼外伤评分"),
            {
                "initial_visual_acuity": "lp_hm",
                "globe_rupture": True,
                "endophthalmitis": False,
                "perforating_injury": True,
                "retinal_detachment": False,
                "relative_afferent_pupillary_defect": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["raw_score"], 23)
        self.assertEqual(calculation.value["category"], 1)
        self.assertEqual(calculation.unit, "OTS category")

    def test_ocular_trauma_score_rejects_unknown_visual_acuity_code(self):
        with self.assertRaises(ValueError):
            ocular_trauma_score(metadata("眼外伤评分"), {"initial_visual_acuity": "20_20"})

    def test_diabetic_retinopathy_severity_returns_coded_grade(self):
        calculation = diabetic_retinopathy_severity_scale(
            metadata("糖尿病视网膜病变严重度"),
            {"severity": "severe_npdr"},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], "severe_npdr")
        self.assertEqual(calculation.value["order"], 3)
        self.assertIn("severe nonproliferative", calculation.interpretation)

    def test_rop_classification_returns_zone_stage_plus_disease_summary(self):
        calculation = retinopathy_of_prematurity_classification(
            metadata("早产儿视网膜病变分区分期"),
            {"zone": 1, "stage": 3, "plus_disease": "plus"},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["zone"], 1)
        self.assertEqual(calculation.value["stage"], 3)
        self.assertEqual(calculation.value["plus_disease"], "plus")
        self.assertIn("Zone I", calculation.interpretation)

    def test_rop_classification_rejects_invalid_stage(self):
        with self.assertRaises(ValueError):
            retinopathy_of_prematurity_classification(
                metadata("早产儿视网膜病变分区分期"),
                {"zone": 2, "stage": 6, "plus_disease": "none"},
            )

    def test_pure_tone_average_supports_three_or_four_frequency_average(self):
        three = pure_tone_average(
            metadata("纯音平均听阈"),
            {"threshold_500_hz_db": 20, "threshold_1000_hz_db": 30, "threshold_2000_hz_db": 40},
        )
        four = pure_tone_average(
            metadata("纯音平均听阈"),
            {
                "threshold_500_hz_db": 20,
                "threshold_1000_hz_db": 30,
                "threshold_2000_hz_db": 40,
                "threshold_4000_hz_db": 50,
            },
        )

        self.assertEqual(three.value, 30)
        self.assertEqual(four.value, 35)
        self.assertEqual(three.unit, "dB HL")

    def test_lund_mackay_ct_score_sums_bilateral_sinus_and_omc_scores(self):
        calculation = lund_mackay_ct_score(
            metadata("鼻窦CT Lund-Mackay评分"),
            {
                "left": {"maxillary": 2, "anterior_ethmoid": 1, "posterior_ethmoid": 0, "sphenoid": 2, "frontal": 1, "omc": 2},
                "right": {"maxillary": 0, "anterior_ethmoid": 1, "posterior_ethmoid": 2, "sphenoid": 0, "frontal": 1, "omc": 0},
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 12)
        self.assertEqual(calculation.unit, "points")

    def test_lund_kennedy_endoscopic_score_sums_bilateral_zero_to_two_items(self):
        calculation = lund_kennedy_endoscopic_score(
            metadata("鼻内镜Lund-Kennedy评分"),
            {
                "left": {"polyps": 2, "edema": 1, "discharge": 1, "scarring": 0, "crusting": 0},
                "right": {"polyps": 1, "edema": 2, "discharge": 0, "scarring": 1, "crusting": 1},
            },
        )

        self.assertEqual(calculation.value, 9)
        self.assertEqual(calculation.unit, "points")

    def test_house_brackmann_returns_coded_grade_and_severity_label(self):
        calculation = house_brackmann_facial_nerve_grade(
            metadata("House-Brackmann面神经分级"),
            {"grade": 4},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], 4)
        self.assertEqual(calculation.value["roman"], "IV")
        self.assertEqual(calculation.value["severity"], "moderately severe dysfunction")
        self.assertEqual(calculation.unit, "House-Brackmann grade")

    def test_house_brackmann_rejects_out_of_range_grade(self):
        with self.assertRaises(ValueError):
            house_brackmann_facial_nerve_grade(
                metadata("House-Brackmann面神经分级"),
                {"grade": 7},
            )

    def test_friedman_staging_uses_tongue_position_tonsil_size_and_bmi(self):
        stage_i = friedman_staging_system(
            metadata("Friedman舌位和扁桃体分期"),
            {"friedman_tongue_position": 2, "tonsil_size": 4, "bmi": 28},
        )
        stage_ii = friedman_staging_system(
            metadata("Friedman舌位和扁桃体分期"),
            {"friedman_tongue_position": 4, "tonsil_size": 3, "bmi": 31},
        )
        stage_iii = friedman_staging_system(
            metadata("Friedman舌位和扁桃体分期"),
            {"friedman_tongue_position": 3, "tonsil_size": 2, "bmi": 34},
        )
        stage_iv = friedman_staging_system(
            metadata("Friedman舌位和扁桃体分期"),
            {"friedman_tongue_position": 1, "tonsil_size": 4, "bmi": 41},
        )

        self.assertEqual(stage_i.value["stage"], 1)
        self.assertEqual(stage_ii.value["stage"], 2)
        self.assertEqual(stage_iii.value["stage"], 3)
        self.assertEqual(stage_iv.value["stage"], 4)
        self.assertEqual(stage_i.unit, "Friedman stage")

    def test_friedman_stage_iv_for_significant_anatomic_deformity(self):
        calculation = friedman_staging_system(
            metadata("Friedman舌位和扁桃体分期"),
            {
                "friedman_tongue_position": 1,
                "tonsil_size": 4,
                "bmi": 27,
                "significant_craniofacial_or_anatomic_deformity": True,
            },
        )

        self.assertEqual(calculation.value["stage"], 4)
        self.assertEqual(calculation.value["stage_reason"], "stage IV criterion")

    def test_brodsky_tonsil_grading_scale_uses_airway_occupation_thresholds(self):
        grade_0 = brodsky_tonsil_grading_scale(
            metadata("Brodsky扁桃体大小分级"),
            {"tonsillar_airway_occupation_percent": 0, "tonsils_within_fossa": True},
        )
        grade_2 = brodsky_tonsil_grading_scale(
            metadata("Brodsky扁桃体大小分级"),
            {"tonsillar_airway_occupation_percent": 50},
        )
        grade_4 = brodsky_tonsil_grading_scale(
            metadata("Brodsky扁桃体大小分级"),
            {"tonsillar_airway_occupation_percent": 76},
        )

        self.assertEqual(grade_0.value["grade"], 0)
        self.assertEqual(grade_2.value["grade"], 2)
        self.assertEqual(grade_4.value["grade"], 4)
        self.assertEqual(grade_4.unit, "Brodsky grade")

    def test_brodsky_tonsil_grading_scale_rejects_percent_outside_zero_to_100(self):
        with self.assertRaises(ValueError):
            brodsky_tonsil_grading_scale(
                metadata("Brodsky扁桃体大小分级"),
                {"tonsillar_airway_occupation_percent": 125},
            )

    def test_iol_power_srk_formula_uses_a_constant_axial_length_and_average_keratometry(self):
        calculation = iol_power_srk_formula(
            metadata("SRK人工晶状体度数"),
            {"a_constant": 118.0, "axial_length_mm": 23.5, "average_keratometry_d": 43.0},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 20.55, places=4)
        self.assertEqual(calculation.unit, "D")
        self.assertIn("SRK", calculation.interpretation)

    def test_nei_visual_function_questionnaire_25_averages_prescored_subscales(self):
        item_scores = {
            "1": 0,
            "2": 80,
            "3": 70,
            "4": 60,
            "5": 90,
            "6": 80,
            "7": 70,
            "8": 60,
            "9": 50,
            "10": 40,
            "11": 100,
            "12": 30,
            "13": 90,
            "14": 40,
            "15c": 100,
            "16": 50,
            "16a": 0,
            "17": 75,
            "18": 25,
            "19": 20,
            "20": 100,
            "21": 60,
            "22": 50,
            "23": 75,
            "24": 50,
            "25": 40,
        }

        calculation = nei_visual_function_questionnaire_25(
            metadata("NEI视觉功能问卷25项"),
            {"item_scores": item_scores},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["subscales"]["general_health"], 0)
        self.assertEqual(calculation.value["subscales"]["near_activities"], 80)
        self.assertEqual(calculation.value["subscales"]["driving"], 50)
        self.assertAlmostEqual(calculation.value["composite_score"], 58.6364, places=4)
        self.assertEqual(calculation.unit, "0-100 score")

    def test_nei_visual_function_questionnaire_25_omits_missing_subscales_from_composite(self):
        calculation = nei_visual_function_questionnaire_25(
            metadata("NEI视觉功能问卷25项"),
            {
                "item_scores": {
                    "2": 100,
                    "5": 50,
                    "6": None,
                    "7": 100,
                    "15c": None,
                    "16": None,
                    "16a": None,
                }
            },
        )

        self.assertEqual(calculation.value["subscales"]["general_vision"], 100)
        self.assertEqual(calculation.value["subscales"]["near_activities"], 75)
        self.assertNotIn("driving", calculation.value["subscales"])
        self.assertEqual(calculation.value["composite_score"], 87.5)

    def test_nei_visual_function_questionnaire_25_rejects_unknown_or_out_of_range_scores(self):
        with self.assertRaises(ValueError):
            nei_visual_function_questionnaire_25(
                metadata("NEI视觉功能问卷25项"),
                {"item_scores": {"2": 101}},
            )
        with self.assertRaises(ValueError):
            nei_visual_function_questionnaire_25(
                metadata("NEI视觉功能问卷25项"),
                {"item_scores": {"26": 50}},
            )


if __name__ == "__main__":
    unittest.main()
