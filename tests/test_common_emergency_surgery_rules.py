import unittest

from clinical_calculators.calculators.common import emergency_surgery_rules as emergency_rules
from clinical_calculators.calculators.common.emergency_surgery_rules import (
    adult_appendicitis_response_score,
    alvarado_appendicitis_score,
    body_surface_area_palm_method,
    centor_mcisaac_strep_pharyngitis_score,
    injury_severity_score,
    mangled_extremity_severity_score,
    nexus_chest_decision_instrument,
    ottawa_ankle_rules,
    ottawa_knee_rules,
    pediatric_trauma_score,
    tash_trauma_associated_severe_hemorrhage_score,
    triss_survival_probability,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str = "Emergency surgery rule") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="emergency_surgery",
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


class CommonEmergencySurgeryRulesTest(unittest.TestCase):
    def test_centor_mcisaac_age_ten_all_clinical_criteria_is_five_high(self):
        result = centor_mcisaac_strep_pharyngitis_score(
            metadata("Centor/McIsaac链球菌咽炎评分"),
            {
                "age_years": 10,
                "fever": True,
                "absence_of_cough": True,
                "tender_anterior_cervical_adenopathy": True,
                "tonsillar_exudates_or_swelling": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_centor_mcisaac_age_fifty_no_criteria_is_minus_one_low(self):
        result = centor_mcisaac_strep_pharyngitis_score(
            metadata("Centor/McIsaac链球菌咽炎评分"),
            {
                "age_years": 50,
                "fever": False,
                "absence_of_cough": False,
                "tender_anterior_cervical_adenopathy": False,
                "tonsillar_exudates_or_swelling": False,
            },
        )

        self.assertEqual(result.value, -1)
        self.assertEqual(result.unit, "points")
        self.assertIn("low", result.interpretation)

    def test_alvarado_all_criteria_scores_ten(self):
        result = alvarado_appendicitis_score(
            metadata("Alvarado阑尾炎评分"),
            {
                "migration_rlq": True,
                "anorexia": True,
                "nausea_vomiting": True,
                "rlq_tenderness": True,
                "rebound_tenderness": True,
                "fever": True,
                "leukocytosis": True,
                "left_shift": True,
            },
        )

        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("very probable", result.interpretation)

    def test_adult_appendicitis_response_all_max_scores_twelve(self):
        result = adult_appendicitis_response_score(
            metadata("成人阑尾炎反应评分"),
            {
                "vomiting": True,
                "rlq_pain": True,
                "rebound_or_muscular_defense": 3,
                "temperature_c": 38.5,
                "wbc_10e9_l": 15,
                "neutrophil_percent": 85,
                "crp_mg_l": 50,
            },
        )

        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_ottawa_ankle_malleolar_pain_and_lateral_tenderness_is_positive(self):
        result = ottawa_ankle_rules(
            metadata("渥太华踝关节规则"),
            {
                "pain_malleolar_zone": True,
                "bone_tenderness_posterior_lateral_malleolus": True,
                "bone_tenderness_posterior_medial_malleolus": False,
                "unable_to_bear_weight_4_steps": False,
                "pain_midfoot_zone": False,
                "bone_tenderness_navicular": False,
                "bone_tenderness_base_5th_metatarsal": False,
            },
        )

        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "")
        self.assertIn("positive", result.interpretation)

    def test_ottawa_ankle_no_pain_is_negative(self):
        result = ottawa_ankle_rules(
            metadata("渥太华踝关节规则"),
            {
                "pain_malleolar_zone": False,
                "bone_tenderness_posterior_lateral_malleolus": True,
                "bone_tenderness_posterior_medial_malleolus": True,
                "unable_to_bear_weight_4_steps": True,
                "pain_midfoot_zone": False,
                "bone_tenderness_navicular": True,
                "bone_tenderness_base_5th_metatarsal": True,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("negative", result.interpretation)

    def test_ottawa_knee_age_sixty_is_positive(self):
        result = ottawa_knee_rules(
            metadata("渥太华膝关节规则"),
            {
                "age_years": 60,
                "isolated_patellar_tenderness": False,
                "fibular_head_tenderness": False,
                "cannot_flex_to_90": False,
                "unable_to_bear_weight_4_steps": False,
            },
        )

        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "")
        self.assertIn("positive", result.interpretation)

    def test_ottawa_knee_age_thirty_all_negative_is_negative(self):
        result = ottawa_knee_rules(
            metadata("渥太华膝关节规则"),
            {
                "age_years": 30,
                "isolated_patellar_tenderness": False,
                "fibular_head_tenderness": False,
                "cannot_flex_to_90": False,
                "unable_to_bear_weight_4_steps": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("negative", result.interpretation)

    def test_boolean_inputs_reject_non_boolean_values(self):
        with self.assertRaises(ValueError):
            ottawa_knee_rules(
                metadata("渥太华膝关节规则"),
                {
                    "age_years": 30,
                    "isolated_patellar_tenderness": "yes",
                    "fibular_head_tenderness": False,
                    "cannot_flex_to_90": False,
                    "unable_to_bear_weight_4_steps": False,
                },
            )

    def test_adult_appendicitis_response_rejects_rebound_outside_zero_to_three(self):
        with self.assertRaises(ValueError):
            adult_appendicitis_response_score(
                metadata("成人阑尾炎反应评分"),
                {
                    "vomiting": False,
                    "rlq_pain": False,
                    "rebound_or_muscular_defense": 4,
                    "temperature_c": 37,
                    "wbc_10e9_l": 9,
                    "neutrophil_percent": 69,
                    "crp_mg_l": 9,
                },
            )

    def test_mangled_extremity_severity_score_doubles_ischemia_after_six_hours(self):
        result = mangled_extremity_severity_score(
            metadata("MESS肢体损伤评分", "Mangled Extremity Severity Score"),
            {
                "skeletal_soft_tissue_injury": 3,
                "limb_ischemia": 2,
                "ischemia_time_hours": 7,
                "shock": 1,
                "age": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 9)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_pediatric_trauma_score_sums_six_component_points(self):
        result = pediatric_trauma_score(
            metadata("儿童创伤评分", "Pediatric Trauma Score"),
            {
                "weight": 2,
                "airway": 2,
                "systolic_bp": 1,
                "central_nervous_system": 1,
                "open_wound": -1,
                "skeletal_injury": -1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertIn("higher trauma risk", result.interpretation)

    def test_body_surface_area_palm_method_counts_patient_palms_as_percent_tbsa(self):
        result = body_surface_area_palm_method(
            metadata("体表面积手掌法", "Body Surface Area by Palm Method"),
            {"patient_palms": 4.5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4.5)
        self.assertEqual(result.unit, "% TBSA")

    def test_nexus_chest_positive_if_any_criterion_present(self):
        result = nexus_chest_decision_instrument(
            metadata("NEXUS胸部影像决策工具", "NEXUS Chest Decision Instrument"),
            {
                "age_years": 61,
                "rapid_deceleration_mechanism": False,
                "chest_pain": False,
                "intoxication": False,
                "abnormal_alertness": False,
                "distracting_painful_injury": False,
                "chest_wall_tenderness": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1)
        self.assertIn("positive", result.interpretation)

    def test_injury_severity_score_squares_top_three_regions(self):
        result = injury_severity_score(
            metadata("损伤严重度评分", "Injury Severity Score"),
            {"ais_by_region": [5, 4, 3, 2, 1, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 50)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_injury_severity_score_is_75_if_any_ais_six(self):
        result = injury_severity_score(
            metadata("损伤严重度评分", "Injury Severity Score"),
            {"ais_by_region": [6, 1, 1, 1, 1, 1]},
        )

        self.assertEqual(result.value, 75)

    def test_injury_severity_score_rejects_fractional_ais_scores(self):
        with self.assertRaises(ValueError):
            injury_severity_score(
                metadata("损伤严重度评分", "Injury Severity Score"),
                {"ais_by_region": [2.5, 2, 1, 0, 0, 0]},
            )

    def test_triss_blunt_uses_original_logistic_coefficients(self):
        result = triss_survival_probability(
            metadata("TRISS生存概率", "Trauma and Injury Severity Score"),
            {
                "injury_type": "blunt",
                "revised_trauma_score": 7.8408,
                "injury_severity_score": 9,
                "age_years": 30,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 99.4164, places=4)
        self.assertEqual(result.unit, "%")
        self.assertIn("higher predicted survival", result.interpretation)

    def test_triss_penetrating_age_fifty_five_applies_age_index(self):
        result = triss_survival_probability(
            metadata("TRISS生存概率", "Trauma and Injury Severity Score"),
            {
                "injury_type": "penetrating",
                "revised_trauma_score": 5,
                "injury_severity_score": 25,
                "age_years": 55,
            },
        )

        self.assertAlmostEqual(result.value, 41.7754, places=4)
        self.assertIn("lower predicted survival", result.interpretation)

    def test_tash_maximum_component_profile_scores_thirty_one(self):
        result = tash_trauma_associated_severe_hemorrhage_score(
            metadata("TASH创伤相关严重出血评分", "Trauma Associated Severe Hemorrhage Score"),
            {
                "hemoglobin_g_dl": 6.9,
                "base_excess_mmol_l": -10.1,
                "systolic_bp_mm_hg": 99,
                "heart_rate": 121,
                "positive_fast": True,
                "unstable_pelvic_fracture": True,
                "open_or_dislocated_femur_fracture": True,
                "male": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 31)
        self.assertEqual(result.unit, "points")
        self.assertIn("very high", result.interpretation)

    def test_tash_systolic_bp_100_to_119_scores_one_point(self):
        result = tash_trauma_associated_severe_hemorrhage_score(
            metadata("TASH创伤相关严重出血评分", "Trauma Associated Severe Hemorrhage Score"),
            {
                "hemoglobin_g_dl": 12,
                "base_excess_mmol_l": 0,
                "systolic_bp_mm_hg": 119,
                "heart_rate": 100,
                "positive_fast": False,
                "unstable_pelvic_fracture": False,
                "open_or_dislocated_femur_fracture": False,
                "male": False,
            },
        )

        self.assertEqual(result.value, 1)

    def test_tash_boundary_values_score_zero_when_no_threshold_crossed(self):
        result = tash_trauma_associated_severe_hemorrhage_score(
            metadata("TASH创伤相关严重出血评分", "Trauma Associated Severe Hemorrhage Score"),
            {
                "hemoglobin_g_dl": 12,
                "base_excess_mmol_l": -2,
                "systolic_bp_mm_hg": 120,
                "heart_rate": 100,
                "positive_fast": False,
                "unstable_pelvic_fracture": False,
                "open_or_dislocated_femur_fracture": False,
                "male": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low", result.interpretation)

    def test_pecarn_pediatric_abdominal_trauma_all_criteria_absent_is_very_low_risk(self):
        calculator = getattr(emergency_rules, "pecarn_pediatric_abdominal_trauma_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("PECARN儿童腹部损伤规则", "PECARN Blunt Abdominal Trauma Rule"),
            {
                "abdominal_wall_trauma_or_seatbelt_sign": False,
                "gcs_less_than_14": False,
                "abdominal_tenderness": False,
                "thoracic_wall_trauma": False,
                "abdominal_pain": False,
                "decreased_breath_sounds": False,
                "vomiting": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertIn("very low risk", result.interpretation)

    def test_pecarn_pediatric_abdominal_trauma_any_criterion_present_is_positive(self):
        calculator = getattr(emergency_rules, "pecarn_pediatric_abdominal_trauma_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("PECARN儿童腹部损伤规则", "PECARN Blunt Abdominal Trauma Rule"),
            {
                "abdominal_wall_trauma_or_seatbelt_sign": False,
                "gcs_less_than_14": False,
                "abdominal_tenderness": True,
                "thoracic_wall_trauma": False,
                "abdominal_pain": False,
                "decreased_breath_sounds": False,
                "vomiting": False,
            },
        )

        self.assertEqual(result.value, 1)
        self.assertIn("positive", result.interpretation)

    def test_pecarn_pediatric_head_injury_younger_than_two_high_risk(self):
        calculator = getattr(emergency_rules, "pecarn_pediatric_head_injury_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("PECARN儿童头部损伤规则", "PECARN Pediatric Head Injury Rule"),
            {
                "age_years": 1,
                "gcs_le_14_or_altered_mental_status": True,
                "palpable_skull_fracture": False,
                "non_frontal_scalp_hematoma": False,
                "loss_of_consciousness_5_seconds_or_more": False,
                "severe_mechanism": False,
                "not_acting_normally_per_parent": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 2)
        self.assertIn("high risk", result.interpretation)

    def test_pecarn_pediatric_head_injury_age_two_or_older_all_absent_is_very_low_risk(self):
        calculator = getattr(emergency_rules, "pecarn_pediatric_head_injury_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("PECARN儿童头部损伤规则", "PECARN Pediatric Head Injury Rule"),
            {
                "age_years": 2,
                "gcs_le_14_or_altered_mental_status": False,
                "signs_basilar_skull_fracture": False,
                "history_loss_of_consciousness": False,
                "history_vomiting": False,
                "severe_mechanism": False,
                "severe_headache": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("very low risk", result.interpretation)

    def test_nexus_chest_ct_major_injury_rule_all_absent_is_low_risk(self):
        calculator = getattr(emergency_rules, "nexus_chest_ct_major_injury_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("NEXUS胸部CT主要损伤规则", "NEXUS Chest CT Major Injury Rule"),
            {
                "abnormal_chest_xray": False,
                "distracting_injury": False,
                "chest_wall_tenderness": False,
                "sternal_tenderness": False,
                "thoracic_spine_tenderness": False,
                "scapular_tenderness": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertIn("low risk", result.interpretation)

    def test_nexus_chest_ct_major_injury_rule_abnormal_xray_is_positive(self):
        calculator = getattr(emergency_rules, "nexus_chest_ct_major_injury_rule", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("NEXUS胸部CT主要损伤规则", "NEXUS Chest CT Major Injury Rule"),
            {
                "abnormal_chest_xray": True,
                "distracting_injury": False,
                "chest_wall_tenderness": False,
                "sternal_tenderness": False,
                "thoracic_spine_tenderness": False,
                "scapular_tenderness": False,
            },
        )

        self.assertEqual(result.value, 1)
        self.assertIn("positive", result.interpretation)


if __name__ == "__main__":
    unittest.main()
