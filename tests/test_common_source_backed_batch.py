import unittest

from clinical_calculators.calculators.common.source_backed_batch import (
    chokai_ureteral_stone_score,
    dutch_lipid_clinic_network_score,
    eortc_2006_nmibc_risk_table,
    four_point_clock_drawing_test,
    fullpiers_48_hour_adverse_maternal_outcome_risk,
    garfield_af_integrated_risk_2017,
    hcm_risk_scd_2014_five_year_risk,
    guys_stone_score,
    hendrich_ii_fall_risk_model,
    isaric_4c_deterioration_probability,
    kidney_failure_risk_equation_4_variable,
    maggic_heart_failure_mortality_score,
    ohts_egps_five_year_poag_point_system,
    plcom2012_six_year_lung_cancer_risk,
    revised_risk_analysis_index_clinical,
    thoracoscore_in_hospital_mortality,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name}",
        category="test",
        subspecialty="",
        scenario="test",
        name_cn=name,
        name_en=name,
        inputs="test",
        output="test",
        formula="test",
        interpretation="test",
        purpose="test",
        source_type="test",
        source="test",
        source_url="https://example.com",
        channel="test",
        evidence_tier="A",
        commonness="test",
        coverage_note="test",
        clinical_note="test",
        version="test",
        entry_source="test",
        source_group="",
        notes="",
    )


def dlcn_inputs(**overrides):
    values = {
        "family_premature_chd_or_ldl_above_95th": False,
        "family_xanthoma_arcus_or_child_ldl_above_95th": False,
        "personal_premature_chd": False,
        "personal_premature_cerebral_or_peripheral_vascular_disease": False,
        "tendon_xanthoma": False,
        "corneal_arcus_under_45": False,
        "ldl_mg_dl": 100,
        "causative_ldlr_apob_pcsk9_mutation": False,
    }
    values.update(overrides)
    return values


