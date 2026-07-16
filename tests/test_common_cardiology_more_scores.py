import unittest

from clinical_calculators.calculators.common.cardiology_more_scores import (
    brugada_criteria_wide_complex_tachycardia,
    esc_ers_pah_four_strata_risk_assessment,
    hfa_peff_score,
    heart_score,
    heart_pathway_low_risk_chest_pain_rule,
    modified_sgarbossa_criteria_lbbb,
    reveal_2_0_risk_score,
    romhilt_estes_lvh_score,
    vereckei_avr_algorithm,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
        category="common",
        subspecialty="cardiology",
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


class CommonCardiologyMoreScoresTest(unittest.TestCase):
    def test_heart_age44_no_risks_normal_troponin_scores_low_risk(self):
        calculation = heart_score(
            metadata("HEART胸痛评分", "HEART Score for Chest Pain"),
            {
                "history": 0,
                "ecg": 0,
                "age_years": 44,
                "risk_factors_count": 0,
                "known_atherosclerotic_disease": False,
                "troponin_multiple_of_normal_limit": 1,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("low risk", calculation.interpretation)

    def test_heart_known_atherosclerotic_disease_overrides_risk_count_and_scores_high(self):
        calculation = heart_score(
            metadata("HEART胸痛评分", "HEART Score for Chest Pain"),
            {
                "history": 2,
                "ecg": 2,
                "age_years": 65,
                "risk_factors_count": 1,
                "known_atherosclerotic_disease": True,
                "troponin_multiple_of_normal_limit": 3.1,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high risk", calculation.interpretation)

    def test_heart_intermediate_age_and_troponin_scores_moderate(self):
        calculation = heart_score(
            metadata("HEART胸痛评分", "HEART Score for Chest Pain"),
            {
                "history": 1,
                "ecg": 1,
                "age_years": 50,
                "risk_factors_count": 2,
                "known_atherosclerotic_disease": 0,
                "troponin_multiple_of_normal_limit": 2.5,
            },
        )

        self.assertEqual(calculation.value, 5)
        self.assertIn("moderate risk", calculation.interpretation)

    def test_heart_rejects_invalid_coded_history(self):
        with self.assertRaises(ValueError):
            heart_score(
                metadata("HEART胸痛评分", "HEART Score for Chest Pain"),
                {
                    "history": 3,
                    "ecg": 0,
                    "age_years": 44,
                    "risk_factors_count": 0,
                    "known_atherosclerotic_disease": False,
                    "troponin_multiple_of_normal_limit": 1,
                },
            )

    def test_romhilt_estes_all_positive_without_digitalis_scores_thirteen_definite(self):
        calculation = romhilt_estes_lvh_score(
            metadata(
                "Romhilt-Estes诊断左心室肥厚的标准",
                "Romhilt-Estes Criteria for Left Ventricular Hypertrophy",
            ),
            {
                "voltage_criteria": True,
                "st_t_abnormality_without_digitalis": True,
                "st_t_abnormality_with_digitalis": False,
                "left_atrial_enlargement": True,
                "left_axis_deviation": True,
                "qrs_duration_ms": 90,
                "intrinsicoid_deflection_ms": 50,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 13)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("definite LVH", calculation.interpretation)

    def test_romhilt_estes_digitalis_st_t_uses_one_point_and_scores_definite(self):
        calculation = romhilt_estes_lvh_score(
            metadata(
                "Romhilt-Estes诊断左心室肥厚的标准",
                "Romhilt-Estes Criteria for Left Ventricular Hypertrophy",
            ),
            {
                "voltage_criteria": True,
                "st_t_abnormality_without_digitalis": False,
                "st_t_abnormality_with_digitalis": True,
                "left_atrial_enlargement": False,
                "left_axis_deviation": False,
                "qrs_duration_ms": 90,
                "intrinsicoid_deflection_ms": 40,
            },
        )

        self.assertEqual(calculation.value, 5)
        self.assertIn("definite LVH", calculation.interpretation)

    def test_romhilt_estes_four_points_is_probable(self):
        calculation = romhilt_estes_lvh_score(
            metadata(
                "Romhilt-Estes诊断左心室肥厚的标准",
                "Romhilt-Estes Criteria for Left Ventricular Hypertrophy",
            ),
            {
                "voltage_criteria": True,
                "st_t_abnormality_without_digitalis": False,
                "st_t_abnormality_with_digitalis": True,
                "left_atrial_enlargement": False,
                "left_axis_deviation": False,
                "qrs_duration_ms": 80,
                "intrinsicoid_deflection_ms": 40,
            },
        )

        self.assertEqual(calculation.value, 4)
        self.assertIn("probable LVH", calculation.interpretation)

    def test_romhilt_estes_three_points_is_not_diagnostic(self):
        calculation = romhilt_estes_lvh_score(
            metadata(
                "Romhilt-Estes诊断左心室肥厚的标准",
                "Romhilt-Estes Criteria for Left Ventricular Hypertrophy",
            ),
            {
                "voltage_criteria": True,
                "st_t_abnormality_without_digitalis": False,
                "st_t_abnormality_with_digitalis": False,
                "left_atrial_enlargement": False,
                "left_axis_deviation": False,
                "qrs_duration_ms": 80,
                "intrinsicoid_deflection_ms": 40,
            },
        )

        self.assertEqual(calculation.value, 3)
        self.assertIn("not diagnostic", calculation.interpretation)

    def test_modified_sgarbossa_counts_all_three_positive_criteria(self):
        calculation = modified_sgarbossa_criteria_lbbb(
            metadata("MILBBB胸痛鉴别", "Modified Sgarbossa Criteria for MI in LBBB"),
            {
                "concordant_st_elevation_mm": 1,
                "concordant_st_depression_v1_v3_mm": 1,
                "discordant_st_elevation_mm": 5,
                "preceding_s_wave_depth_mm": 20,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 3)
        self.assertEqual(calculation.unit, "criteria")
        self.assertIn("positive", calculation.interpretation)

    def test_modified_sgarbossa_accepts_signed_negative_discordant_elevation(self):
        calculation = modified_sgarbossa_criteria_lbbb(
            metadata("MILBBB胸痛鉴别", "Modified Sgarbossa Criteria for MI in LBBB"),
            {
                "concordant_st_elevation_mm": 0,
                "concordant_st_depression_v1_v3_mm": 0,
                "discordant_st_elevation_mm": -3,
                "preceding_s_wave_depth_mm": 12,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("positive", calculation.interpretation)

    def test_modified_sgarbossa_no_positive_criteria(self):
        calculation = modified_sgarbossa_criteria_lbbb(
            metadata("MILBBB胸痛鉴别", "Modified Sgarbossa Criteria for MI in LBBB"),
            {
                "concordant_st_elevation_mm": 0.5,
                "concordant_st_depression_v1_v3_mm": 0.5,
                "discordant_st_elevation_mm": 2,
                "preceding_s_wave_depth_mm": 10,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("negative", calculation.interpretation)

    def test_heart_pathway_low_risk_requires_low_heart_and_negative_serial_troponins(self):
        calculation = heart_pathway_low_risk_chest_pain_rule(
            metadata("HEART路径低危胸痛判定", "HEART Pathway"),
            {
                "history": 0,
                "ecg": 0,
                "age_years": 44,
                "risk_factors_count": 0,
                "known_atherosclerotic_disease": False,
                "troponin_multiple_of_normal_limit": 1,
                "troponin_0h_positive": False,
                "troponin_3h_positive": False,
                "new_ischemic_ecg_changes": False,
                "known_coronary_artery_disease": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 1)
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("low risk", calculation.interpretation)
        self.assertIn("HEART score 0", calculation.interpretation)

    def test_heart_pathway_positive_three_hour_troponin_is_not_low_risk(self):
        calculation = heart_pathway_low_risk_chest_pain_rule(
            metadata("HEART路径低危胸痛判定", "HEART Pathway"),
            {
                "history": 0,
                "ecg": 0,
                "age_years": 44,
                "risk_factors_count": 0,
                "known_atherosclerotic_disease": False,
                "troponin_multiple_of_normal_limit": 1,
                "troponin_0h_positive": False,
                "troponin_3h_positive": True,
                "new_ischemic_ecg_changes": False,
                "known_coronary_artery_disease": False,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("not low risk", calculation.interpretation)

    def test_reveal_2_0_best_values_scores_zero_low_risk(self):
        calculation = reveal_2_0_risk_score(
            metadata("REVEAL 2.0肺动脉高压风险评分", "REVEAL 2.0 Risk Score"),
            {
                "egfr_ml_min_1_73m2": 90,
                "who_functional_class": 1,
                "systolic_bp": 120,
                "heart_rate": 80,
                "six_minute_walk_distance_m": 450,
                "bnp_pg_ml": 40,
                "etiology": "other",
                "sex": "female",
                "age_years": 50,
                "hospitalization_within_6_months": False,
                "pericardial_effusion": False,
                "dlco_percent_predicted": 45,
                "mean_right_atrial_pressure_mm_hg": 10,
                "pvr_wood_units": 4,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("low risk", calculation.interpretation)

    def test_reveal_2_0_high_risk_features_scores_twenty_three(self):
        calculation = reveal_2_0_risk_score(
            metadata("REVEAL 2.0肺动脉高压风险评分", "REVEAL 2.0 Risk Score"),
            {
                "egfr_ml_min_1_73m2": 45,
                "who_functional_class": 4,
                "systolic_bp": 100,
                "heart_rate": 100,
                "six_minute_walk_distance_m": 100,
                "nt_probnp_pg_ml": 1200,
                "etiology": "pop_h",
                "sex": "male",
                "age_years": 70,
                "hospitalization_within_6_months": True,
                "pericardial_effusion": True,
                "dlco_percent_predicted": 35,
                "mean_right_atrial_pressure_mm_hg": 21,
                "pvr_wood_units": 5,
            },
        )

        self.assertEqual(calculation.value, 23)
        self.assertIn("high risk", calculation.interpretation)

    def test_esc_ers_pah_four_strata_averages_three_follow_up_parameters(self):
        calculation = esc_ers_pah_four_strata_risk_assessment(
            metadata(
                "ESC/ERS肺高压四层风险评估",
                "ESC/ERS PAH Four-Strata Risk Assessment",
            ),
            {
                "who_functional_class": 3,
                "six_minute_walk_distance_m": 300,
                "nt_probnp_pg_ml": 700,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 3)
        self.assertEqual(calculation.unit, "mean points")
        self.assertIn("intermediate-high risk", calculation.interpretation)

    def test_esc_ers_pah_four_strata_low_risk_boundaries(self):
        calculation = esc_ers_pah_four_strata_risk_assessment(
            metadata(
                "ESC/ERS肺高压四层风险评估",
                "ESC/ERS PAH Four-Strata Risk Assessment",
            ),
            {
                "who_functional_class": 2,
                "six_minute_walk_distance_m": 441,
                "bnp_pg_ml": 49,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("low risk", calculation.interpretation)

    def test_hfa_peff_score_sums_capped_domains_and_rules_in_hfpef(self):
        calculation = hfa_peff_score(
            metadata("HFA-PEFF评分", "HFA-PEFF Score"),
            {
                "functional_domain_points": 2,
                "morphological_domain_points": 1,
                "biomarker_domain_points": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("diagnostic", calculation.interpretation)

    def test_hfa_peff_score_intermediate_range_needs_functional_testing(self):
        calculation = hfa_peff_score(
            metadata("HFA-PEFF评分", "HFA-PEFF Score"),
            {
                "functional_domain_points": 1,
                "morphological_domain_points": 1,
                "biomarker_domain_points": 0,
            },
        )

        self.assertEqual(calculation.value, 2)
        self.assertIn("intermediate", calculation.interpretation)

    def test_brugada_first_positive_step_diagnoses_vt(self):
        calculation = brugada_criteria_wide_complex_tachycardia(
            metadata("Brugada室速鉴别算法", "Brugada Criteria for Wide Complex Tachycardia"),
            {
                "rs_complex_absent_all_precordial_leads": True,
                "longest_rs_interval_ms": 80,
                "av_dissociation": False,
                "vt_morphology_criteria_present": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 1)
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("VT", calculation.interpretation)
        self.assertIn("step 1", calculation.interpretation)

    def test_brugada_no_positive_steps_supports_svt_with_aberrancy(self):
        calculation = brugada_criteria_wide_complex_tachycardia(
            metadata("Brugada室速鉴别算法", "Brugada Criteria for Wide Complex Tachycardia"),
            {
                "rs_complex_absent_all_precordial_leads": False,
                "longest_rs_interval_ms": 100,
                "av_dissociation": False,
                "vt_morphology_criteria_present": False,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("SVT with aberrancy", calculation.interpretation)

    def test_vereckei_avr_initial_r_wave_diagnoses_vt(self):
        calculation = vereckei_avr_algorithm(
            metadata("Vereckei aVR室速算法", "Vereckei aVR Algorithm"),
            {
                "initial_r_wave_present": True,
                "initial_r_or_q_duration_ms": 20,
                "notching_initial_downstroke": False,
                "initial_to_terminal_activation_velocity_ratio": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 1)
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("VT", calculation.interpretation)
        self.assertIn("step 1", calculation.interpretation)

    def test_vereckei_avr_ratio_greater_than_one_supports_svt_with_aberrancy(self):
        calculation = vereckei_avr_algorithm(
            metadata("Vereckei aVR室速算法", "Vereckei aVR Algorithm"),
            {
                "initial_r_wave_present": False,
                "initial_r_or_q_duration_ms": 40,
                "notching_initial_downstroke": False,
                "initial_to_terminal_activation_velocity_ratio": 1.1,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("SVT with aberrancy", calculation.interpretation)


if __name__ == "__main__":
    unittest.main()
