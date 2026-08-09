import unittest

from clinical_calculators.calculators.common import neuro_classification_scores
from clinical_calculators.calculators.common.neuro_classification_scores import (
    expanded_disability_status_scale,
    hunt_hess_subarachnoid_hemorrhage_grade,
    marshall_ct_classification,
    multiple_sclerosis_functional_composite,
    nih_stroke_scale,
    quantitative_myasthenia_gravis_score,
    rotterdam_ct_score,
    unified_parkinsons_disease_rating_scale_prescored,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="neuro classification",
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


class CommonNeuroClassificationScoresTest(unittest.TestCase):
    def test_edss_accepts_prescored_half_step_and_reports_severity(self):
        result = expanded_disability_status_scale(
            metadata("扩展残疾状态量表", "Expanded Disability Status Scale"),
            {"score": 6.5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6.5)
        self.assertEqual(result.unit, "points")
        self.assertIn("assistance", result.interpretation)

    def test_edss_rejects_non_half_step_score(self):
        with self.assertRaises(ValueError):
            expanded_disability_status_scale(
                metadata("扩展残疾状态量表", "Expanded Disability Status Scale"),
                {"score": 6.25},
            )

    def test_msfc_averages_three_prescored_z_scores(self):
        result = multiple_sclerosis_functional_composite(
            metadata("多发性硬化功能复合评分", "Multiple Sclerosis Functional Composite"),
            {"timed_25_foot_walk_z": -0.5, "nine_hole_peg_test_z": 0.25, "cognitive_test_z": 1.0},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0.25)
        self.assertEqual(result.unit, "z-score")
        self.assertIn("higher functional performance", result.interpretation)

    def test_qmg_sums_thirteen_prescored_zero_to_three_items(self):
        result = quantitative_myasthenia_gravis_score(
            metadata("重症肌无力量化评分", "Quantitative Myasthenia Gravis Score"),
            {"item_scores": [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 21)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher weakness", result.interpretation)

    def test_updrs_prescored_sums_part_scores(self):
        result = unified_parkinsons_disease_rating_scale_prescored(
            metadata("UPDRS帕金森病评分", "Unified Parkinson's Disease Rating Scale"),
            {"part_scores": {"part_i": 8, "part_ii": 18, "part_iii": 32, "part_iv": 6}},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 64)
        self.assertEqual(result.value["part_scores"]["part_iii"], 32)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher Parkinson", result.interpretation)

    def test_updrs_prescored_rejects_negative_part_score(self):
        with self.assertRaises(ValueError):
            unified_parkinsons_disease_rating_scale_prescored(
                metadata("UPDRS帕金森病评分", "Unified Parkinson's Disease Rating Scale"),
                {"part_scores": {"part_i": 0, "part_ii": -1, "part_iii": 0, "part_iv": 0}},
            )

    def test_hoehn_yahr_stage_three_identifies_postural_instability(self):
        calculator = getattr(neuro_classification_scores, "hoehn_yahr_scale", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("Hoehn-Yahr帕金森分期", "Hoehn and Yahr Scale"),
            {"stage": 3},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "stage")
        self.assertIn("postural instability", result.interpretation)

    def test_race_stroke_scale_sums_component_scores_and_flags_lvo_cutoff(self):
        calculator = getattr(neuro_classification_scores, "rapid_arterial_occlusion_evaluation_scale", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("RACE卒中量表", "Rapid Arterial Occlusion Evaluation Scale"),
            {
                "facial_palsy": 1,
                "arm_motor_function": 2,
                "leg_motor_function": 1,
                "head_and_gaze_deviation": 1,
                "cortical_signs": 2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "points")
        self.assertIn("large vessel occlusion", result.interpretation)

    def test_nihss_all_zeros_has_no_symptoms_interpretation(self):
        result = nih_stroke_scale(
            metadata("NIH 卒中评分", "NIH Stroke Scale"),
            {"items": [0] * 15},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("no symptoms", result.interpretation)

    def test_nihss_maxima_sum_matches_supported_item_maxima(self):
        maxima = [3, 2, 2, 2, 3, 3, 4, 4, 4, 4, 2, 2, 3, 2, 2]

        result = nih_stroke_scale(
            metadata("NIH 卒中评分", "NIH Stroke Scale"),
            {"items": maxima},
        )

        self.assertEqual(result.value, sum(maxima))
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_nihss_rejects_item_score_over_standard_maximum(self):
        items = [0] * 15
        items[0] = 4

        with self.assertRaises(ValueError):
            nih_stroke_scale(
                metadata("NIH 卒中评分", "NIH Stroke Scale"),
                {"items": items},
            )

    def test_hunt_hess_grade_four_returns_grade_and_stupor_label(self):
        result = hunt_hess_subarachnoid_hemorrhage_grade(
            metadata("Hunt-Hess蛛网膜下腔出血分级", "Hunt-Hess SAH Grade"),
            {"grade": 4},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "grade")
        self.assertIn("stupor", result.interpretation)

    def test_marshall_ct_classification_non_evacuated_large_mass_lesion_is_grade_six(self):
        result = marshall_ct_classification(
            metadata("Marshall CT颅脑损伤分类", "Marshall CT Classification"),
            {
                "visible_intracranial_pathology": True,
                "cisterns": "normal",
                "midline_shift_mm": 3,
                "high_or_mixed_density_lesion_volume_ml": 30,
                "mass_lesion_evacuated": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "class")
        self.assertIn("non-evacuated mass lesion", result.interpretation)

    def test_marshall_ct_classification_compressed_cisterns_without_shift_is_grade_three(self):
        result = marshall_ct_classification(
            metadata("Marshall CT颅脑损伤分类", "Marshall CT Classification"),
            {
                "visible_intracranial_pathology": True,
                "cisterns": "compressed",
                "midline_shift_mm": 4,
                "high_or_mixed_density_lesion_volume_ml": 0,
                "mass_lesion_evacuated": False,
            },
        )

        self.assertEqual(result.value, 3)
        self.assertIn("swelling", result.interpretation)

    def test_marshall_ct_classification_exact_shift_and_lesion_thresholds_remain_grade_two(self):
        result = marshall_ct_classification(
            metadata("Marshall CT颅脑损伤分类", "Marshall CT Classification"),
            {
                "visible_intracranial_pathology": True,
                "cisterns": "normal",
                "midline_shift_mm": 5,
                "high_or_mixed_density_lesion_volume_ml": 25,
                "mass_lesion_evacuated": False,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertIn("0-5 mm", result.interpretation)

    def test_rotterdam_ct_score_lowest_pattern_scores_one(self):
        result = rotterdam_ct_score(
            metadata("Rotterdam CT评分", "Rotterdam CT Score"),
            {
                "basal_cisterns": "normal",
                "midline_shift_mm": 0,
                "epidural_mass_lesion_present": True,
                "intraventricular_or_traumatic_sah": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "points")
        self.assertIn("lower", result.interpretation)

    def test_rotterdam_ct_score_highest_pattern_scores_six(self):
        result = rotterdam_ct_score(
            metadata("Rotterdam CT评分", "Rotterdam CT Score"),
            {
                "basal_cisterns": "absent",
                "midline_shift_mm": 6,
                "epidural_mass_lesion_present": False,
                "intraventricular_or_traumatic_sah": True,
            },
        )

        self.assertEqual(result.value, 6)
        self.assertIn("higher", result.interpretation)

    def test_rotterdam_ct_score_midline_shift_scores_only_when_greater_than_five_mm(self):
        at_threshold = rotterdam_ct_score(
            metadata("Rotterdam CT评分", "Rotterdam CT Score"),
            {
                "basal_cisterns": "normal",
                "midline_shift_mm": 5,
                "epidural_mass_lesion_present": True,
                "intraventricular_or_traumatic_sah": False,
            },
        )
        above_threshold = rotterdam_ct_score(
            metadata("Rotterdam CT评分", "Rotterdam CT Score"),
            {
                "basal_cisterns": "normal",
                "midline_shift_mm": 5.1,
                "epidural_mass_lesion_present": True,
                "intraventricular_or_traumatic_sah": False,
            },
        )

        self.assertEqual(at_threshold.value, 1)
        self.assertEqual(above_threshold.value, 2)

    def test_rotterdam_ct_score_rejects_negative_midline_shift(self):
        with self.assertRaises(ValueError):
            rotterdam_ct_score(
                metadata("Rotterdam CT评分", "Rotterdam CT Score"),
                {
                    "basal_cisterns": "normal",
                    "midline_shift_mm": -1,
                    "epidural_mass_lesion_present": True,
                    "intraventricular_or_traumatic_sah": False,
                },
            )


if __name__ == "__main__":
    unittest.main()
