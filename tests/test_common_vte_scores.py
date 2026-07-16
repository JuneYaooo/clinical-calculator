import unittest

from clinical_calculators.calculators.common.vte_scores import (
    bova_score,
    dash_vte_recurrence_score,
    herdoo2_vte_recurrence_rule,
    improve_bleeding_risk_score,
    improve_vte_risk_score,
    khorana_cancer_vte_risk_score,
    riete_bleeding_score,
    vte_bleed_score,
    wells_dvt_score,
    wells_pe_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="vte",
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


class CommonVteScoresTest(unittest.TestCase):
    def test_wells_dvt_active_cancer_tenderness_and_swelling_is_likely(self):
        result = wells_dvt_score(
            metadata("深静脉血栓形成概率：Wells评分系统", "Wells Score for Deep Vein Thrombosis"),
            {
                "active_cancer": True,
                "paralysis_paresis_or_recent_cast": 0,
                "recent_bedridden_or_major_surgery": False,
                "localized_tenderness": 1,
                "entire_leg_swollen": True,
                "calf_swelling_3cm": 0,
                "pitting_edema": False,
                "collateral_superficial_veins": 0,
                "previous_dvt": False,
                "alternative_diagnosis_at_least_as_likely": 0,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("DVT likely", result.interpretation)

    def test_wells_dvt_alternative_diagnosis_only_is_unlikely(self):
        result = wells_dvt_score(
            metadata("深静脉血栓形成概率：Wells评分系统", "Wells Score for Deep Vein Thrombosis"),
            {
                "active_cancer": 0,
                "paralysis_paresis_or_recent_cast": 0,
                "recent_bedridden_or_major_surgery": 0,
                "localized_tenderness": 0,
                "entire_leg_swollen": 0,
                "calf_swelling_3cm": 0,
                "pitting_edema": 0,
                "collateral_superficial_veins": 0,
                "previous_dvt": 0,
                "alternative_diagnosis_at_least_as_likely": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, -2)
        self.assertEqual(result.unit, "points")
        self.assertIn("DVT unlikely", result.interpretation)

    def test_wells_pe_dvt_signs_most_likely_and_tachycardia_is_likely(self):
        result = wells_pe_score(
            metadata("肺栓塞可能性：Wells评分系统", "Wells Score for Pulmonary Embolism"),
            {
                "clinical_signs_dvt": True,
                "pe_most_likely": True,
                "heart_rate": 110,
                "immobilization_or_surgery": 0,
                "previous_dvt_pe": False,
                "hemoptysis": 0,
                "malignancy": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7.5)
        self.assertEqual(result.unit, "points")
        self.assertIn("PE likely", result.interpretation)

    def test_wells_pe_malignancy_only_with_normal_heart_rate_is_unlikely(self):
        result = wells_pe_score(
            metadata("肺栓塞可能性：Wells评分系统", "Wells Score for Pulmonary Embolism"),
            {
                "clinical_signs_dvt": 0,
                "pe_most_likely": 0,
                "heart_rate": 90,
                "immobilization_or_surgery": 0,
                "previous_dvt_pe": 0,
                "hemoptysis": 0,
                "malignancy": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "points")
        self.assertIn("PE unlikely", result.interpretation)

    def test_improve_vte_risk_score_high_risk(self):
        result = improve_vte_risk_score(
            metadata("IMPROVE住院VTE风险评分", "IMPROVE VTE Risk Score"),
            {
                "previous_vte": True,
                "known_thrombophilia": False,
                "lower_limb_paralysis": False,
                "current_cancer": True,
                "immobilized_7_days": False,
                "icu_or_ccu_stay": False,
                "age_years": 70,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_improve_vte_risk_score_low_risk(self):
        result = improve_vte_risk_score(
            metadata("IMPROVE住院VTE风险评分", "IMPROVE VTE Risk Score"),
            {
                "previous_vte": 0,
                "known_thrombophilia": 0,
                "lower_limb_paralysis": 0,
                "current_cancer": 0,
                "immobilized_7_days": 0,
                "icu_or_ccu_stay": 0,
                "age_years": 50,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("lower", result.interpretation)

    def test_improve_bleeding_risk_score_high_risk(self):
        result = improve_bleeding_risk_score(
            metadata("IMPROVE出血风险评分", "IMPROVE Bleeding Risk Score"),
            {
                "active_gastroduodenal_ulcer": True,
                "bleeding_within_3_months": False,
                "platelets_10e9_l": 45,
                "age_years": 86,
                "hepatic_failure_inr_gt_1_5": False,
                "gfr_ml_min": 45,
                "icu_or_ccu_stay": False,
                "central_venous_catheter": False,
                "rheumatic_disease": False,
                "current_cancer": False,
                "sex": "female",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_improve_bleeding_rejects_unknown_sex(self):
        with self.assertRaises(ValueError):
            improve_bleeding_risk_score(
                metadata("IMPROVE出血风险评分", "IMPROVE Bleeding Risk Score"),
                {
                    "active_gastroduodenal_ulcer": False,
                    "bleeding_within_3_months": False,
                    "platelets_10e9_l": 200,
                    "age_years": 50,
                    "hepatic_failure_inr_gt_1_5": False,
                    "gfr_ml_min": 90,
                    "icu_or_ccu_stay": False,
                    "central_venous_catheter": False,
                    "rheumatic_disease": False,
                    "current_cancer": False,
                    "sex": "unknown",
                },
            )

    def test_khorana_high_risk_pancreas_with_labs_scores_six(self):
        result = khorana_cancer_vte_risk_score(
            metadata("Khorana肿瘤相关VTE风险", "Khorana Score"),
            {
                "cancer_site": "very_high_risk",
                "platelets_10e9_l": 400,
                "hemoglobin_g_dl": 9.5,
                "using_esa": False,
                "wbc_10e9_l": 12,
                "bmi": 36,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_khorana_rejects_unknown_cancer_site_group(self):
        with self.assertRaises(ValueError):
            khorana_cancer_vte_risk_score(
                metadata("Khorana肿瘤相关VTE风险", "Khorana Score"),
                {
                    "cancer_site": "unknown",
                    "platelets_10e9_l": 200,
                    "hemoglobin_g_dl": 13,
                    "using_esa": False,
                    "wbc_10e9_l": 6,
                    "bmi": 24,
                },
            )

    def test_vte_bleed_all_positive_scores_nine_high_risk(self):
        result = vte_bleed_score(
            metadata("VTE-BLEED抗凝出血风险", "VTE-BLEED Score"),
            {
                "active_cancer": True,
                "male_with_uncontrolled_hypertension": True,
                "anemia": True,
                "history_of_bleeding": True,
                "age_years": 60,
                "renal_dysfunction": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 9)
        self.assertEqual(result.unit, "points")
        self.assertIn("high bleeding risk", result.interpretation)

    def test_bova_all_positive_scores_seven_stage_three(self):
        result = bova_score(
            metadata("BOVA肺栓塞并发症风险", "Bova Score"),
            {
                "systolic_bp": 95,
                "elevated_troponin": True,
                "right_ventricular_dysfunction": True,
                "heart_rate": 110,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "points")
        self.assertIn("stage III", result.interpretation)

    def test_bova_rejects_hemodynamically_unstable_systolic_bp(self):
        with self.assertRaises(ValueError):
            bova_score(
                metadata("BOVA肺栓塞并发症风险", "Bova Score"),
                {
                    "systolic_bp": 89,
                    "elevated_troponin": False,
                    "right_ventricular_dysfunction": False,
                    "heart_rate": 90,
                },
            )

    def test_riete_bleeding_score_high_risk_from_public_predictors(self):
        result = riete_bleeding_score(
            metadata("RIETE肺栓塞出血风险", "RIETE Bleeding Score"),
            {
                "recent_major_bleeding": True,
                "creatinine_abnormal": True,
                "anemia": True,
                "active_cancer": True,
                "clinically_overt_pulmonary_embolism": True,
                "age_years": 80,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_riete_bleeding_score_zero_is_low_risk(self):
        result = riete_bleeding_score(
            metadata("RIETE肺栓塞出血风险", "RIETE Bleeding Score"),
            {
                "recent_major_bleeding": False,
                "creatinine_abnormal": False,
                "anemia": False,
                "active_cancer": False,
                "clinically_overt_pulmonary_embolism": False,
                "age_years": 50,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low", result.interpretation)

    def test_dash_vte_recurrence_score_high_from_public_point_rule(self):
        result = dash_vte_recurrence_score(
            metadata("DASH停抗凝后VTE复发风险", "DASH Score"),
            {
                "abnormal_d_dimer_after_anticoagulation": True,
                "age_years": 45,
                "sex": "male",
                "hormone_associated_vte": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_dash_vte_recurrence_score_hormone_associated_vte_subtracts_two(self):
        result = dash_vte_recurrence_score(
            metadata("DASH停抗凝后VTE复发风险", "DASH Score"),
            {
                "abnormal_d_dimer_after_anticoagulation": False,
                "age_years": 55,
                "sex": "female",
                "hormone_associated_vte": True,
            },
        )

        self.assertEqual(result.value, -2)
        self.assertIn("low", result.interpretation)

    def test_herdoo2_female_with_two_criteria_is_high_risk(self):
        result = herdoo2_vte_recurrence_rule(
            metadata("HERDOO2停抗凝后VTE复发规则", "HERDOO2 Rule"),
            {
                "sex": "female",
                "leg_hyperpigmentation_edema_or_redness": True,
                "d_dimer_ug_l": 300,
                "bmi": 24,
                "age_years": 60,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 2)
        self.assertTrue(result.value["high_recurrence_risk"])
        self.assertIn("high", result.interpretation)

    def test_herdoo2_male_is_not_low_risk_by_rule(self):
        result = herdoo2_vte_recurrence_rule(
            metadata("HERDOO2停抗凝后VTE复发规则", "HERDOO2 Rule"),
            {
                "sex": "male",
                "leg_hyperpigmentation_edema_or_redness": False,
                "d_dimer_ug_l": 100,
                "bmi": 24,
                "age_years": 40,
            },
        )

        self.assertIsNone(result.value["score"])
        self.assertTrue(result.value["high_recurrence_risk"])
        self.assertIn("Men", result.interpretation)


if __name__ == "__main__":
    unittest.main()
