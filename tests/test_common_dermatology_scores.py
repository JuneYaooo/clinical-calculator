import unittest

from clinical_calculators.calculators.common.dermatology_scores import (
    abcde_melanoma_warning_rule,
    dermatology_life_quality_index,
    eczema_area_severity_index,
    global_acne_grading_system,
    hidradenitis_suppurativa_hurley_stage,
    investigator_global_assessment_rosacea,
    modified_rodnan_skin_score,
    nail_psoriasis_severity_index,
    psoriasis_area_severity_index,
    severity_of_alopecia_tool,
    scorad_atopic_dermatitis,
    urticaria_activity_score_7,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="dermatology",
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


def pasi_region(erythema: int, induration: int, scaling: int, area: int) -> dict[str, int]:
    return {
        "erythema": erythema,
        "induration": induration,
        "scaling": scaling,
        "area": area,
    }


def easi_region(erythema: int, edema: int, excoriation: int, lichenification: int, area: int) -> dict[str, int]:
    return {
        "erythema": erythema,
        "edema": edema,
        "excoriation": excoriation,
        "lichenification": lichenification,
        "area": area,
    }


class CommonDermatologyScoresTest(unittest.TestCase):
    def test_pasi_all_regions_max_scores_seventy_two_and_severe(self):
        calculation = psoriasis_area_severity_index(
            metadata("银屑病面积与严重度指数", "Psoriasis Area and Severity Index"),
            {
                "head": pasi_region(4, 4, 4, 6),
                "upper_limbs": pasi_region(4, 4, 4, 6),
                "trunk": pasi_region(4, 4, 4, 6),
                "lower_limbs": pasi_region(4, 4, 4, 6),
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 72)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_pasi_all_regions_zero_scores_zero_and_mild(self):
        calculation = psoriasis_area_severity_index(
            metadata("银屑病面积与严重度指数", "Psoriasis Area and Severity Index"),
            {
                "head": pasi_region(0, 0, 0, 0),
                "upper_limbs": pasi_region(0, 0, 0, 0),
                "trunk": pasi_region(0, 0, 0, 0),
                "lower_limbs": pasi_region(0, 0, 0, 0),
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("mild", calculation.interpretation)

    def test_easi_all_regions_max_scores_seventy_two(self):
        calculation = eczema_area_severity_index(
            metadata("湿疹面积与严重度指数", "Eczema Area and Severity Index"),
            {
                "head_neck": easi_region(3, 3, 3, 3, 6),
                "upper_limbs": easi_region(3, 3, 3, 3, 6),
                "trunk": easi_region(3, 3, 3, 3, 6),
                "lower_limbs": easi_region(3, 3, 3, 3, 6),
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 72)
        self.assertEqual(calculation.unit, "points")

    def test_scorad_uses_extent_intensity_and_subjective_symptoms(self):
        calculation = scorad_atopic_dermatitis(
            metadata("特应性皮炎SCORAD评分", "SCORing Atopic Dermatitis"),
            {
                "extent_percent": 40,
                "intensity_scores": [2, 2, 1, 1, 2, 1],
                "pruritus_vas": 6,
                "sleep_loss_vas": 4,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 49.5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_dlqi_all_items_three_scores_thirty_and_extremely_large_effect(self):
        calculation = dermatology_life_quality_index(
            metadata("皮肤病生活质量指数", "Dermatology Life Quality Index"),
            {"items": [3] * 10},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 30)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("extremely large effect", calculation.interpretation)

    def test_dlqi_all_items_zero_scores_zero_and_no_effect(self):
        calculation = dermatology_life_quality_index(
            metadata("皮肤病生活质量指数", "Dermatology Life Quality Index"),
            {"items": [0] * 10},
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("no effect", calculation.interpretation)

    def test_salt_weights_four_scalp_regions_by_area_percent(self):
        calculation = severity_of_alopecia_tool(
            metadata("脱发严重度工具", "Severity of Alopecia Tool"),
            {
                "vertex_percent_loss": 50,
                "right_profile_percent_loss": 25,
                "left_profile_percent_loss": 25,
                "posterior_percent_loss": 10,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 31.4)
        self.assertEqual(calculation.unit, "percent")
        self.assertIn("SALT", calculation.interpretation)

    def test_salt_rejects_region_percent_over_one_hundred(self):
        with self.assertRaises(ValueError):
            severity_of_alopecia_tool(
                metadata("脱发严重度工具", "Severity of Alopecia Tool"),
                {
                    "vertex_percent_loss": 101,
                    "right_profile_percent_loss": 0,
                    "left_profile_percent_loss": 0,
                    "posterior_percent_loss": 0,
                },
            )

    def test_modified_rodnan_skin_score_sums_seventeen_site_scores(self):
        calculation = modified_rodnan_skin_score(
            metadata("改良Rodnan皮肤评分", "Modified Rodnan Skin Score"),
            {"site_scores": [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3]},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 27)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("17 skin sites", calculation.interpretation)

    def test_global_acne_grading_system_weights_regional_grades(self):
        calculation = global_acne_grading_system(
            metadata("全球痤疮分级系统", "Global Acne Grading System"),
            {
                "forehead": 3,
                "right_cheek": 2,
                "left_cheek": 2,
                "nose": 1,
                "chin": 1,
                "chest_upper_back": 4,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 28)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_nail_psoriasis_severity_index_sums_matrix_and_bed_scores(self):
        calculation = nail_psoriasis_severity_index(
            metadata("指甲银屑病严重度指数", "Nail Psoriasis Severity Index"),
            {
                "matrix_scores": [4, 3, 2, 1, 0, 4, 3, 2, 1, 0],
                "bed_scores": [0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 40)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("10 nails", calculation.interpretation)

    def test_urticaria_activity_score_7_sums_daily_wheal_and_pruritus_scores(self):
        calculation = urticaria_activity_score_7(
            metadata("荨麻疹活动度7日评分", "Urticaria Activity Score 7"),
            {
                "daily_wheal_scores": [3, 2, 2, 1, 0, 3, 2],
                "daily_pruritus_scores": [3, 3, 2, 2, 1, 3, 3],
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 30)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_abcde_melanoma_warning_rule_counts_positive_warning_signs(self):
        calculation = abcde_melanoma_warning_rule(
            metadata("ABCDE黑色素瘤警示规则", "ABCDE Rule for Melanoma"),
            {
                "asymmetry": True,
                "border_irregularity": True,
                "color_variation": False,
                "diameter_over_6_mm": True,
                "evolving": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["warning_sign_count"], 4)
        self.assertTrue(calculation.value["any_warning_sign"])
        self.assertIn("ABCDE", calculation.interpretation)

    def test_hurley_stage_returns_coded_stage_and_description(self):
        calculation = hidradenitis_suppurativa_hurley_stage(
            metadata("化脓性汗腺炎Hurley分期", "Hurley Staging for Hidradenitis Suppurativa"),
            {"stage": 2},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 2)
        self.assertEqual(calculation.unit, "stage")
        self.assertIn("recurrent abscess", calculation.interpretation)

    def test_hurley_stage_rejects_out_of_range_stage(self):
        with self.assertRaises(ValueError):
            hidradenitis_suppurativa_hurley_stage(
                metadata("化脓性汗腺炎Hurley分期", "Hurley Staging for Hidradenitis Suppurativa"),
                {"stage": 4},
            )

    def test_investigator_global_assessment_rosacea_returns_coded_grade_label(self):
        calculation = investigator_global_assessment_rosacea(
            metadata("研究者总体评估玫瑰痤疮", "Investigator Global Assessment for Rosacea"),
            {"grade": 1},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], 1)
        self.assertEqual(calculation.value["label"], "almost clear")
        self.assertTrue(calculation.value["clear_or_almost_clear"])
        self.assertEqual(calculation.unit, "IGA grade")

    def test_investigator_global_assessment_rosacea_rejects_out_of_range_grade(self):
        with self.assertRaises(ValueError):
            investigator_global_assessment_rosacea(
                metadata("研究者总体评估玫瑰痤疮", "Investigator Global Assessment for Rosacea"),
                {"grade": 5},
            )

    def test_pasi_rejects_missing_region_key(self):
        with self.assertRaises(KeyError):
            psoriasis_area_severity_index(
                metadata("银屑病面积与严重度指数", "Psoriasis Area and Severity Index"),
                {
                    "head": pasi_region(0, 0, 0, 0),
                    "upper_limbs": pasi_region(0, 0, 0, 0),
                    "trunk": pasi_region(0, 0, 0, 0),
                },
            )

    def test_easi_rejects_severity_score_outside_range(self):
        with self.assertRaises(ValueError):
            eczema_area_severity_index(
                metadata("湿疹面积与严重度指数", "Eczema Area and Severity Index"),
                {
                    "head_neck": easi_region(4, 3, 3, 3, 6),
                    "upper_limbs": easi_region(3, 3, 3, 3, 6),
                    "trunk": easi_region(3, 3, 3, 3, 6),
                    "lower_limbs": easi_region(3, 3, 3, 3, 6),
                },
            )

    def test_dlqi_rejects_wrong_item_count(self):
        with self.assertRaises(ValueError):
            dermatology_life_quality_index(
                metadata("皮肤病生活质量指数", "Dermatology Life Quality Index"),
                {"items": [0] * 9},
            )


if __name__ == "__main__":
    unittest.main()
