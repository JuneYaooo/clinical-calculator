import unittest

from clinical_calculators.calculators.common.cardiac_risk_scores import (
    additive_euroscore,
    canadian_syncope_risk_score,
    dapt_score,
    duke_treadmill_score,
    grace_acs_risk_score,
    h2fpef_score,
    intracranial_hemorrhage_risk_thrombolytic_mi,
    non_q_wave_mi_prediction,
    orbit_af_bleeding_risk_score,
    ptca_mortality_risk_score,
    same_tt2r2_score,
    timi_stemi_score,
    timi_ua_nstemi_score,
    unstable_angina_outcome_prediction,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
        category="common",
        subspecialty="cardiovascular",
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


class CommonCardiacRiskScoresTest(unittest.TestCase):
    def test_intracranial_hemorrhage_risk_thrombolytic_mi_maps_high_score_risk(self):
        calculation = intracranial_hemorrhage_risk_thrombolytic_mi(
            metadata(
                "MI溶栓治疗颅内出血风险",
                "Intracranial Hemorrhage Risk with Thrombolytic Therapy for MI",
            ),
            {
                "age_years": 78,
                "race_black": True,
                "sex": "female",
                "prior_stroke": True,
                "systolic_bp": 170,
                "weight_kg": 60,
                "inr": 5,
                "prothrombin_time_seconds": 20,
                "tpa_instead_other_thrombolytic": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["score"], 8)
        self.assertEqual(calculation.value["risk_percent"], 4.11)
        self.assertEqual(calculation.unit, "points")

    def test_ptca_mortality_risk_score_subtracts_stent_and_maps_low_risk(self):
        calculation = ptca_mortality_risk_score(
            metadata("PTCA死亡率预测", "PTCA Mortality Risk Prediction"),
            {
                "cardiogenic_shock": False,
                "chf_class_iii_iv": False,
                "left_main_ptca": False,
                "tachycardia": False,
                "chronic_renal_insufficiency": False,
                "age_years": 70,
                "lesion_type_b2_or_c": False,
                "acute_mi": False,
                "unstable_angina": False,
                "stent_placed": True,
            },
        )

        self.assertEqual(calculation.value["score"], -1)
        self.assertEqual(calculation.value["mortality_percent"], 0.4)

    def test_unstable_angina_outcome_prediction_all_predictors_maps_high_risk(self):
        calculation = unstable_angina_outcome_prediction(
            metadata("不稳定型心绞痛结局预测", "Unstable Angina Outcome Prediction"),
            {
                "age_years": 70,
                "prior_cabg": True,
                "aspirin_use": True,
                "beta_blocker_use": True,
                "st_depression": True,
            },
        )

        self.assertEqual(calculation.value["score"], 5)
        self.assertEqual(calculation.value["risk_percent"], 37.1)

    def test_non_q_wave_mi_prediction_counts_four_public_predictors(self):
        calculation = non_q_wave_mi_prediction(
            metadata("非Q波心肌梗死预测", "Non-Q-Wave Myocardial Infarction Prediction"),
            {
                "no_prior_angioplasty": True,
                "pain_duration_minutes": 75,
                "st_deviation": True,
                "recent_angina": True,
            },
        )

        self.assertEqual(calculation.value["score"], 4)
        self.assertEqual(calculation.value["risk_percent"], 70.6)

    def test_timi_stemi_age76_all_positive_scores_fourteen(self):
        calculation = timi_stemi_score(
            metadata(
                "ST段抬高型心肌梗死溶栓（TIMI）评分",
                "TIMI Risk Score for STEMI",
            ),
            {
                "age_years": 76,
                "diabetes_hypertension_or_angina": True,
                "systolic_bp": 90,
                "heart_rate": 110,
                "killip_class_ii_to_iv": True,
                "weight_kg": 60,
                "anterior_st_elevation_or_lbbb": True,
                "time_to_treatment_hours": 5,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 14)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher 30-day mortality risk", calculation.interpretation)

    def test_timi_ua_nstemi_all_positive_age70_scores_seven(self):
        calculation = timi_ua_nstemi_score(
            metadata(
                "不稳定型心绞痛非ST段抬高型心肌梗死溶栓（TIMI）评分",
                "TIMI Risk Score for UA/NSTEMI",
            ),
            {
                "age_years": 70,
                "three_or_more_cad_risk_factors": True,
                "known_cad_stenosis_50_percent": True,
                "aspirin_past_7_days": True,
                "severe_angina_24h": True,
                "st_deviation": True,
                "positive_cardiac_marker": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 7)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher 14-day adverse event risk", calculation.interpretation)

    def test_dapt_age80_no_positives_scores_negative_two(self):
        calculation = dapt_score(
            metadata("DAPT评分", "DAPT Score"),
            {
                "age_years": 80,
                "current_smoker": False,
                "diabetes": False,
                "mi_at_presentation": False,
                "prior_pci_or_mi": False,
                "paclitaxel_eluting_stent": False,
                "stent_diameter_less_3mm": False,
                "chf_or_lvef_less_30": False,
                "vein_graft_stent": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, -2)
        self.assertEqual(calculation.unit, "points")

    def test_dapt_age60_all_positives_scores_ten(self):
        calculation = dapt_score(
            metadata("DAPT评分", "DAPT Score"),
            {
                "age_years": 60,
                "current_smoker": True,
                "diabetes": True,
                "mi_at_presentation": True,
                "prior_pci_or_mi": True,
                "paclitaxel_eluting_stent": True,
                "stent_diameter_less_3mm": True,
                "chf_or_lvef_less_30": True,
                "vein_graft_stent": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("favors prolonged DAPT benefit", calculation.interpretation)

    def test_duke_time9_st1_angina0_scores_four_moderate(self):
        calculation = duke_treadmill_score(
            metadata("Duke跑台评分", "Duke Treadmill Score"),
            {"exercise_time_minutes": 9, "st_deviation_mm": 1, "angina_index": 0},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate risk", calculation.interpretation)

    def test_duke_time3_st3_angina2_scores_negative_twenty_high(self):
        calculation = duke_treadmill_score(
            metadata("Duke跑台评分", "Duke Treadmill Score"),
            {"exercise_time_minutes": 3, "st_deviation_mm": 3, "angina_index": 2},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, -20)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high risk", calculation.interpretation)

    def test_orbit_age80_male_hb12_bleed_egfr50_antiplatelet_scores_seven_high(self):
        calculation = orbit_af_bleeding_risk_score(
            metadata("ORBIT房颤出血风险评分", "ORBIT AF Bleeding Risk Score"),
            {
                "age_years": 80,
                "hemoglobin_g_dl": 12,
                "sex": "male",
                "bleeding_history": True,
                "egfr_ml_min_1_73m2": 50,
                "antiplatelet_therapy": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 7)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high bleeding risk", calculation.interpretation)

    def test_h2fpef_all_positive_scores_nine_high_probability(self):
        calculation = h2fpef_score(
            metadata("H2FPEF心衰保留射血分数评分", "H2FPEF Score"),
            {
                "bmi": 31,
                "antihypertensive_medications_count": 2,
                "atrial_fibrillation": True,
                "pulmonary_artery_systolic_pressure_mm_hg": 36,
                "age_years": 61,
                "e_over_e_prime": 10,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 9)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high probability", calculation.interpretation)

    def test_same_tt2r2_all_positive_scores_eight_poor_control_risk(self):
        calculation = same_tt2r2_score(
            metadata("SAMe-TT2R2华法林控制预测", "SAMe-TT2R2 Score"),
            {
                "sex": "female",
                "age_years": 59,
                "two_or_more_comorbidities": True,
                "interacting_drugs": True,
                "tobacco_use_within_2_years": True,
                "non_caucasian_race": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 8)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher risk of poor warfarin control", calculation.interpretation)

    def test_canadian_syncope_all_high_risk_features_scores_eleven_very_high(self):
        calculation = canadian_syncope_risk_score(
            metadata("加拿大晕厥风险评分", "Canadian Syncope Risk Score"),
            {
                "predisposition_to_vasovagal_syncope": False,
                "history_of_heart_disease": True,
                "any_systolic_bp_less_90_or_greater_180": True,
                "elevated_troponin": True,
                "abnormal_qrs_axis": True,
                "qrs_duration_gt_130_ms": True,
                "qtc_gt_480_ms": True,
                "ed_diagnosis": "cardiac",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 11)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("very high risk", calculation.interpretation)

    def test_additive_euroscore_age_61_female_moderate_lv_and_major_risks_scores_fourteen(self):
        calculation = additive_euroscore(
            metadata(
                "EuroSCORE评分心脏手术风险评估（附加版）",
                "Additive EuroSCORE for Cardiac Operative Risk",
            ),
            {
                "age_years": 61,
                "sex": "female",
                "chronic_pulmonary_disease": True,
                "extracardiac_arteriopathy": False,
                "neurologic_dysfunction": False,
                "previous_cardiac_surgery": True,
                "serum_creatinine_gt_200_umol_l": False,
                "active_endocarditis": False,
                "critical_preoperative_state": True,
                "unstable_angina_iv_nitrates": False,
                "left_ventricular_function": "moderate",
                "recent_mi_90_days": True,
                "pulmonary_hypertension": False,
                "emergency_operation": False,
                "other_than_isolated_cabg": True,
                "thoracic_aorta_surgery": False,
                "postinfarct_septal_rupture": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 14)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high operative risk", calculation.interpretation)

    def test_additive_euroscore_age60_good_lv_no_risks_scores_zero(self):
        calculation = additive_euroscore(
            metadata(
                "EuroSCORE评分心脏手术风险评估（附加版）",
                "Additive EuroSCORE for Cardiac Operative Risk",
            ),
            {
                "age_years": 60,
                "sex": "male",
                "chronic_pulmonary_disease": False,
                "extracardiac_arteriopathy": False,
                "neurologic_dysfunction": False,
                "previous_cardiac_surgery": False,
                "serum_creatinine_gt_200_umol_l": False,
                "active_endocarditis": False,
                "critical_preoperative_state": False,
                "unstable_angina_iv_nitrates": False,
                "left_ventricular_function": "good",
                "recent_mi_90_days": False,
                "pulmonary_hypertension": False,
                "emergency_operation": False,
                "other_than_isolated_cabg": False,
                "thoracic_aorta_surgery": False,
                "postinfarct_septal_rupture": False,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("low operative risk", calculation.interpretation)

    def test_grace_acs_all_lowest_values_scores_one(self):
        calculation = grace_acs_risk_score(
            metadata("GRACE急性冠脉综合征风险评分", "GRACE ACS Risk Score"),
            {
                "age_years": 29,
                "heart_rate": 49,
                "systolic_bp": 200,
                "creatinine_mg_dl": 0.3,
                "killip_class": 1,
                "cardiac_arrest_at_admission": False,
                "st_segment_deviation": False,
                "elevated_cardiac_markers": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 1)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("low risk", calculation.interpretation)

    def test_grace_acs_all_highest_values_scores_three_hundred_seventy_two(self):
        calculation = grace_acs_risk_score(
            metadata("GRACE急性冠脉综合征风险评分", "GRACE ACS Risk Score"),
            {
                "age_years": 90,
                "heart_rate": 200,
                "systolic_bp": 70,
                "creatinine_mg_dl": 4,
                "killip_class": 4,
                "cardiac_arrest_at_admission": True,
                "st_segment_deviation": True,
                "elevated_cardiac_markers": True,
            },
        )

        self.assertEqual(calculation.value, 372)
        self.assertIn("high risk", calculation.interpretation)


if __name__ == "__main__":
    unittest.main()