class CommonSourceBackedBatchTest(unittest.TestCase):
    def test_garfield_af_centered_reference_case_reduces_to_zero_predictors(self):
        calculation = garfield_af_integrated_risk_2017(
            metadata("GARFIELD-AF"),
            {
                "age_years": 65,
                "weight_kg": 75,
                "pulse_bpm": 120,
                "diastolic_bp_mm_hg": 80,
                "race_ethnicity_garfield": "caucasian",
                "sex": "male",
                "history_bleeding": False,
                "history_heart_failure_or_lvef_below_40": False,
                "history_stroke": False,
                "moderate_severe_ckd": False,
                "history_coronary_or_peripheral_vascular_disease": False,
                "diabetes": False,
                "current_smoker": False,
                "dementia": False,
                "current_antiplatelet_drug": False,
                "carotid_occlusive_disease": False,
            },
        )

        self.assertEqual(
            calculation.value["linear_predictors"],
            {
                "mortality": 0.0,
                "ischemic_stroke_or_systemic_embolism": 0.0,
                "major_bleeding": 0.0,
            },
        )
        two_year = calculation.value["scenario_risk_percent"]["2_year"]
        self.assertEqual(two_year["mortality"]["no_oac"], 3.8)
        self.assertEqual(two_year["ischemic_stroke_or_systemic_embolism"]["no_oac"], 1.2)
        self.assertEqual(two_year["major_bleeding"]["no_oac"], 0.8)
        self.assertFalse(calculation.value["scenario_comparison_is_causal"])

    def test_garfield_af_matches_public_treatment_adjustments(self):
        calculation = garfield_af_integrated_risk_2017(
            metadata("GARFIELD-AF"),
            {
                "age_years": 80,
                "weight_kg": 60,
                "pulse_bpm": 90,
                "diastolic_bp_mm_hg": 70,
                "race_ethnicity_garfield": "asian",
                "sex": "female",
                "history_bleeding": True,
                "history_heart_failure_or_lvef_below_40": True,
                "history_stroke": True,
                "moderate_severe_ckd": True,
                "history_coronary_or_peripheral_vascular_disease": True,
                "diabetes": True,
                "current_smoker": True,
                "dementia": True,
                "current_antiplatelet_drug": True,
                "carotid_occlusive_disease": True,
            },
        )

        one_year = calculation.value["scenario_risk_percent"]["1_year"]
        self.assertEqual(one_year["mortality"], {"no_oac": 49.8, "vka": 43.6, "noac": 36.6})
        self.assertEqual(
            one_year["ischemic_stroke_or_systemic_embolism"],
            {"no_oac": 25.5, "vka": 18.7, "noac": 15.3},
        )
        self.assertEqual(one_year["major_bleeding"], {"no_oac": 7.7, "vka": 13.7, "noac": 9.7})

    def test_garfield_af_rejects_nonadult_use(self):
        with self.assertRaisesRegex(ValueError, "derived in adults"):
            garfield_af_integrated_risk_2017(
                metadata("GARFIELD-AF"),
                {
                    "age_years": 17,
                    "weight_kg": 75,
                    "pulse_bpm": 80,
                    "diastolic_bp_mm_hg": 80,
                    "race_ethnicity_garfield": "caucasian",
                    "sex": "male",
                    "history_bleeding": False,
                    "history_heart_failure_or_lvef_below_40": False,
                    "history_stroke": False,
                    "moderate_severe_ckd": False,
                    "history_coronary_or_peripheral_vascular_disease": False,
                    "diabetes": False,
                    "current_smoker": False,
                    "dementia": False,
                    "current_antiplatelet_drug": False,
                    "carotid_occlusive_disease": False,
                },
            )

    def test_hcm_risk_scd_reproduces_public_equation_low_risk_case(self):
        calculation = hcm_risk_scd_2014_five_year_risk(
            metadata("HCM Risk-SCD"),
            {
                "age_years": 50,
                "maximal_wall_thickness_mm": 15,
                "left_atrial_diameter_mm": 35,
                "maximal_lvot_gradient_mm_hg": 10,
                "family_history_sudden_cardiac_death": False,
                "nonsustained_ventricular_tachycardia": False,
                "unexplained_syncope": False,
            },
        )

        self.assertAlmostEqual(calculation.value["prognostic_index"], 1.78030205, places=8)
        self.assertEqual(calculation.value["risk_5_year_sudden_cardiac_death_percent"], 1.18)
        self.assertEqual(calculation.value["risk_band"], "below_4_percent")

    def test_hcm_risk_scd_reproduces_public_equation_high_risk_case(self):
        calculation = hcm_risk_scd_2014_five_year_risk(
            metadata("HCM Risk-SCD"),
            {
                "age_years": 30,
                "maximal_wall_thickness_mm": 30,
                "left_atrial_diameter_mm": 50,
                "maximal_lvot_gradient_mm_hg": 80,
                "family_history_sudden_cardiac_death": True,
                "nonsustained_ventricular_tachycardia": True,
                "unexplained_syncope": True,
            },
        )

        self.assertAlmostEqual(calculation.value["prognostic_index"], 5.24705676, places=8)
        self.assertEqual(calculation.value["risk_5_year_sudden_cardiac_death_percent"], 31.64)
        self.assertEqual(calculation.value["risk_band"], "at_least_6_percent")

    def test_hcm_risk_scd_rejects_extrapolation_outside_public_ranges(self):
        with self.assertRaisesRegex(ValueError, "10-35"):
            hcm_risk_scd_2014_five_year_risk(
                metadata("HCM Risk-SCD"),
                {
                    "age_years": 50,
                    "maximal_wall_thickness_mm": 36,
                    "left_atrial_diameter_mm": 35,
                    "maximal_lvot_gradient_mm_hg": 10,
                    "family_history_sudden_cardiac_death": False,
                    "nonsustained_ventricular_tachycardia": False,
                    "unexplained_syncope": False,
                },
            )

    def test_fullpiers_reproduces_published_equation_low_risk_case(self):
        calculation = fullpiers_48_hour_adverse_maternal_outcome_risk(
            metadata("fullPIERS"),
            {
                "gestational_age_weeks": 36,
                "has_chest_pain_or_dyspnea": False,
                "serum_creatinine_umol_l": 70,
                "platelets_10e9_l": 200,
                "ast_u_l": 30,
                "oxygen_saturation_percent": 97,
            },
        )

        self.assertAlmostEqual(calculation.value["linear_predictor"], -4.447745, places=6)
        self.assertAlmostEqual(calculation.value["risk_48_hour_percent"], 1.1570, places=4)
        self.assertEqual(calculation.value["risk_group"], "below_2_5_percent")

    def test_fullpiers_reproduces_published_equation_high_risk_case(self):
        calculation = fullpiers_48_hour_adverse_maternal_outcome_risk(
            metadata("fullPIERS"),
            {
                "gestational_age_weeks": 30,
                "has_chest_pain_or_dyspnea": True,
                "serum_creatinine_umol_l": 150,
                "platelets_10e9_l": 70,
                "ast_u_l": 200,
                "oxygen_saturation_percent": 92,
            },
        )

        self.assertAlmostEqual(calculation.value["linear_predictor"], -0.034, places=6)
        self.assertAlmostEqual(calculation.value["risk_48_hour_percent"], 49.1501, places=4)
        self.assertEqual(calculation.value["risk_group"], "at_least_30_percent")

    def test_fullpiers_rejects_use_before_twenty_weeks(self):
        with self.assertRaisesRegex(ValueError, "20-43"):
            fullpiers_48_hour_adverse_maternal_outcome_risk(
                metadata("fullPIERS"),
                {
                    "gestational_age_weeks": 19,
                    "has_chest_pain_or_dyspnea": False,
                    "serum_creatinine_umol_l": 70,
                    "platelets_10e9_l": 200,
                    "ast_u_l": 30,
                    "oxygen_saturation_percent": 97,
                },
            )

    def test_four_point_clock_drawing_screen(self):
        normal = four_point_clock_drawing_test(
            metadata("clock"),
            {
                "closed_circle": True,
                "numbers_in_correct_positions": True,
                "all_twelve_numbers_present": True,
                "hands_show_requested_time": True,
            },
        )
        abnormal = four_point_clock_drawing_test(
            metadata("clock"),
            {
                "closed_circle": True,
                "numbers_in_correct_positions": True,
                "all_twelve_numbers_present": True,
                "hands_show_requested_time": False,
            },
        )

        self.assertEqual(normal.value["score"], 4)
        self.assertEqual(normal.value["classification"], "normal screen")
        self.assertEqual(abnormal.value["score"], 3)
        self.assertEqual(abnormal.value["classification"], "abnormal screen")

    def test_dlcn_uses_highest_score_per_group_and_source_thresholds(self):
        calculation = dutch_lipid_clinic_network_score(
            metadata("DLCN"),
            dlcn_inputs(
                family_premature_chd_or_ldl_above_95th=True,
                family_xanthoma_arcus_or_child_ldl_above_95th=True,
                personal_premature_chd=True,
                personal_premature_cerebral_or_peripheral_vascular_disease=True,
                tendon_xanthoma=True,
                corneal_arcus_under_45=True,
                ldl_mg_dl=326,
                causative_ldlr_apob_pcsk9_mutation=True,
            ),
        )

        self.assertEqual(calculation.value["score"], 26)
        self.assertEqual(
            calculation.value["components"],
            {
                "family_history": 2,
                "clinical_history": 2,
                "physical_examination": 6,
                "ldl_cholesterol": 8,
                "genetic_testing": 8,
            },
        )
        self.assertEqual(calculation.value["classification"], "definite familial hypercholesterolemia")

    def test_dlcn_ldl_boundary_325_scores_five(self):
        calculation = dutch_lipid_clinic_network_score(
            metadata("DLCN"), dlcn_inputs(ldl_mg_dl=325)
        )

        self.assertEqual(calculation.value["score"], 5)
        self.assertEqual(calculation.value["classification"], "possible familial hypercholesterolemia")

    def test_guys_stone_score_covers_all_four_source_grades(self):
        cases = [
            ({"stone_count": "solitary", "location": "pelvis", "anatomy": "simple", "staghorn": "none"}, 1),
            ({"stone_count": "multiple", "location": "other", "anatomy": "simple", "staghorn": "none"}, 2),
            ({"stone_count": "multiple", "location": "other", "anatomy": "abnormal", "staghorn": "none"}, 3),
            ({"stone_count": "solitary", "location": "other", "anatomy": "simple", "staghorn": "complete"}, 4),
        ]
        for inputs, grade in cases:
            with self.subTest(grade=grade):
                calculation = guys_stone_score(metadata("Guy"), inputs)
                self.assertEqual(calculation.value["grade"], grade)

    def test_guys_stone_score_rejects_unrepresented_combination(self):
        with self.assertRaisesRegex(ValueError, "not represented"):
            guys_stone_score(
                metadata("Guy"),
                {"stone_count": "solitary", "location": "other", "anatomy": "simple", "staghorn": "none"},
            )

    def test_hendrich_ii_uses_published_item_weights_and_standard_threshold(self):
        calculation = hendrich_ii_fall_risk_model(
            metadata("Hendrich II"),
            {
                "confusion_disorientation_impulsivity": True,
                "symptomatic_depression": False,
                "altered_elimination": False,
                "dizziness_or_vertigo": False,
                "sex": "female",
                "antiepileptics": False,
                "benzodiazepines": False,
                "get_up_and_go": "pushes_up_one_attempt",
            },
        )

        self.assertEqual(calculation.value["score"], 5)
        self.assertTrue(calculation.value["high_fall_risk"])

    def test_hendrich_ii_get_up_and_go_weights_are_zero_one_three_four(self):
        expected = {
            "single_movement": 0,
            "pushes_up_one_attempt": 1,
            "multiple_attempts": 3,
            "unable_without_assistance": 4,
        }
        base = {
            "confusion_disorientation_impulsivity": False,
            "symptomatic_depression": False,
            "altered_elimination": False,
            "dizziness_or_vertigo": False,
            "sex": "female",
            "antiepileptics": False,
            "benzodiazepines": False,
        }
        for category, points in expected.items():
            with self.subTest(category=category):
                calculation = hendrich_ii_fall_risk_model(
                    metadata("Hendrich II"), {**base, "get_up_and_go": category}
                )
                self.assertEqual(calculation.value["score"], points)

    def test_chokai_reproduces_published_zero_to_thirteen_point_table(self):
        calculation = chokai_ureteral_stone_score(
            metadata("CHOKAI"),
            {
                "has_nausea_or_vomiting": True,
                "has_hydronephrosis": True,
                "has_occult_blood_in_urine": True,
                "history_kidney_stone": True,
                "sex": "male",
                "age_years": 59,
                "has_pain_reduction_within_6h": True,
            },
        )

        self.assertEqual(calculation.value["score"], 13)
        self.assertTrue(calculation.value["meets_2026_validation_cutoff"])
        self.assertEqual(sum(calculation.value["components"].values()), 13)

    def test_chokai_source_validation_cutoff_boundary(self):
        base = {
            "has_nausea_or_vomiting": False,
            "has_hydronephrosis": True,
            "has_occult_blood_in_urine": True,
            "history_kidney_stone": False,
            "sex": "female",
            "age_years": 60,
            "has_pain_reduction_within_6h": False,
        }
        below = chokai_ureteral_stone_score(metadata("CHOKAI"), base)
        at_cutoff = chokai_ureteral_stone_score(
            metadata("CHOKAI"), {**base, "has_nausea_or_vomiting": True}
        )

        self.assertEqual(below.value["score"], 7)
        self.assertFalse(below.value["meets_2026_validation_cutoff"])
        self.assertEqual(at_cutoff.value["score"], 8)
        self.assertTrue(at_cutoff.value["meets_2026_validation_cutoff"])

    def test_4c_deterioration_matches_official_calculator_reference_case(self):
        calculation = isaric_4c_deterioration_probability(
            metadata("4C deterioration"),
            {
                "age_years": 50,
                "sex": "female",
                "nosocomial": False,
                "has_radiographic_infiltrates": False,
                "on_oxygen_therapy": False,
                "has_gcs_below_15": False,
                "respiratory_rate_breaths_min": 20,
                "oxygen_saturation_percent": 95,
                "urea_mmol_l": 5,
                "crp_mg_l": 50,
                "lymphocytes_10e9_l": 1,
            },
        )

        self.assertAlmostEqual(calculation.value["risk_percent"], 12.7289, places=4)
        self.assertAlmostEqual(calculation.value["linear_predictor"], -1.925143, places=6)

    def test_4c_deterioration_rejects_extrapolation_beyond_official_ranges(self):
        with self.assertRaisesRegex(ValueError, "observed range"):
            isaric_4c_deterioration_probability(
                metadata("4C deterioration"),
                {
                    "age_years": 50,
                    "sex": "female",
                    "nosocomial": False,
                    "has_radiographic_infiltrates": False,
                    "on_oxygen_therapy": False,
                    "has_gcs_below_15": False,
                    "respiratory_rate_breaths_min": 20,
                    "oxygen_saturation_percent": 101,
                    "urea_mmol_l": 5,
                    "crp_mg_l": 50,
                    "lymphocytes_10e9_l": 1,
                },
            )

    def test_four_variable_kfre_matches_author_calculator_equation(self):
        calculation = kidney_failure_risk_equation_4_variable(
            metadata("KFRE"),
            {
                "age_years": 70,
                "sex": "female",
                "egfr_ml_min_1_73m2": 30,
                "urine_acr_mg_g": 100,
                "north_america": True,
            },
        )

        self.assertAlmostEqual(calculation.value["risk_2_year_percent"], 3.3902, places=4)
        self.assertAlmostEqual(calculation.value["risk_5_year_percent"], 10.2085, places=4)
        self.assertEqual(calculation.value["calibration"], "North American")

    def test_four_variable_kfre_uses_non_north_american_recalibration(self):
        calculation = kidney_failure_risk_equation_4_variable(
            metadata("KFRE"),
            {
                "age_years": 70,
                "sex": "female",
                "egfr_ml_min_1_73m2": 30,
                "urine_acr_mg_g": 100,
                "north_america": False,
            },
        )

        self.assertAlmostEqual(calculation.value["risk_2_year_percent"], 2.2817, places=4)
        self.assertAlmostEqual(calculation.value["risk_5_year_percent"], 8.5497, places=4)

    def test_four_variable_kfre_rejects_egfr_outside_validated_population(self):
        with self.assertRaisesRegex(ValueError, "below 60"):
            kidney_failure_risk_equation_4_variable(
                metadata("KFRE"),
                {
                    "age_years": 70,
                    "sex": "female",
                    "egfr_ml_min_1_73m2": 60,
                    "urine_acr_mg_g": 100,
                    "north_america": True,
                },
            )

    def test_eortc_2006_nmibc_reproduces_lowest_risk_table_row(self):
        calculation = eortc_2006_nmibc_risk_table(
            metadata("EORTC NMIBC"),
            {
                "tumor_count_category": "single",
                "tumor_size_category": "under_3_cm",
                "prior_recurrence_rate": "primary",
                "t_category": "ta",
                "concomitant_cis": False,
                "who_1973_grade": "g1",
            },
        )

        self.assertEqual(calculation.value["recurrence_score"], 0)
        self.assertEqual(calculation.value["progression_score"], 0)
        self.assertEqual(calculation.value["recurrence_risk_1_year_percent"], 15)
        self.assertEqual(calculation.value["recurrence_risk_5_year_percent"], 31)
        self.assertEqual(calculation.value["progression_risk_1_year_percent"], 0.2)
        self.assertEqual(calculation.value["progression_risk_5_year_percent"], 0.8)

    def test_eortc_2006_nmibc_reproduces_highest_risk_table_row(self):
        calculation = eortc_2006_nmibc_risk_table(
            metadata("EORTC NMIBC"),
            {
                "tumor_count_category": "eight_or_more",
                "tumor_size_category": "at_least_3_cm",
                "prior_recurrence_rate": "more_than_one_per_year",
                "t_category": "t1",
                "concomitant_cis": True,
                "who_1973_grade": "g3",
            },
        )

        self.assertEqual(calculation.value["recurrence_score"], 17)
        self.assertEqual(calculation.value["progression_score"], 23)
        self.assertEqual(calculation.value["recurrence_risk_1_year_percent"], 61)
        self.assertEqual(calculation.value["recurrence_risk_5_year_percent"], 78)
        self.assertEqual(calculation.value["progression_risk_1_year_percent"], 17)
        self.assertEqual(calculation.value["progression_risk_5_year_percent"], 45)

    def test_revised_rai_clinical_reproduces_source_maximum_score(self):
        calculation = revised_risk_analysis_index_clinical(
            metadata("RAI-C-rev"),
            {
                "age_years": 100,
                "sex": "male",
                "has_disseminated_cancer": True,
                "has_unintentional_weight_loss": True,
                "has_poor_appetite": True,
                "has_renal_failure": True,
                "has_chronic_or_congestive_heart_failure": True,
                "has_shortness_of_breath": True,
                "has_non_independent_residence": True,
                "has_cognitive_decline": True,
                "mobility_adl_0_to_4": 4,
                "eating_adl_0_to_4": 4,
                "toileting_adl_0_to_4": 4,
                "hygiene_adl_0_to_4": 4,
            },
        )

        self.assertEqual(calculation.value["score"], 81)
        self.assertEqual(calculation.value["adl_total"], 16)
        self.assertEqual(calculation.value["frailty_band"], "very high frailty signal")

    def test_revised_rai_clinical_age_cancer_and_adl_interactions(self):
        calculation = revised_risk_analysis_index_clinical(
            metadata("RAI-C-rev"),
            {
                "age_years": 70,
                "sex": "female",
                "has_disseminated_cancer": False,
                "has_unintentional_weight_loss": False,
                "has_poor_appetite": False,
                "has_renal_failure": False,
                "has_chronic_or_congestive_heart_failure": False,
                "has_shortness_of_breath": False,
                "has_non_independent_residence": False,
                "has_cognitive_decline": True,
                "mobility_adl_0_to_4": 1,
                "eating_adl_0_to_4": 1,
                "toileting_adl_0_to_4": 1,
                "hygiene_adl_0_to_4": 1,
            },
        )

        self.assertEqual(calculation.value["components"]["age_and_disseminated_cancer"], 22)
        self.assertEqual(calculation.value["components"]["adl_and_cognitive_decline"], 8)
        self.assertEqual(calculation.value["score"], 30)

    def test_revised_rai_clinical_rejects_noninteger_adl_levels(self):
        with self.assertRaisesRegex(ValueError, "integer from 0 to 4"):
            revised_risk_analysis_index_clinical(
                metadata("RAI-C-rev"),
                {
                    "age_years": 70,
                    "sex": "female",
                    "has_disseminated_cancer": False,
                    "has_unintentional_weight_loss": False,
                    "has_poor_appetite": False,
                    "has_renal_failure": False,
                    "has_chronic_or_congestive_heart_failure": False,
                    "has_shortness_of_breath": False,
                    "has_non_independent_residence": False,
                    "has_cognitive_decline": False,
                    "mobility_adl_0_to_4": 0.5,
                    "eating_adl_0_to_4": 0,
                    "toileting_adl_0_to_4": 0,
                    "hygiene_adl_0_to_4": 0,
                },
            )

    def test_plcom2012_centered_reference_case_reduces_to_model_constant(self):
        calculation = plcom2012_six_year_lung_cancer_risk(
            metadata("PLCOm2012"),
            {
                "age_years": 62,
                "race_ethnicity_plco": "white",
                "education_level_1_to_6": 4,
                "bmi": 27,
                "has_copd": False,
                "history_personal_cancer": False,
                "history_family_lung_cancer": False,
                "current_smoker": False,
                "smoking_intensity_cigarettes_day": 10 / 0.4021541613,
                "smoking_duration_years": 27,
                "quit_time_years": 10,
            },
        )

        self.assertAlmostEqual(calculation.value["linear_predictor"], -4.532506, places=6)
        self.assertAlmostEqual(calculation.value["risk_6_year_percent"], 1.0639, places=4)

    def test_plcom2012_applies_published_race_and_binary_coefficients(self):
        base = {
            "age_years": 62,
            "race_ethnicity_plco": "white",
            "education_level_1_to_6": 4,
            "bmi": 27,
            "has_copd": False,
            "history_personal_cancer": False,
            "history_family_lung_cancer": False,
            "current_smoker": True,
            "smoking_intensity_cigarettes_day": 20,
            "smoking_duration_years": 27,
            "quit_time_years": 0,
        }
        white = plcom2012_six_year_lung_cancer_risk(metadata("PLCOm2012"), base)
        pacific = plcom2012_six_year_lung_cancer_risk(
            metadata("PLCOm2012"),
            {**base, "race_ethnicity_plco": "native_hawaiian_or_pacific_islander"},
        )

        self.assertAlmostEqual(
            pacific.value["linear_predictor"] - white.value["linear_predictor"],
            1.027152,
            places=6,
        )

    def test_plcom2012_rejects_nonzero_quit_time_for_current_smoker(self):
        with self.assertRaisesRegex(ValueError, "must be 0"):
            plcom2012_six_year_lung_cancer_risk(
                metadata("PLCOm2012"),
                {
                    "age_years": 62,
                    "race_ethnicity_plco": "white",
                    "education_level_1_to_6": 4,
                    "bmi": 27,
                    "has_copd": False,
                    "history_personal_cancer": False,
                    "history_family_lung_cancer": False,
                    "current_smoker": True,
                    "smoking_intensity_cigarettes_day": 20,
                    "smoking_duration_years": 27,
                    "quit_time_years": 1,
                },
            )

    def test_ohts_egps_point_system_reproduces_lowest_published_risk_band(self):
        calculation = ohts_egps_five_year_poag_point_system(
            metadata("OHTS-EGPS"),
            {
                "age_years": 40,
                "mean_iop_mm_hg": 21,
                "mean_cct_micrometers": 600,
                "mean_vertical_cup_disc_ratio": 0.2,
                "mean_pattern_standard_deviation_db": 1.7,
            },
        )

        self.assertEqual(calculation.value["score"], 0)
        self.assertEqual(calculation.value["risk_5_year_band"], "at_most_4_percent")
        self.assertEqual(calculation.value["risk_5_year_display"], "≤4%")

    def test_ohts_egps_point_system_reproduces_highest_published_risk_band(self):
        calculation = ohts_egps_five_year_poag_point_system(
            metadata("OHTS-EGPS"),
            {
                "age_years": 75,
                "mean_iop_mm_hg": 28,
                "mean_cct_micrometers": 525,
                "mean_vertical_cup_disc_ratio": 0.6,
                "mean_pattern_standard_deviation_db": 2.8,
            },
        )

        self.assertEqual(calculation.value["score"], 20)
        self.assertEqual(calculation.value["risk_5_year_band"], "at_least_33_percent")
        self.assertEqual(calculation.value["risk_5_year_display"], "≥33%")

    def test_ohts_egps_rejects_values_outside_official_source_ranges(self):
        with self.assertRaisesRegex(ValueError, "20-32"):
            ohts_egps_five_year_poag_point_system(
                metadata("OHTS-EGPS"),
                {
                    "age_years": 60,
                    "mean_iop_mm_hg": 33,
                    "mean_cct_micrometers": 575,
                    "mean_vertical_cup_disc_ratio": 0.5,
                    "mean_pattern_standard_deviation_db": 2.0,
                },
            )

    def test_thoracoscore_baseline_case_reduces_to_official_intercept(self):
        calculation = thoracoscore_in_hospital_mortality(
            metadata("Thoracoscore"),
            {
                "age_years": 54,
                "sex": "female",
                "asa_class": 2,
                "ecog_performance_status": 2,
                "mrc_dyspnea_grade": 2,
                "urgent_or_emergency_surgery": False,
                "pneumonectomy": False,
                "malignant_diagnosis": False,
                "comorbidity_count": 0,
            },
        )

        self.assertAlmostEqual(calculation.value["linear_predictor"], -7.3737, places=4)
        self.assertAlmostEqual(calculation.value["in_hospital_mortality_percent"], 0.0627, places=4)

    def test_thoracoscore_applies_all_official_high_category_coefficients(self):
        calculation = thoracoscore_in_hospital_mortality(
            metadata("Thoracoscore"),
            {
                "age_years": 66,
                "sex": "male",
                "asa_class": 3,
                "ecog_performance_status": 3,
                "mrc_dyspnea_grade": 3,
                "urgent_or_emergency_surgery": True,
                "pneumonectomy": True,
                "malignant_diagnosis": True,
                "comorbidity_count": 3,
            },
        )

        self.assertAlmostEqual(calculation.value["linear_predictor"], 0.497, places=4)
        self.assertAlmostEqual(calculation.value["in_hospital_mortality_percent"], 62.1754, places=4)

    def test_thoracoscore_keeps_age_65_in_official_middle_category(self):
        base = {
            "sex": "female",
            "asa_class": 2,
            "ecog_performance_status": 2,
            "mrc_dyspnea_grade": 2,
            "urgent_or_emergency_surgery": False,
            "pneumonectomy": False,
            "malignant_diagnosis": False,
            "comorbidity_count": 0,
        }
        age_65 = thoracoscore_in_hospital_mortality(
            metadata("Thoracoscore"), {**base, "age_years": 65}
        )
        age_66 = thoracoscore_in_hospital_mortality(
            metadata("Thoracoscore"), {**base, "age_years": 66}
        )

        self.assertEqual(age_65.value["components"]["age"], 0.7679)
        self.assertEqual(age_66.value["components"]["age"], 1.0073)

    def test_maggic_reproduces_public_calculator_zero_point_case(self):
        calculation = maggic_heart_failure_mortality_score(
            metadata("MAGGIC"),
            {
                "age_years": 50,
                "ejection_fraction_percent": 45,
                "systolic_bp_mm_hg": 155,
                "bmi": 32,
                "serum_creatinine_umol_l": 80,
                "nyha_class": 1,
                "sex": "female",
                "current_smoker": False,
                "diabetes": False,
                "copd": False,
                "heart_failure_diagnosed_at_least_18_months": False,
                "on_beta_blocker": True,
                "on_acei_or_arb": True,
            },
        )

        self.assertEqual(calculation.value["score"], 0)
        self.assertEqual(calculation.value["risk_1_year_percent_lower_bound"], 1.5)
        self.assertEqual(calculation.value["risk_3_year_percent_lower_bound"], 3.9)

    def test_maggic_reproduces_public_calculator_eleven_point_case(self):
        calculation = maggic_heart_failure_mortality_score(
            metadata("MAGGIC"),
            {
                "age_years": 60,
                "ejection_fraction_percent": 40,
                "systolic_bp_mm_hg": 120,
                "bmi": 25,
                "serum_creatinine_umol_l": 100,
                "nyha_class": 2,
                "sex": "female",
                "current_smoker": False,
                "diabetes": False,
                "copd": False,
                "heart_failure_diagnosed_at_least_18_months": False,
                "on_beta_blocker": True,
                "on_acei_or_arb": True,
            },
        )

        self.assertEqual(calculation.value["score"], 11)
        self.assertEqual(calculation.value["risk_1_year_percent_lower_bound"], 4.3)
        self.assertEqual(calculation.value["risk_3_year_percent_lower_bound"], 11.1)

    def test_maggic_preserves_source_cap_for_scores_above_fifty(self):
        calculation = maggic_heart_failure_mortality_score(
            metadata("MAGGIC"),
            {
                "age_years": 80,
                "ejection_fraction_percent": 15,
                "systolic_bp_mm_hg": 100,
                "bmi": 14,
                "serum_creatinine_umol_l": 260,
                "nyha_class": 4,
                "sex": "male",
                "current_smoker": True,
                "diabetes": True,
                "copd": True,
                "heart_failure_diagnosed_at_least_18_months": True,
                "on_beta_blocker": False,
                "on_acei_or_arb": False,
            },
        )

        self.assertEqual(calculation.value["score"], 57)
        self.assertEqual(calculation.value["risk_1_year_display"], ">84.2%")
        self.assertEqual(calculation.value["risk_3_year_display"], ">98.5%")
        self.assertTrue(calculation.value["risk_table_capped_above_50"])


if __name__ == "__main__":
    unittest.main()
