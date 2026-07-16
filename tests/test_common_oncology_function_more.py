import unittest

from clinical_calculators.calculators.common.oncology_function_more import (
    ecog_performance_status,
    genant_semiquantitative_vertebral_fracture_grade,
    gleason_grade_group,
    imdc_risk_model_renal_cell_carcinoma,
    irecist_response,
    karnofsky_performance_status,
    lansky_play_performance_scale,
    palliative_performance_scale,
    palliative_prognostic_index,
    palliative_prognostic_score_pap,
    radiation_pneumonitis_dose_constraint_support,
    recist_1_1_response,
    van_nuys_prognostic_index,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="oncology_function_more",
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


class CommonOncologyFunctionMoreTest(unittest.TestCase):
    def test_ecog_grade_zero_is_fully_active(self):
        result = ecog_performance_status(
            metadata("ECOG体能状态评分", "ECOG Performance Status"),
            {"grade": 0},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "grade")
        self.assertIn("fully active", result.interpretation)

    def test_ecog_grade_five_is_dead(self):
        result = ecog_performance_status(
            metadata("ECOG体能状态评分", "ECOG Performance Status"),
            {"grade": 5},
        )

        self.assertEqual(result.value, 5)
        self.assertIn("dead", result.interpretation)

    def test_ecog_rejects_grade_outside_zero_to_five(self):
        with self.assertRaises(ValueError):
            ecog_performance_status(
                metadata("ECOG体能状态评分", "ECOG Performance Status"),
                {"grade": 6},
            )

    def test_karnofsky_score_seventy_returns_self_care_label(self):
        result = karnofsky_performance_status(
            metadata("Karnofsky体能状态评分", "Karnofsky Performance Status"),
            {"score": 70},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 70)
        self.assertEqual(result.unit, "points")
        self.assertIn("cares for self", result.interpretation)
        self.assertIn("unable normal activity/work", result.interpretation)

    def test_karnofsky_rejects_non_multiple_of_ten(self):
        with self.assertRaises(ValueError):
            karnofsky_performance_status(
                metadata("Karnofsky体能状态评分", "Karnofsky Performance Status"),
                {"score": 75},
            )

    def test_palliative_performance_scale_accepts_ten_point_increments(self):
        result = palliative_performance_scale(
            metadata("姑息体能状态量表", "Palliative Performance Scale"),
            {"score": 40},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 40)
        self.assertEqual(result.unit, "points")
        self.assertIn("mainly in bed", result.interpretation)

    def test_lansky_play_performance_scale_accepts_ten_point_increments(self):
        result = lansky_play_performance_scale(
            metadata("Lansky儿童体能状态评分", "Lansky Play-Performance Scale"),
            {"score": 80},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 80)
        self.assertEqual(result.unit, "points")
        self.assertIn("active", result.interpretation)

    def test_imdc_zero_risk_factors_is_favorable(self):
        result = imdc_risk_model_renal_cell_carcinoma(
            metadata("肾癌IMDC风险模型", "IMDC Risk Model for Renal Cell Carcinoma"),
            {
                "karnofsky_less_80": False,
                "time_from_diagnosis_to_treatment_less_1_year": False,
                "hemoglobin_below_lln": False,
                "corrected_calcium_above_uln": False,
                "neutrophils_above_uln": False,
                "platelets_above_uln": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "risk factors")
        self.assertIn("favorable", result.interpretation)

    def test_imdc_two_risk_factors_is_intermediate(self):
        result = imdc_risk_model_renal_cell_carcinoma(
            metadata("肾癌IMDC风险模型", "IMDC Risk Model for Renal Cell Carcinoma"),
            {
                "karnofsky_less_80": True,
                "time_from_diagnosis_to_treatment_less_1_year": True,
                "hemoglobin_below_lln": False,
                "corrected_calcium_above_uln": False,
                "neutrophils_above_uln": False,
                "platelets_above_uln": False,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertIn("intermediate", result.interpretation)

    def test_imdc_three_risk_factors_is_poor(self):
        result = imdc_risk_model_renal_cell_carcinoma(
            metadata("肾癌IMDC风险模型", "IMDC Risk Model for Renal Cell Carcinoma"),
            {
                "karnofsky_less_80": True,
                "time_from_diagnosis_to_treatment_less_1_year": True,
                "hemoglobin_below_lln": True,
                "corrected_calcium_above_uln": False,
                "neutrophils_above_uln": False,
                "platelets_above_uln": False,
            },
        )

        self.assertEqual(result.value, 3)
        self.assertIn("poor", result.interpretation)

    def test_imdc_rejects_non_boolean_factor(self):
        with self.assertRaises(ValueError):
            imdc_risk_model_renal_cell_carcinoma(
                metadata("肾癌IMDC风险模型", "IMDC Risk Model for Renal Cell Carcinoma"),
                {
                    "karnofsky_less_80": 1,
                    "time_from_diagnosis_to_treatment_less_1_year": False,
                    "hemoglobin_below_lln": False,
                    "corrected_calcium_above_uln": False,
                    "neutrophils_above_uln": False,
                    "platelets_above_uln": False,
                },
            )

    def test_gleason_three_plus_three_is_grade_group_one(self):
        result = gleason_grade_group(
            metadata("Gleason分级组", "Gleason Grade Group"),
            {"primary_pattern": 3, "secondary_pattern": 3},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "grade group")
        self.assertIn("Gleason score 6", result.interpretation)
        self.assertIn("grade group 1", result.interpretation)

    def test_gleason_three_plus_four_is_grade_group_two(self):
        result = gleason_grade_group(
            metadata("Gleason分级组", "Gleason Grade Group"),
            {"primary_pattern": 3, "secondary_pattern": 4},
        )

        self.assertEqual(result.value, 2)
        self.assertIn("Gleason score 7", result.interpretation)

    def test_gleason_four_plus_three_is_grade_group_three(self):
        result = gleason_grade_group(
            metadata("Gleason分级组", "Gleason Grade Group"),
            {"primary_pattern": 4, "secondary_pattern": 3},
        )

        self.assertEqual(result.value, 3)
        self.assertIn("Gleason score 7", result.interpretation)

    def test_gleason_four_plus_four_is_grade_group_four(self):
        result = gleason_grade_group(
            metadata("Gleason分级组", "Gleason Grade Group"),
            {"primary_pattern": 4, "secondary_pattern": 4},
        )

        self.assertEqual(result.value, 4)
        self.assertIn("Gleason score 8", result.interpretation)

    def test_gleason_five_plus_five_is_grade_group_five(self):
        result = gleason_grade_group(
            metadata("Gleason分级组", "Gleason Grade Group"),
            {"primary_pattern": 5, "secondary_pattern": 5},
        )

        self.assertEqual(result.value, 5)
        self.assertIn("Gleason score 10", result.interpretation)

    def test_gleason_rejects_unsupported_low_pattern_combination(self):
        with self.assertRaises(ValueError):
            gleason_grade_group(
                metadata("Gleason分级组", "Gleason Grade Group"),
                {"primary_pattern": 2, "secondary_pattern": 4},
            )

    def test_gleason_rejects_pattern_outside_one_to_five(self):
        with self.assertRaises(ValueError):
            gleason_grade_group(
                metadata("Gleason分级组", "Gleason Grade Group"),
                {"primary_pattern": 6, "secondary_pattern": 3},
            )

    def test_genant_grade_two_for_thirty_percent_vertebral_height_loss(self):
        result = genant_semiquantitative_vertebral_fracture_grade(
            metadata("椎体骨折Genant半定量分级", "Genant Semiquantitative Vertebral Fracture Grade"),
            {"height_loss_percent": 30},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 2)
        self.assertEqual(result.unit, "grade")
        self.assertIn("moderate", result.interpretation)

    def test_genant_rejects_negative_height_loss(self):
        with self.assertRaises(ValueError):
            genant_semiquantitative_vertebral_fracture_grade(
                metadata("椎体骨折Genant半定量分级", "Genant Semiquantitative Vertebral Fracture Grade"),
                {"height_loss_percent": -1},
            )

    def test_recist_partial_response_requires_at_least_30_percent_decrease(self):
        result = recist_1_1_response(
            metadata("RECIST 1.1实体瘤疗效评价", "RECIST 1.1"),
            {
                "baseline_sum_mm": 100,
                "current_sum_mm": 65,
                "nadir_sum_mm": 65,
                "target_lesions_absent": False,
                "new_lesions": False,
                "non_target_progressive_disease": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "PR")
        self.assertEqual(result.unit, "response")
        self.assertIn("partial response", result.interpretation)

    def test_recist_progressive_disease_requires_20_percent_and_5_mm_from_nadir(self):
        result = recist_1_1_response(
            metadata("RECIST 1.1实体瘤疗效评价", "RECIST 1.1"),
            {
                "baseline_sum_mm": 100,
                "current_sum_mm": 126,
                "nadir_sum_mm": 100,
                "target_lesions_absent": False,
                "new_lesions": False,
                "non_target_progressive_disease": False,
            },
        )

        self.assertEqual(result.value, "PD")
        self.assertIn("progressive disease", result.interpretation)

    def test_recist_new_lesion_overrides_target_partial_response(self):
        result = recist_1_1_response(
            metadata("RECIST 1.1实体瘤疗效评价", "RECIST 1.1"),
            {
                "baseline_sum_mm": 100,
                "current_sum_mm": 40,
                "nadir_sum_mm": 40,
                "target_lesions_absent": False,
                "new_lesions": True,
                "non_target_progressive_disease": False,
            },
        )

        self.assertEqual(result.value, "PD")
        self.assertIn("new lesions", result.interpretation)

    def test_irecist_first_progression_is_iupd(self):
        result = irecist_response(
            metadata("iRECIST免疫治疗疗效评价", "iRECIST"),
            {
                "target_response": "PR",
                "non_target_response": "non-CR/non-PD",
                "new_lesions": True,
                "prior_iupd": False,
                "progression_confirmed": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "iUPD")
        self.assertEqual(result.unit, "response")
        self.assertIn("unconfirmed progressive disease", result.interpretation)

    def test_irecist_confirmed_progression_after_iupd_is_icpd(self):
        result = irecist_response(
            metadata("iRECIST免疫治疗疗效评价", "iRECIST"),
            {
                "target_response": "PD",
                "non_target_response": "non-CR/non-PD",
                "new_lesions": False,
                "prior_iupd": True,
                "progression_confirmed": True,
            },
        )

        self.assertEqual(result.value, "iCPD")
        self.assertIn("confirmed progressive disease", result.interpretation)

    def test_pap_score_places_patient_in_group_c(self):
        result = palliative_prognostic_score_pap(
            metadata("姑息预后评分", "Palliative Prognostic Score, PaP"),
            {
                "dyspnea": True,
                "anorexia": True,
                "karnofsky_score": 30,
                "clinical_prediction_weeks": 2,
                "white_blood_cell_count_10e9_l": 12,
                "lymphocyte_percentage": 10,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 15.0)
        self.assertEqual(result.unit, "points")
        self.assertIn("group C", result.interpretation)

    def test_pap_clinical_prediction_seven_to_eight_weeks_scores_two_and_half(self):
        result = palliative_prognostic_score_pap(
            metadata("姑息预后评分", "Palliative Prognostic Score, PaP"),
            {
                "dyspnea": False,
                "anorexia": False,
                "karnofsky_score": 80,
                "clinical_prediction_weeks": 7,
                "white_blood_cell_count_10e9_l": 7,
                "lymphocyte_percentage": 25,
            },
        )

        self.assertEqual(result.value, 2.5)
        self.assertIn("group A", result.interpretation)

    def test_pap_rejects_karnofsky_not_in_pap_bands(self):
        with self.assertRaises(ValueError):
            palliative_prognostic_score_pap(
                metadata("姑息预后评分", "Palliative Prognostic Score, PaP"),
                {
                    "dyspnea": False,
                    "anorexia": False,
                    "karnofsky_score": 85,
                    "clinical_prediction_weeks": 20,
                    "white_blood_cell_count_10e9_l": 7,
                    "lymphocyte_percentage": 25,
                },
            )

    def test_palliative_prognostic_index_scores_high_risk_profile(self):
        result = palliative_prognostic_index(
            metadata("姑息预后指数", "Palliative Prognostic Index"),
            {
                "palliative_performance_scale": 30,
                "oral_intake": "mouthfuls_or_less",
                "edema": True,
                "dyspnea_at_rest": True,
                "delirium": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13.5)
        self.assertEqual(result.unit, "points")
        self.assertIn("greater than 6", result.interpretation)

    def test_radiation_pneumonitis_constraints_pass_when_mld_and_v20_under_quantitative_limits(self):
        result = radiation_pneumonitis_dose_constraint_support(
            metadata("放射性肺炎风险平均肺剂量约束", "Radiation Pneumonitis Dose Constraint Support"),
            {"mean_lung_dose_gy": 18, "v20_percent": 28},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "within_constraints")
        self.assertEqual(result.unit, "classification")
        self.assertIn("within", result.interpretation)

    def test_radiation_pneumonitis_constraints_flag_exceeded_v20(self):
        result = radiation_pneumonitis_dose_constraint_support(
            metadata("放射性肺炎风险平均肺剂量约束", "Radiation Pneumonitis Dose Constraint Support"),
            {"mean_lung_dose_gy": 18, "v20_percent": 36},
        )

        self.assertEqual(result.value, "constraints_exceeded")
        self.assertIn("V20", result.interpretation)

    def test_van_nuys_prognostic_index_scores_high_risk_dcis(self):
        result = van_nuys_prognostic_index(
            metadata("Van Nuys DCIS预后指数", "Van Nuys Prognostic Index"),
            {
                "tumor_size_mm": 45,
                "margin_width_mm": 0.5,
                "pathologic_classification": "high_grade",
                "age_years": 39,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_van_nuys_prognostic_index_scores_low_risk_dcis(self):
        result = van_nuys_prognostic_index(
            metadata("Van Nuys DCIS预后指数", "Van Nuys Prognostic Index"),
            {
                "tumor_size_mm": 10,
                "margin_width_mm": 10,
                "pathologic_classification": "low_or_intermediate_without_necrosis",
                "age_years": 65,
            },
        )

        self.assertEqual(result.value, 4)
        self.assertIn("low", result.interpretation)


if __name__ == "__main__":
    unittest.main()
