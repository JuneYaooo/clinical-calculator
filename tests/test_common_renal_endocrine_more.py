import unittest

from clinical_calculators.calculators.common import renal_endocrine_more as renal_more
from clinical_calculators.calculators.common.renal_endocrine_more import (
    bariatric_percent_excess_weight_loss,
    burch_wartofsky_point_scale,
    cdc_prediabetes_risk_test,
    ckd_epi_2021_creatinine_cystatin_c,
    damico_prostate_cancer_risk_classification,
    dan_pss_score,
    diabetic_ketoacidosis_severity,
    finnish_diabetes_risk_score,
    homa_ir,
    iief_5_erectile_function_score,
    insulin_sensitivity_factor_estimate,
    international_prostate_symptom_score,
    ipss_quality_of_life,
    kdigo_ckd_ga_risk_category,
    metabolic_syndrome_criteria,
    peritoneal_dialysis_ktv,
    peritoneal_equilibration_test_category,
    sanaka_creatinine_clearance,
    single_pool_kt_v_daugirdas_ii,
    twenty_four_hour_urine_creatinine_excretion_estimate,
    ucsf_capra_prostate_cancer_risk_score,
    university_of_texas_diabetic_foot_classification,
    wagner_diabetic_foot_ulcer_classification,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="renal endocrine",
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


class CommonRenalEndocrineMoreTest(unittest.TestCase):
    def test_sanaka_creatinine_clearance_uses_sex_specific_albumin_formula(self):
        female_result = sanaka_creatinine_clearance(
            metadata("Sanaka肌酐清除率", "Sanaka Formula for Creatinine Clearance"),
            {
                "sex": "female",
                "weight_kg": 50,
                "serum_albumin_g_dl": 4.0,
                "serum_creatinine_mg_dl": 1.0,
            },
        )
        male_result = sanaka_creatinine_clearance(
            metadata("Sanaka肌酐清除率", "Sanaka Formula for Creatinine Clearance"),
            {
                "sex": "male",
                "weight_kg": 70,
                "serum_albumin_g_dl": 3.5,
                "serum_creatinine_mg_dl": 1.2,
            },
        )

        self.assertEqual(female_result.status, "implemented")
        self.assertAlmostEqual(female_result.value, 40.5, places=4)
        self.assertEqual(female_result.unit, "mL/min")
        self.assertIn("Sanaka", female_result.interpretation)
        self.assertAlmostEqual(male_result.value, 57.4583, places=4)

    def test_twenty_four_hour_urine_creatinine_excretion_estimate_compares_collection(self):
        result = twenty_four_hour_urine_creatinine_excretion_estimate(
            metadata("24小时尿肌酐排泄估算", "24-hour Urine Creatinine Excretion Estimate"),
            {
                "age_years": 60,
                "sex": "male",
                "weight_kg": 80,
                "black_race": False,
                "urine_creatinine_mg_dl": 100,
                "urine_volume_ml": 1500,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["estimated_creatinine_excretion_mg_day"], 1509.29, places=4)
        self.assertAlmostEqual(result.value["measured_creatinine_excretion_mg_day"], 1500.0, places=4)
        self.assertAlmostEqual(result.value["measured_percent_of_estimated"], 99.3845, places=4)
        self.assertEqual(result.unit, "mg/day")
        self.assertIn("complete", result.interpretation)

    def test_twenty_four_hour_urine_creatinine_estimate_uses_female_and_black_terms(self):
        result = twenty_four_hour_urine_creatinine_excretion_estimate(
            metadata("24小时尿肌酐排泄估算", "24-hour Urine Creatinine Excretion Estimate"),
            {"age_years": 70, "sex": "female", "weight_kg": 60, "black_race": True},
        )

        self.assertAlmostEqual(result.value["estimated_creatinine_excretion_mg_day"], 852.28, places=4)
        self.assertNotIn("measured_creatinine_excretion_mg_day", result.value)

    def test_burch_wartofsky_point_scale_scores_thyroid_storm_likelihood(self):
        result = burch_wartofsky_point_scale(
            metadata("Burch-Wartofsky甲状腺危象评分", "Burch-Wartofsky Point Scale"),
            {
                "temperature_f": 103.5,
                "heart_rate_bpm": 145,
                "cns_effects": "moderate",
                "gi_hepatic_dysfunction": "severe",
                "congestive_heart_failure": "moderate",
                "atrial_fibrillation": True,
                "precipitating_event": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 120)
        self.assertEqual(result.unit, "points")
        self.assertIn("highly suggestive", result.interpretation)

    def test_burch_wartofsky_point_scale_accepts_celsius_and_impending_range(self):
        result = burch_wartofsky_point_scale(
            metadata("Burch-Wartofsky甲状腺危象评分", "Burch-Wartofsky Point Scale"),
            {
                "temperature_c": 38.0,
                "heart_rate_bpm": 112,
                "cns_effects": "mild",
                "gi_hepatic_dysfunction": "absent",
                "congestive_heart_failure": "absent",
                "atrial_fibrillation": False,
                "precipitating_event": True,
            },
        )

        self.assertEqual(result.value, 40)
        self.assertIn("impending", result.interpretation)

    def test_wagner_diabetic_foot_ulcer_classification_maps_clinical_grade(self):
        result = wagner_diabetic_foot_ulcer_classification(
            metadata("糖尿病足Wagner分级", "Wagner Diabetic Foot Ulcer Classification"),
            {"wound_category": "deep_abscess_or_osteomyelitis"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "grade")
        self.assertIn("deep ulcer", result.interpretation)

    def test_wagner_diabetic_foot_ulcer_classification_identifies_forefoot_gangrene(self):
        result = wagner_diabetic_foot_ulcer_classification(
            metadata("糖尿病足Wagner分级", "Wagner Diabetic Foot Ulcer Classification"),
            {"wound_category": "forefoot_gangrene"},
        )

        self.assertEqual(result.value, 4)
        self.assertIn("forefoot", result.interpretation)

    def test_university_of_texas_diabetic_foot_classification_combines_grade_and_stage(self):
        result = university_of_texas_diabetic_foot_classification(
            metadata("德州大学糖尿病足分级", "University of Texas Diabetic Foot Classification"),
            {"grade": 2, "infected": True, "ischemic": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, {"classification": "2D", "grade": 2, "stage": "D"})
        self.assertEqual(result.unit, "grade/stage")
        self.assertIn("penetrates to tendon or capsule", result.interpretation)
        self.assertIn("infection and ischemia", result.interpretation)

    def test_university_of_texas_diabetic_foot_classification_stage_a(self):
        result = university_of_texas_diabetic_foot_classification(
            metadata("德州大学糖尿病足分级", "University of Texas Diabetic Foot Classification"),
            {"grade": 0, "infected": False, "ischemic": False},
        )

        self.assertEqual(result.value["classification"], "0A")
        self.assertIn("pre- or postulcerative", result.interpretation)

    def test_damico_prostate_cancer_risk_classification_uses_highest_risk_factor(self):
        high = damico_prostate_cancer_risk_classification(
            metadata("前列腺癌D'Amico风险分层", "D'Amico Prostate Cancer Risk Classification"),
            {"psa_ng_ml": 24, "gleason_score": 6, "clinical_t_stage": "T1c"},
        )
        intermediate = damico_prostate_cancer_risk_classification(
            metadata("前列腺癌D'Amico风险分层", "D'Amico Prostate Cancer Risk Classification"),
            {"psa_ng_ml": 8, "grade_group": 2, "clinical_t_stage": "cT2b"},
        )
        low = damico_prostate_cancer_risk_classification(
            metadata("前列腺癌D'Amico风险分层", "D'Amico Prostate Cancer Risk Classification"),
            {"psa_ng_ml": 10, "gleason_score": 6, "clinical_t_stage": "T2a"},
        )

        self.assertEqual(high.value, "high risk")
        self.assertIn("PSA >20", high.interpretation)
        self.assertEqual(intermediate.value, "intermediate risk")
        self.assertIn("grade group 2-3", intermediate.interpretation)
        self.assertEqual(low.value, "low risk")

    def test_finnish_diabetes_risk_score_uses_component_points_and_risk_band(self):
        result = finnish_diabetes_risk_score(
            metadata("芬兰糖尿病风险评分", "Finnish Diabetes Risk Score"),
            {
                "age_years": 58,
                "sex": "male",
                "bmi": 31,
                "waist_circumference_cm": 103,
                "physically_active_daily": False,
                "daily_fruit_vegetable_or_berry": False,
                "antihypertensive_medication": True,
                "history_high_blood_glucose": True,
                "family_history": "first_degree",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 25)
        self.assertEqual(result.value["risk_category"], "very high")
        self.assertEqual(result.value["estimated_10_year_risk"], "1 in 2")
        self.assertEqual(result.unit, "points")
        self.assertEqual(result.value["components"]["waist_circumference"], 4)
        self.assertIn("very high", result.interpretation)

    def test_finnish_diabetes_risk_score_maps_boundaries_and_second_degree_family_history(self):
        result = finnish_diabetes_risk_score(
            metadata("芬兰糖尿病风险评分", "Finnish Diabetes Risk Score"),
            {
                "age_years": 45,
                "sex": "female",
                "bmi": 26,
                "waist_circumference_cm": 80,
                "physically_active_daily": True,
                "daily_fruit_vegetable_or_berry": True,
                "antihypertensive_medication": False,
                "history_high_blood_glucose": False,
                "family_history": "second_degree",
            },
        )

        self.assertEqual(result.value["score"], 9)
        self.assertEqual(result.value["risk_category"], "slightly elevated")
        self.assertEqual(result.value["estimated_10_year_risk"], "1 in 25")
        self.assertEqual(result.value["components"]["age"], 2)
        self.assertEqual(result.value["components"]["waist_circumference"], 3)

    def test_finnish_diabetes_risk_score_rejects_invalid_family_history_code(self):
        with self.assertRaisesRegex(ValueError, "family_history must be"):
            finnish_diabetes_risk_score(
                metadata("芬兰糖尿病风险评分", "Finnish Diabetes Risk Score"),
                {
                    "age_years": 50,
                    "sex": "male",
                    "bmi": 24,
                    "waist_circumference_cm": 90,
                    "physically_active_daily": True,
                    "daily_fruit_vegetable_or_berry": True,
                    "antihypertensive_medication": False,
                    "history_high_blood_glucose": False,
                    "family_history": "cousin_only_unclear",
                },
            )

    def test_ucsf_capra_prostate_cancer_risk_score_matches_public_examples(self):
        low_intermediate = ucsf_capra_prostate_cancer_risk_score(
            metadata("UCSF-CAPRA前列腺癌风险评分", "UCSF-CAPRA Prostate Cancer Risk Score"),
            {
                "age_years": 51,
                "psa_ng_ml": 6.2,
                "gleason_primary": 3,
                "gleason_secondary": 4,
                "clinical_t_stage": "T2c",
                "positive_biopsy_cores": 2,
                "total_biopsy_cores": 8,
            },
        )
        high = ucsf_capra_prostate_cancer_risk_score(
            metadata("UCSF-CAPRA前列腺癌风险评分", "UCSF-CAPRA Prostate Cancer Risk Score"),
            {
                "age_years": 48,
                "psa_ng_ml": 15.2,
                "gleason_primary": 4,
                "gleason_secondary": 3,
                "clinical_t_stage": "T1c",
                "positive_biopsy_cores": 5,
                "total_biopsy_cores": 10,
            },
        )

        self.assertEqual(low_intermediate.status, "implemented")
        self.assertEqual(low_intermediate.value["score"], 3)
        self.assertEqual(low_intermediate.value["risk_category"], "intermediate risk")
        self.assertAlmostEqual(low_intermediate.value["percent_positive_cores"], 25.0)
        self.assertEqual(high.value["score"], 6)
        self.assertEqual(high.value["risk_category"], "high risk")
        self.assertEqual(high.unit, "points")

    def test_ucsf_capra_prostate_cancer_risk_score_accepts_percent_positive_cores_and_higher_t_stage(self):
        result = ucsf_capra_prostate_cancer_risk_score(
            metadata("UCSF-CAPRA前列腺癌风险评分", "UCSF-CAPRA Prostate Cancer Risk Score"),
            {
                "age_years": 60,
                "psa_ng_ml": 31,
                "gleason_primary": 5,
                "gleason_secondary": 4,
                "clinical_t_stage": "cT3b",
                "percent_positive_cores": 34,
            },
        )

        self.assertEqual(result.value["score"], 10)
        self.assertEqual(result.value["risk_category"], "high risk")
        self.assertEqual(result.value["components"]["clinical_t_stage"], 1)
        self.assertIn("CAPRA", result.interpretation)

    def test_ucsf_capra_prostate_cancer_risk_score_rejects_invalid_biopsy_core_counts(self):
        with self.assertRaisesRegex(ValueError, "positive_biopsy_cores must be no greater than total_biopsy_cores"):
            ucsf_capra_prostate_cancer_risk_score(
                metadata("UCSF-CAPRA前列腺癌风险评分", "UCSF-CAPRA Prostate Cancer Risk Score"),
                {
                    "age_years": 55,
                    "psa_ng_ml": 8,
                    "gleason_primary": 3,
                    "gleason_secondary": 4,
                    "clinical_t_stage": "T2",
                    "positive_biopsy_cores": 6,
                    "total_biopsy_cores": 5,
                },
            )

    def test_cdc_prediabetes_risk_test_scores_high_risk(self):
        result = cdc_prediabetes_risk_test(
            metadata("CDC糖尿病前期风险测试", "CDC Prediabetes Risk Test"),
            {
                "age_years": 60,
                "sex": "male",
                "history_gestational_diabetes": False,
                "first_degree_family_history": True,
                "high_blood_pressure": True,
                "physically_active": False,
                "bmi": 30,
                "asian_american": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 9)
        self.assertTrue(result.value["high_risk"])
        self.assertEqual(result.value["classification"], "high risk")
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_cdc_prediabetes_risk_test_uses_asian_bmi_cutoff_and_gestational_diabetes(self):
        result = cdc_prediabetes_risk_test(
            metadata("CDC糖尿病前期风险测试", "CDC Prediabetes Risk Test"),
            {
                "age_years": 42,
                "sex": "female",
                "history_gestational_diabetes": True,
                "first_degree_family_history": False,
                "high_blood_pressure": False,
                "physically_active": True,
                "bmi": 23,
                "asian_american": True,
            },
        )

        self.assertEqual(result.value["score"], 3)
        self.assertFalse(result.value["high_risk"])
        self.assertEqual(result.value["components"]["bmi"], 1)
        self.assertEqual(result.value["components"]["sex_or_gestational_diabetes"], 1)

    def test_cdc_prediabetes_risk_test_rejects_gestational_diabetes_for_male(self):
        with self.assertRaisesRegex(ValueError, "history_gestational_diabetes applies only when sex is 'female'"):
            cdc_prediabetes_risk_test(
                metadata("CDC糖尿病前期风险测试", "CDC Prediabetes Risk Test"),
                {
                    "age_years": 42,
                    "sex": "male",
                    "history_gestational_diabetes": True,
                    "first_degree_family_history": False,
                    "high_blood_pressure": False,
                    "physically_active": True,
                    "bmi": 23,
                    "asian_american": False,
                },
            )

    def test_homa_ir_uses_mmol_glucose_when_both_units_are_present(self):
        result = homa_ir(
            metadata("HOMA-IR胰岛素抵抗指数", "HOMA-IR"),
            {
                "fasting_insulin_uIU_ml": 10,
                "fasting_glucose_mmol_l": 4.5,
                "fasting_glucose_mg_dl": 200,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 2)
        self.assertEqual(result.unit, "index")
        self.assertIn("possible insulin resistance", result.interpretation)

    def test_homa_ir_uses_mg_dl_formula_when_mmol_missing(self):
        result = homa_ir(
            metadata("HOMA-IR胰岛素抵抗指数", "HOMA-IR"),
            {"fasting_insulin_uIU_ml": 18, "fasting_glucose_mg_dl": 90},
        )

        self.assertAlmostEqual(result.value, 4)
        self.assertIn("insulin resistance", result.interpretation)

    def test_homa_ir_requires_one_glucose_value(self):
        with self.assertRaisesRegex(KeyError, "fasting_glucose_mmol_l or fasting_glucose_mg_dl"):
            homa_ir(
                metadata("HOMA-IR胰岛素抵抗指数", "HOMA-IR"),
                {"fasting_insulin_uIU_ml": 10},
            )

    def test_insulin_sensitivity_factor_estimate_uses_1800_rule(self):
        result = insulin_sensitivity_factor_estimate(
            metadata("胰岛素敏感因子估算", "Insulin Sensitivity Factor Estimate"),
            {"total_daily_insulin_units": 40},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 45)
        self.assertEqual(result.unit, "mg/dL per unit")
        self.assertIn("1800 rule", result.interpretation)

    def test_insulin_sensitivity_factor_estimate_uses_1500_rule_for_regular_insulin(self):
        result = insulin_sensitivity_factor_estimate(
            metadata("胰岛素敏感因子估算", "Insulin Sensitivity Factor Estimate"),
            {"total_daily_insulin_units": 30, "insulin_type": "regular"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 50)
        self.assertEqual(result.unit, "mg/dL per unit")
        self.assertIn("1500 rule", result.interpretation)

    def test_diabetic_ketoacidosis_severity_uses_worst_consensus_criterion(self):
        cases = [
            (
                {
                    "beta_hydroxybutyrate_mmol_l": 4.0,
                    "ph": 7.28,
                    "bicarbonate_mmol_l": 16,
                    "mental_status": "normal",
                },
                "mild",
            ),
            (
                {
                    "beta_hydroxybutyrate_mmol_l": 5.5,
                    "ph": 7.20,
                    "bicarbonate_mmol_l": 12,
                    "mental_status": "drowsy",
                },
                "moderate",
            ),
            (
                {
                    "beta_hydroxybutyrate_mmol_l": 6.5,
                    "ph": 7.26,
                    "bicarbonate_mmol_l": 16,
                    "mental_status": "normal",
                },
                "severe",
            ),
        ]

        for inputs, severity in cases:
            with self.subTest(severity=severity):
                result = diabetic_ketoacidosis_severity(
                    metadata("DKA严重度分级", "Diabetic Ketoacidosis Severity"),
                    inputs,
                )

                self.assertEqual(result.status, "implemented")
                self.assertEqual(result.value, severity)
                self.assertEqual(result.unit, "severity")
                self.assertIn(severity, result.interpretation)

    def test_diabetic_ketoacidosis_severity_accepts_alert_mental_status(self):
        result = diabetic_ketoacidosis_severity(
            metadata("DKA严重度分级", "Diabetic Ketoacidosis Severity"),
            {
                "beta_hydroxybutyrate_mmol_l": 3.0,
                "ph": 7.29,
                "bicarbonate_mmol_l": 18,
                "mental_status": "alert",
            },
        )

        self.assertEqual(result.value, "mild")

    def test_ipss_score_moderate_and_ignores_quality_of_life(self):
        result = international_prostate_symptom_score(
            metadata("前列腺疾病症状评分", "International Prostate Symptom Score"),
            {"items": [2, 2, 2, 1, 1, 1, 1], "quality_of_life": 6},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_ipss_score_rejects_wrong_item_count(self):
        with self.assertRaisesRegex(ValueError, "items must contain exactly 7 scores"):
            international_prostate_symptom_score(
                metadata("前列腺疾病症状评分", "International Prostate Symptom Score"),
                {"items": [0, 1, 2, 3, 4, 5]},
            )

    def test_ipss_quality_of_life_labels(self):
        cases = [
            (0, "delighted"),
            (1, "pleased"),
            (2, "mostly satisfied"),
            (3, "mixed"),
            (4, "mostly dissatisfied"),
            (5, "unhappy"),
            (6, "terrible"),
        ]

        for score, label in cases:
            with self.subTest(score=score):
                result = ipss_quality_of_life(
                    metadata("IPSS生活质量单项", "IPSS Quality of Life"),
                    {"quality_of_life": score},
                )

                self.assertEqual(result.value, score)
                self.assertEqual(result.unit, "points")
                self.assertIn(label, result.interpretation)

    def test_iief_5_score_mild_to_moderate(self):
        result = iief_5_erectile_function_score(
            metadata("IIEF-5勃起功能评分", "IIEF-5"),
            {"items": [3, 3, 3, 3, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 15)
        self.assertEqual(result.unit, "points")
        self.assertIn("mild-to-moderate", result.interpretation)

    def test_iief_5_rejects_zero_item(self):
        with self.assertRaisesRegex(ValueError, r"items\[0\] must be between 1 and 5"):
            iief_5_erectile_function_score(
                metadata("IIEF-5勃起功能评分", "IIEF-5"),
                {"items": [0, 3, 3, 3, 3]},
            )

    def test_kdigo_ckd_ga_risk_category_returns_g_a_and_risk(self):
        result = kdigo_ckd_ga_risk_category(
            metadata("KDIGO CKD G-A风险分层", "KDIGO CKD G-A Risk"),
            {"egfr_ml_min_1_73m2": 38, "acr_mg_g": 120},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, {"G": "G3b", "A": "A2", "risk": "very high"})
        self.assertEqual(result.unit, "category")
        self.assertIn("very high", result.interpretation)

    def test_kdigo_ckd_ga_risk_boundaries(self):
        cases = [
            (95, 10, "G1", "A1", "low"),
            (60, 30, "G2", "A2", "moderate"),
            (45, 300, "G3a", "A2", "high"),
            (30, 301, "G3b", "A3", "very high"),
            (15, 20, "G4", "A1", "very high"),
            (14, 20, "G5", "A1", "very high"),
        ]

        for egfr, acr, g_category, a_category, risk in cases:
            with self.subTest(egfr=egfr, acr=acr):
                result = kdigo_ckd_ga_risk_category(
                    metadata("KDIGO CKD G-A风险分层", "KDIGO CKD G-A Risk"),
                    {"egfr_ml_min_1_73m2": egfr, "acr_mg_g": acr},
                )

                self.assertEqual(result.value, {"G": g_category, "A": a_category, "risk": risk})

    def test_ckd_epi_2021_creatinine_cystatin_c_male(self):
        result = ckd_epi_2021_creatinine_cystatin_c(
            metadata("CKD-EPI肌酐-胱抑素C联合方程", "CKD-EPI Creatinine-Cystatin C Equation"),
            {
                "age_years": 50,
                "serum_creatinine_mg_dl": 1.0,
                "cystatin_c_mg_l": 1.0,
                "sex": "male",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 88.1440, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")
        self.assertIn("creatinine-cystatin C", result.interpretation)

    def test_ckd_epi_2021_creatinine_cystatin_c_requires_adult_age(self):
        with self.assertRaisesRegex(ValueError, "age_years must be at least 18"):
            ckd_epi_2021_creatinine_cystatin_c(
                metadata("CKD-EPI肌酐-胱抑素C联合方程", "CKD-EPI Creatinine-Cystatin C Equation"),
                {
                    "age_years": 17,
                    "serum_creatinine_mg_dl": 1.0,
                    "cystatin_c_mg_l": 1.0,
                    "sex": "male",
                },
            )

    def test_metabolic_syndrome_criteria_requires_three_of_five_components(self):
        result = metabolic_syndrome_criteria(
            metadata("代谢综合征判定", "Metabolic Syndrome Criteria"),
            {
                "sex": "male",
                "waist_circumference_cm": 105,
                "triglycerides_mg_dl": 160,
                "hdl_mg_dl": 45,
                "systolic_bp": 128,
                "diastolic_bp": 80,
                "fasting_glucose_mg_dl": 95,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["criteria_met"], 2)
        self.assertFalse(result.value["metabolic_syndrome"])
        self.assertIn("not met", result.interpretation)

        result = metabolic_syndrome_criteria(
            metadata("代谢综合征判定", "Metabolic Syndrome Criteria"),
            {
                "sex": "female",
                "waist_circumference_cm": 90,
                "triglycerides_mg_dl": 140,
                "hdl_mg_dl": 45,
                "systolic_bp": 132,
                "diastolic_bp": 80,
                "fasting_glucose_mg_dl": 101,
            },
        )

        self.assertEqual(result.value["criteria_met"], 4)
        self.assertTrue(result.value["metabolic_syndrome"])
        self.assertIn("met", result.interpretation)

    def test_bariatric_percent_excess_weight_loss(self):
        result = bariatric_percent_excess_weight_loss(
            metadata("减重手术预期多余体重下降", "Percent Excess Weight Loss"),
            {"preoperative_weight_kg": 120, "current_weight_kg": 90, "ideal_weight_kg": 70},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 60)
        self.assertEqual(result.unit, "%")

    def test_bariatric_percent_excess_weight_loss_requires_preop_above_ideal(self):
        with self.assertRaisesRegex(ValueError, "preoperative_weight_kg must be greater than ideal_weight_kg"):
            bariatric_percent_excess_weight_loss(
                metadata("减重手术预期多余体重下降", "Percent Excess Weight Loss"),
                {"preoperative_weight_kg": 70, "current_weight_kg": 65, "ideal_weight_kg": 70},
            )

    def test_single_pool_kt_v_daugirdas_ii(self):
        result = single_pool_kt_v_daugirdas_ii(
            metadata("尿素清除指数透析剂量多重计算公式", "Single-pool Kt/V Daugirdas II"),
            {
                "pre_bun_mg_dl": 60,
                "post_bun_mg_dl": 18,
                "dialysis_hours": 4,
                "ultrafiltration_l": 2,
                "post_weight_kg": 70,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 1.4011)
        self.assertEqual(result.unit, "Kt/V")
        self.assertIn("Daugirdas II", result.interpretation)

    def test_single_pool_kt_v_rejects_invalid_log_argument(self):
        with self.assertRaisesRegex(ValueError, "R - 0.008\\*t must be positive"):
            single_pool_kt_v_daugirdas_ii(
                metadata("尿素清除指数透析剂量多重计算公式", "Single-pool Kt/V Daugirdas II"),
                {
                    "pre_bun_mg_dl": 60,
                    "post_bun_mg_dl": 1,
                    "dialysis_hours": 4,
                    "ultrafiltration_l": 2,
                    "post_weight_kg": 70,
                },
            )

    def test_peritoneal_dialysis_ktv_combines_dialysate_and_residual_clearance(self):
        result = peritoneal_dialysis_ktv(
            metadata("腹膜透析Kt/V", "Peritoneal Dialysis Kt/V"),
            {
                "serum_urea_mg_dl": 50,
                "dialysate_urea_mg_dl": 45,
                "dialysate_volume_l": 10,
                "urine_urea_mg_dl": 25,
                "urine_volume_l": 0.5,
                "urea_distribution_volume_l": 35,
                "collection_hours": 24,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["total_weekly_ktv"], 1.85, places=4)
        self.assertAlmostEqual(result.value["dialysate_weekly_ktv"], 1.8, places=4)
        self.assertAlmostEqual(result.value["residual_weekly_ktv"], 0.05, places=4)
        self.assertEqual(result.unit, "weekly Kt/V")

    def test_peritoneal_equilibration_test_category_uses_four_hour_creatinine_ratio(self):
        result = peritoneal_equilibration_test_category(
            metadata("腹膜平衡试验分类", "Peritoneal Equilibration Test"),
            {"dialysate_plasma_creatinine_ratio_4h": 0.70, "dialysate_initial_glucose_ratio_4h": 0.34},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["transport_category"], "high average")
        self.assertEqual(result.unit, "category")
        self.assertIn("high average", result.interpretation)

    def test_dan_pss_score_sums_prescored_symptom_bother_products(self):
        result = dan_pss_score(
            metadata("DAN-PSS", "DAN-PSS"),
            {"symptom_scores": [1, 2, 3], "bother_scores": [0, 2, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 13)
        self.assertEqual(result.value["item_scores"], [0, 4, 9])
        self.assertEqual(result.unit, "points")

    def test_pending_questionnaire_calculators_are_exposed(self):
        self.assertTrue(hasattr(renal_more, "overactive_bladder_symptom_score"))
        self.assertTrue(hasattr(renal_more, "clarke_hypoglycemia_awareness_score"))

    def test_overactive_bladder_symptom_score_classifies_oab_and_severity(self):
        result = renal_more.overactive_bladder_symptom_score(
            metadata("OABSS膀胱过度活动症评分", "Overactive Bladder Symptom Score"),
            {
                "daytime_frequency": 2,
                "nighttime_frequency": 2,
                "urgency": 3,
                "urgency_incontinence": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 11)
        self.assertTrue(result.value["oab_diagnostic_support"])
        self.assertEqual(result.value["severity"], "moderate")
        self.assertEqual(result.unit, "points")
        self.assertIn("moderate", result.interpretation)

    def test_overactive_bladder_symptom_score_requires_urgency_and_total_thresholds(self):
        result = renal_more.overactive_bladder_symptom_score(
            metadata("OABSS膀胱过度活动症评分", "Overactive Bladder Symptom Score"),
            {
                "daytime_frequency": 2,
                "nighttime_frequency": 1,
                "urgency": 1,
                "urgency_incontinence": 1,
            },
        )

        self.assertEqual(result.value["total_score"], 5)
        self.assertFalse(result.value["oab_diagnostic_support"])
        self.assertEqual(result.value["severity"], "mild")

    def test_overactive_bladder_symptom_score_rejects_component_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "urgency must be between 0 and 5"):
            renal_more.overactive_bladder_symptom_score(
                metadata("OABSS膀胱过度活动症评分", "Overactive Bladder Symptom Score"),
                {
                    "daytime_frequency": 1,
                    "nighttime_frequency": 1,
                    "urgency": 6,
                    "urgency_incontinence": 0,
                },
            )

    def test_clarke_hypoglycemia_awareness_score_classifies_impaired_awareness(self):
        result = renal_more.clarke_hypoglycemia_awareness_score(
            metadata("低血糖意识障碍Clarke评分", "Clarke Hypoglycemia Awareness Score"),
            {"impaired_awareness_responses": 4},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 4)
        self.assertEqual(result.value["classification"], "impaired awareness")
        self.assertTrue(result.value["impaired_awareness"])
        self.assertEqual(result.unit, "responses")
        self.assertIn("impaired awareness", result.interpretation)

    def test_clarke_hypoglycemia_awareness_score_classifies_normal_and_borderline(self):
        cases = [(2, "normal awareness", False), (3, "borderline awareness", False)]

        for score, classification, impaired in cases:
            with self.subTest(score=score):
                result = renal_more.clarke_hypoglycemia_awareness_score(
                    metadata("低血糖意识障碍Clarke评分", "Clarke Hypoglycemia Awareness Score"),
                    {"impaired_awareness_responses": score},
                )

                self.assertEqual(result.value["score"], score)
                self.assertEqual(result.value["classification"], classification)
                self.assertEqual(result.value["impaired_awareness"], impaired)

    def test_clarke_hypoglycemia_awareness_score_rejects_out_of_range_count(self):
        with self.assertRaisesRegex(ValueError, "impaired_awareness_responses must be between 0 and 8"):
            renal_more.clarke_hypoglycemia_awareness_score(
                metadata("低血糖意识障碍Clarke评分", "Clarke Hypoglycemia Awareness Score"),
                {"impaired_awareness_responses": 9},
            )


if __name__ == "__main__":
    unittest.main()
