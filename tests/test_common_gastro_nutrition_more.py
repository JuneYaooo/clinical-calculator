import unittest

from clinical_calculators.calculators.common.gastro_nutrition_more import (
    aims65_upper_gi_bleeding_score,
    adenoma_detection_rate,
    bclc_hepatocellular_carcinoma_stage,
    crohns_disease_activity_index,
    feverpain_sore_throat_score,
    forns_index,
    geriatric_nutritional_risk_index,
    glasgow_blatchford_upper_gi_bleeding_score,
    glim_malnutrition_criteria,
    harvey_bradshaw_index,
    kings_college_criteria_acute_liver_failure,
    mayo_score_ulcerative_colitis,
    modified_ct_severity_index_acute_pancreatitis,
    montreal_classification_crohns_disease,
    montreal_classification_ulcerative_colitis,
    must_malnutrition_screening,
    nrs_2002_nutritional_risk_screening,
    nutritional_risk_index,
    partial_mayo_score_ulcerative_colitis,
    refeeding_syndrome_risk_nice,
    revised_atlanta_acute_pancreatitis_classification,
    rockall_upper_gi_bleeding_score,
    rutgeerts_score_postoperative_crohn_recurrence,
    severe_lower_gi_bleeding_risk_score,
    simple_clinical_colitis_activity_index,
    simple_endoscopic_score_crohns_disease,
    tips_survival_from_risk_score,
    tips_survival_probability,
    ulcerative_colitis_endoscopic_index_severity,
    ulcerative_colitis_baron_endoscopic_score,
    boston_bowel_preparation_scale,
    controlling_nutritional_status_score,
    full_rockall_score,
    hisort_autoimmune_pancreatitis_criteria,
    ibs_severity_scoring_system,
    tokyo_guidelines_cholangitis_severity,
    tokyo_guidelines_cholecystitis_severity,
    west_haven_hepatic_encephalopathy_grade,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
        category="common",
        subspecialty="gastro_nutrition",
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


class CommonGastroNutritionMoreTest(unittest.TestCase):
    def test_glasgow_blatchford_scores_all_major_positive_findings(self):
        calculation = glasgow_blatchford_upper_gi_bleeding_score(
            metadata("Glasgow-Blatchford上消化道出血评分", "Glasgow-Blatchford Score"),
            {
                "bun_mg_dl": 70.025,
                "hemoglobin_g_dl": 9.8,
                "sex": "male",
                "systolic_bp": 88,
                "pulse": 110,
                "melena": True,
                "syncope": True,
                "hepatic_disease": True,
                "cardiac_failure": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 23)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher risk", calculation.interpretation)

    def test_glasgow_blatchford_score_one_is_very_low_risk(self):
        calculation = glasgow_blatchford_upper_gi_bleeding_score(
            metadata("Glasgow-Blatchford上消化道出血评分", "Glasgow-Blatchford Score"),
            {
                "bun_mg_dl": 12,
                "hemoglobin_g_dl": 11.4,
                "sex": "female",
                "systolic_bp": 120,
                "pulse": 80,
                "melena": False,
                "syncope": False,
                "hepatic_disease": False,
                "cardiac_failure": False,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("very low risk", calculation.interpretation)

    def test_glasgow_blatchford_rejects_unknown_sex(self):
        with self.assertRaises(ValueError):
            glasgow_blatchford_upper_gi_bleeding_score(
                metadata("Glasgow-Blatchford上消化道出血评分", "Glasgow-Blatchford Score"),
                {
                    "bun_mg_dl": 20,
                    "hemoglobin_g_dl": 12,
                    "sex": "unknown",
                    "systolic_bp": 110,
                    "pulse": 90,
                    "melena": False,
                    "syncope": False,
                    "hepatic_disease": False,
                    "cardiac_failure": False,
                },
            )

    def test_rockall_scores_high_risk_total_eleven(self):
        calculation = rockall_upper_gi_bleeding_score(
            metadata("Rockall上消化道出血评分", "Rockall Score"),
            {
                "age_years": 82,
                "shock": "hypotension",
                "comorbidity": "renal_liver_malignancy",
                "diagnosis": "upper_gi_malignancy",
                "stigmata": "blood_or_adherent_clot_or_visible_vessel",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 11)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high", calculation.interpretation)

    def test_rockall_score_two_is_low_risk(self):
        calculation = rockall_upper_gi_bleeding_score(
            metadata("Rockall上消化道出血评分", "Rockall Score"),
            {
                "age_years": 65,
                "shock": "tachycardia",
                "comorbidity": "none",
                "diagnosis": "mallory_weiss_or_none",
                "stigmata": "none_or_dark_spot",
            },
        )

        self.assertEqual(calculation.value, 2)
        self.assertIn("low", calculation.interpretation)

    def test_rockall_rejects_unknown_shock_category(self):
        with self.assertRaises(ValueError):
            rockall_upper_gi_bleeding_score(
                metadata("Rockall上消化道出血评分", "Rockall Score"),
                {
                    "age_years": 65,
                    "shock": "borderline",
                    "comorbidity": "none",
                    "diagnosis": "all_other",
                    "stigmata": "none_or_dark_spot",
                },
            )

    def test_aims65_scores_all_five_points_and_higher_risk(self):
        calculation = aims65_upper_gi_bleeding_score(
            metadata("AIMS65上消化道出血评分", "AIMS65 Score"),
            {
                "albumin_g_dl": 2.9,
                "inr": 1.6,
                "altered_mental_status": True,
                "systolic_bp": 90,
                "age_years": 66,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher risk", calculation.interpretation)

    def test_aims65_score_one_is_lower_risk(self):
        calculation = aims65_upper_gi_bleeding_score(
            metadata("AIMS65上消化道出血评分", "AIMS65 Score"),
            {
                "albumin_g_dl": 3.0,
                "inr": 1.5,
                "altered_mental_status": False,
                "systolic_bp": 91,
                "age_years": 66,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("lower risk", calculation.interpretation)

    def test_must_score_five_is_high_risk(self):
        calculation = must_malnutrition_screening(
            metadata("MUST营养不良筛查", "MUST Malnutrition Universal Screening Tool"),
            {
                "bmi": 18.4,
                "unplanned_weight_loss_percent": 12,
                "acute_disease_no_intake_over_5_days": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 6)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high", calculation.interpretation)

    def test_must_score_one_is_medium_risk(self):
        calculation = must_malnutrition_screening(
            metadata("MUST营养不良筛查", "MUST Malnutrition Universal Screening Tool"),
            {
                "bmi": 20.0,
                "unplanned_weight_loss_percent": 4.9,
                "acute_disease_no_intake_over_5_days": False,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("medium", calculation.interpretation)

    def test_nrs_2002_score_three_indicates_nutritional_risk(self):
        calculation = nrs_2002_nutritional_risk_screening(
            metadata("NRS-2002营养风险筛查", "NRS-2002 Nutritional Risk Screening"),
            {"impaired_nutritional_status": 1, "disease_severity": 1, "age_years": 72},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 3)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("nutritional risk", calculation.interpretation)

    def test_nrs_2002_rejects_out_of_range_component(self):
        with self.assertRaises(ValueError):
            nrs_2002_nutritional_risk_screening(
                metadata("NRS-2002营养风险筛查", "NRS-2002 Nutritional Risk Screening"),
                {"impaired_nutritional_status": 4, "disease_severity": 1, "age_years": 72},
            )

    def test_nutritional_risk_index_calculates_moderate_risk_from_albumin_and_weight_ratio(self):
        calculation = nutritional_risk_index(
            metadata("营养风险指数", "Nutritional Risk Index"),
            {"albumin_g_dl": 3.2, "current_weight_kg": 60, "usual_weight_kg": 70},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 84.351, places=3)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_geriatric_nutritional_risk_index_caps_weight_ratio_at_one(self):
        calculation = geriatric_nutritional_risk_index(
            metadata("老年营养风险指数", "Geriatric Nutritional Risk Index"),
            {"albumin_g_dl": 3.2, "current_weight_kg": 70, "ideal_weight_kg": 60},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 89.348, places=3)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_refeeding_syndrome_risk_nice_flags_one_major_criterion(self):
        calculation = refeeding_syndrome_risk_nice(
            metadata("再喂养综合征风险筛查", "Refeeding Syndrome Risk"),
            {
                "bmi": 15.9,
                "unintentional_weight_loss_percent": 4,
                "little_or_no_nutritional_intake_days": 3,
                "low_potassium_phosphate_or_magnesium_before_feeding": False,
                "alcohol_misuse_or_relevant_drugs": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertTrue(calculation.value["high_risk"])
        self.assertEqual(calculation.value["major_criteria_met"], 1)
        self.assertEqual(calculation.value["minor_criteria_met"], 1)
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("high risk", calculation.interpretation)

    def test_refeeding_syndrome_risk_nice_flags_two_minor_criteria(self):
        calculation = refeeding_syndrome_risk_nice(
            metadata("再喂养综合征风险筛查", "Refeeding Syndrome Risk"),
            {
                "bmi": 17.0,
                "unintentional_weight_loss_percent": 11,
                "little_or_no_nutritional_intake_days": 6,
                "low_potassium_phosphate_or_magnesium_before_feeding": False,
                "alcohol_misuse_or_relevant_drugs": False,
            },
        )

        self.assertTrue(calculation.value["high_risk"])
        self.assertEqual(calculation.value["major_criteria_met"], 0)
        self.assertEqual(calculation.value["minor_criteria_met"], 3)

    def test_feverpain_score_five_is_high_likelihood(self):
        calculation = feverpain_sore_throat_score(
            metadata("FeverPAIN咽痛评分", "FeverPAIN Score"),
            {
                "fever_past_24h": True,
                "purulence": True,
                "attend_rapidly_3_days_or_less": True,
                "severely_inflamed_tonsils": True,
                "no_cough_or_coryza": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high", calculation.interpretation)

    def test_feverpain_score_two_is_intermediate_likelihood(self):
        calculation = feverpain_sore_throat_score(
            metadata("FeverPAIN咽痛评分", "FeverPAIN Score"),
            {
                "fever_past_24h": True,
                "purulence": False,
                "attend_rapidly_3_days_or_less": False,
                "severely_inflamed_tonsils": True,
                "no_cough_or_coryza": False,
            },
        )

        self.assertEqual(calculation.value, 2)
        self.assertIn("intermediate", calculation.interpretation)

    def test_feverpain_rejects_non_boolean_flag(self):
        with self.assertRaises(ValueError):
            feverpain_sore_throat_score(
                metadata("FeverPAIN咽痛评分", "FeverPAIN Score"),
                {
                    "fever_past_24h": "yes",
                    "purulence": False,
                    "attend_rapidly_3_days_or_less": False,
                    "severely_inflamed_tonsils": True,
                    "no_cough_or_coryza": False,
                },
            )

    def test_crohns_disease_activity_index_uses_weighted_seven_day_components(self):
        calculation = crohns_disease_activity_index(
            metadata("克罗恩病活动指数（CDAI）", "Crohn's Disease Activity Index"),
            {
                "liquid_stools_7_days": 28,
                "abdominal_pain_sum_7_days": 14,
                "general_wellbeing_sum_7_days": 14,
                "complications_count": 2,
                "antidiarrheal_or_opiate": True,
                "abdominal_mass": 5,
                "hematocrit_percent": 35,
                "sex": "male",
                "current_weight_kg": 60,
                "standard_weight_kg": 70,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 430.29, places=2)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_ses_cd_sums_prescored_segment_domains(self):
        calculation = simple_endoscopic_score_crohns_disease(
            metadata("简化内镜克罗恩评分", "Simple Endoscopic Score for Crohn's Disease"),
            {
                "segments": [
                    {"name": "ileum", "ulcer_size": 2, "ulcerated_surface": 1, "affected_surface": 2, "narrowing": 0},
                    {"name": "right_colon", "ulcer_size": 1, "ulcerated_surface": 1, "affected_surface": 1, "narrowing": 1},
                    {
                        "name": "transverse_colon",
                        "ulcer_size": 0,
                        "ulcerated_surface": 0,
                        "affected_surface": 1,
                        "narrowing": 0,
                    },
                    {"name": "left_colon", "ulcer_size": 3, "ulcerated_surface": 2, "affected_surface": 2, "narrowing": 1},
                    {"name": "rectum", "ulcer_size": 0, "ulcerated_surface": 0, "affected_surface": 0, "narrowing": 0},
                ],
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["total_score"], 18)
        self.assertEqual(calculation.value["segment_scores"]["left_colon"], 8)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("endoscopic activity", calculation.interpretation)

    def test_montreal_crohn_classification_combines_age_location_behavior_and_modifiers(self):
        calculation = montreal_classification_crohns_disease(
            metadata("蒙特利尔克罗恩病分类", "Montreal Classification for Crohn's Disease"),
            {
                "age_at_diagnosis_years": 32,
                "location": "l3",
                "upper_gi_modifier": True,
                "behavior": "b2",
                "perianal_modifier": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["age"], "A2")
        self.assertEqual(calculation.value["location"], "L3+L4")
        self.assertEqual(calculation.value["behavior"], "B2p")
        self.assertEqual(calculation.value["classification"], "A2 L3+L4 B2p")
        self.assertEqual(calculation.unit, "classification")

    def test_montreal_ulcerative_colitis_classification_combines_extent_and_severity(self):
        calculation = montreal_classification_ulcerative_colitis(
            metadata("蒙特利尔溃疡性结肠炎分类", "Montreal Classification for Ulcerative Colitis"),
            {"extent": "e3", "severity": "s2"},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["extent"], "E3")
        self.assertEqual(calculation.value["severity"], "S2")
        self.assertEqual(calculation.value["classification"], "E3 S2")
        self.assertEqual(calculation.unit, "classification")

    def test_boston_bowel_preparation_scale_sums_three_segment_scores(self):
        calculation = boston_bowel_preparation_scale(
            metadata("波士顿肠道准备量表", "Boston Bowel Preparation Scale"),
            {"right_colon": 2, "transverse_colon": 3, "left_colon": 2},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["total_score"], 7)
        self.assertTrue(calculation.value["adequate_preparation"])
        self.assertEqual(calculation.unit, "points")
        self.assertIn("adequate", calculation.interpretation)

    def test_conut_scores_albumin_lymphocytes_and_cholesterol_cutoffs(self):
        calculation = controlling_nutritional_status_score(
            metadata("CONUT营养状态评分", "Controlling Nutritional Status Score"),
            {
                "albumin_g_dl": 2.8,
                "total_lymphocytes_per_mm3": 950,
                "total_cholesterol_mg_dl": 120,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["total_score"], 8)
        self.assertEqual(calculation.value["albumin_points"], 4)
        self.assertEqual(calculation.value["lymphocyte_points"], 2)
        self.assertEqual(calculation.value["cholesterol_points"], 2)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_uceis_sums_three_endoscopic_domains(self):
        calculation = ulcerative_colitis_endoscopic_index_severity(
            metadata("UC内镜严重度指数", "Ulcerative Colitis Endoscopic Index of Severity"),
            {"vascular_pattern": 2, "bleeding": 3, "erosions_ulcers": 3},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 8)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_rutgeerts_score_returns_grade_and_recurrence_flag(self):
        calculation = rutgeerts_score_postoperative_crohn_recurrence(
            metadata("Rutgeerts术后克罗恩复发评分", "Rutgeerts Score"),
            {"grade": "i2"},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], "i2")
        self.assertTrue(calculation.value["endoscopic_recurrence"])
        self.assertIn("recurrence", calculation.interpretation)

    def test_glim_requires_phenotypic_and_etiologic_criteria(self):
        calculation = glim_malnutrition_criteria(
            metadata("GLIM营养不良诊断框架", "GLIM Malnutrition Criteria"),
            {
                "weight_loss": True,
                "low_bmi": False,
                "reduced_muscle_mass": False,
                "reduced_food_intake_or_assimilation": True,
                "inflammation_or_disease_burden": False,
                "severe_phenotypic_criterion": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertTrue(calculation.value["malnutrition"])
        self.assertEqual(calculation.value["severity"], "severe")

    def test_mayo_score_ulcerative_colitis_sums_four_zero_to_three_components(self):
        calculation = mayo_score_ulcerative_colitis(
            metadata("Mayo溃疡性结肠炎评分", "Mayo Score for Ulcerative Colitis"),
            {
                "stool_frequency": 2,
                "rectal_bleeding": 1,
                "endoscopic_findings": 2,
                "physician_global_assessment": 1,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 6)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_sccai_sums_precoded_activity_components(self):
        calculation = simple_clinical_colitis_activity_index(
            metadata("简化临床结肠炎活动指数", "Simple Clinical Colitis Activity Index"),
            {
                "daytime_stool_frequency": 2,
                "nocturnal_stool_frequency": 1,
                "urgency": 2,
                "blood_in_stool": 1,
                "general_wellbeing": 2,
                "extracolonic_manifestations": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("active", calculation.interpretation)

    def test_partial_mayo_score_sums_three_zero_to_three_components(self):
        calculation = partial_mayo_score_ulcerative_colitis(
            metadata("部分Mayo评分", "Partial Mayo Score"),
            {"stool_frequency": 2, "rectal_bleeding": 1, "physician_global_assessment": 2},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_harvey_bradshaw_index_scores_clinical_crohn_activity(self):
        calculation = harvey_bradshaw_index(
            metadata("Harvey-Bradshaw克罗恩指数", "Harvey-Bradshaw Index"),
            {
                "general_wellbeing": 2,
                "abdominal_pain": 2,
                "liquid_stools_per_day": 5,
                "abdominal_mass": 1,
                "complications_count": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 12)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("moderate", calculation.interpretation)

    def test_modified_ct_severity_index_scores_pancreatitis_imaging(self):
        calculation = modified_ct_severity_index_acute_pancreatitis(
            metadata("急性胰腺炎改良CT严重指数", "Modified CT Severity Index"),
            {
                "pancreatic_inflammation": 4,
                "pancreatic_necrosis_percent": 35,
                "extrapancreatic_complications": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_revised_atlanta_classifies_persistent_organ_failure_as_severe(self):
        calculation = revised_atlanta_acute_pancreatitis_classification(
            metadata("Atlanta急性胰腺炎严重度分类", "Revised Atlanta Classification"),
            {"organ_failure": "persistent", "local_or_systemic_complications": True},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["classification"], "severe")
        self.assertIn("severe", calculation.interpretation)

    def test_baron_endoscopic_score_returns_grade_label(self):
        calculation = ulcerative_colitis_baron_endoscopic_score(
            metadata("Baron内镜评分", "Baron Score"),
            {"grade": 2},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 2)
        self.assertEqual(calculation.unit, "grade")
        self.assertIn("moderate", calculation.interpretation)

    def test_west_haven_grade_three_is_severe_encephalopathy(self):
        calculation = west_haven_hepatic_encephalopathy_grade(
            metadata("肝性脑病West Haven分级", "West Haven Criteria"),
            {"grade": 3},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 3)
        self.assertEqual(calculation.unit, "grade")
        self.assertIn("severe", calculation.interpretation)

    def test_kings_college_criteria_acetaminophen_uses_ph_or_triad(self):
        calculation = kings_college_criteria_acute_liver_failure(
            metadata("King学院急性肝衰竭标准", "King's College Criteria"),
            {
                "etiology_group": "acetaminophen",
                "arterial_ph": 7.25,
                "inr": 2.0,
                "creatinine_mg_dl": 1.0,
                "encephalopathy_grade": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertTrue(calculation.value["criteria_met"])
        self.assertIn("poor prognosis", calculation.interpretation)

    def test_kings_college_criteria_non_acetaminophen_requires_three_minor_criteria(self):
        calculation = kings_college_criteria_acute_liver_failure(
            metadata("King学院急性肝衰竭标准", "King's College Criteria"),
            {
                "etiology_group": "non_acetaminophen",
                "age_years": 45,
                "unfavorable_etiology": True,
                "jaundice_to_encephalopathy_days": 8,
                "inr": 4.0,
                "bilirubin_mg_dl": 10,
            },
        )

        self.assertTrue(calculation.value["criteria_met"])
        self.assertEqual(calculation.value["minor_criteria_met"], 4)

    def test_forns_index_uses_log_formula_and_cutoffs(self):
        calculation = forns_index(
            metadata("Forns肝纤维化指数", "Forns Index"),
            {"age_years": 50, "ggt_u_l": 80, "cholesterol_mg_dl": 180, "platelets_10e9_l": 150},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 6.588, places=4)
        self.assertIn("indeterminate", calculation.interpretation)

    def test_adenoma_detection_rate_returns_percent(self):
        calculation = adenoma_detection_rate(
            metadata("腺瘤检出率", "Adenoma Detection Rate"),
            {"colonoscopies_with_at_least_one_adenoma": 92, "total_screening_colonoscopies": 400},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 23)
        self.assertEqual(calculation.unit, "%")

    def test_tokyo_cholangitis_severity_grade_three_when_organ_dysfunction_present(self):
        calculation = tokyo_guidelines_cholangitis_severity(
            metadata("东京急性胆管炎严重度分级", "Tokyo Guidelines Cholangitis Severity"),
            {
                "cardiovascular_dysfunction": False,
                "neurologic_dysfunction": False,
                "respiratory_dysfunction": False,
                "renal_dysfunction": True,
                "hepatic_dysfunction": False,
                "hematologic_dysfunction": False,
                "wbc_abnormal": False,
                "fever_39c_or_higher": False,
                "age_75_or_older": False,
                "bilirubin_mg_dl_5_or_higher": False,
                "albumin_low": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], "III")
        self.assertTrue(calculation.value["organ_dysfunction_present"])
        self.assertEqual(calculation.unit, "grade")
        self.assertIn("severe", calculation.interpretation)

    def test_tokyo_cholangitis_severity_grade_two_when_two_moderate_criteria_present(self):
        calculation = tokyo_guidelines_cholangitis_severity(
            metadata("东京急性胆管炎严重度分级", "Tokyo Guidelines Cholangitis Severity"),
            {
                "cardiovascular_dysfunction": False,
                "neurologic_dysfunction": False,
                "respiratory_dysfunction": False,
                "renal_dysfunction": False,
                "hepatic_dysfunction": False,
                "hematologic_dysfunction": False,
                "wbc_abnormal": True,
                "fever_39c_or_higher": False,
                "age_75_or_older": True,
                "bilirubin_mg_dl_5_or_higher": False,
                "albumin_low": False,
            },
        )

        self.assertEqual(calculation.value["grade"], "II")
        self.assertEqual(calculation.value["moderate_criteria_met"], 2)
        self.assertIn("moderate", calculation.interpretation)

    def test_tokyo_cholecystitis_severity_grade_three_when_organ_dysfunction_present(self):
        calculation = tokyo_guidelines_cholecystitis_severity(
            metadata("东京急性胆囊炎严重度分级", "Tokyo Guidelines Cholecystitis Severity"),
            {
                "cardiovascular_dysfunction": True,
                "neurologic_dysfunction": False,
                "respiratory_dysfunction": False,
                "renal_dysfunction": False,
                "hepatic_dysfunction": False,
                "hematologic_dysfunction": False,
                "wbc_over_18000": False,
                "palpable_tender_mass_right_upper_quadrant": False,
                "symptom_duration_over_72h": False,
                "marked_local_inflammation": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["grade"], "III")
        self.assertTrue(calculation.value["organ_dysfunction_present"])
        self.assertEqual(calculation.unit, "grade")

    def test_tokyo_cholecystitis_severity_grade_two_when_any_moderate_criterion_present(self):
        calculation = tokyo_guidelines_cholecystitis_severity(
            metadata("东京急性胆囊炎严重度分级", "Tokyo Guidelines Cholecystitis Severity"),
            {
                "cardiovascular_dysfunction": False,
                "neurologic_dysfunction": False,
                "respiratory_dysfunction": False,
                "renal_dysfunction": False,
                "hepatic_dysfunction": False,
                "hematologic_dysfunction": False,
                "wbc_over_18000": False,
                "palpable_tender_mass_right_upper_quadrant": False,
                "symptom_duration_over_72h": True,
                "marked_local_inflammation": False,
            },
        )

        self.assertEqual(calculation.value["grade"], "II")
        self.assertEqual(calculation.value["moderate_criteria_met"], 1)
        self.assertIn("moderate", calculation.interpretation)

    def test_full_rockall_score_uses_existing_full_clinical_and_endoscopic_components(self):
        calculation = full_rockall_score(
            metadata("完整Rockall评分", "Full Rockall Score"),
            {
                "age_years": 82,
                "shock": "hypotension",
                "comorbidity": "renal_liver_malignancy",
                "diagnosis": "upper_gi_malignancy",
                "stigmata": "blood_or_adherent_clot_or_visible_vessel",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 11)
        self.assertEqual(calculation.unit, "points")

    def test_ibs_sss_sums_five_prescored_zero_to_one_hundred_domains(self):
        calculation = ibs_severity_scoring_system(
            metadata("IBS严重度评分", "IBS Severity Scoring System"),
            {
                "abdominal_pain_severity": 70,
                "abdominal_pain_frequency": 80,
                "abdominal_distension": 65,
                "bowel_habit_dissatisfaction": 75,
                "life_interference": 60,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 350)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe", calculation.interpretation)

    def test_ibs_sss_rejects_domain_above_one_hundred(self):
        with self.assertRaises(ValueError):
            ibs_severity_scoring_system(
                metadata("IBS严重度评分", "IBS Severity Scoring System"),
                {
                    "abdominal_pain_severity": 101,
                    "abdominal_pain_frequency": 80,
                    "abdominal_distension": 65,
                    "bowel_habit_dissatisfaction": 75,
                    "life_interference": 60,
                },
            )

    def test_hisort_criteria_supports_diagnosis_from_typical_imaging_and_serology(self):
        calculation = hisort_autoimmune_pancreatitis_criteria(
            metadata("HISORt自身免疫性胰腺炎标准", "HISORt Criteria"),
            {
                "histology_diagnostic": False,
                "typical_pancreatic_imaging": True,
                "elevated_igg4": True,
                "atypical_pancreatic_imaging_after_negative_malignancy_workup": False,
                "other_organ_involvement": False,
                "steroid_response_after_negative_malignancy_workup": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertTrue(calculation.value["diagnostic_support"])
        self.assertTrue(calculation.value["typical_imaging_and_serology"])
        self.assertEqual(calculation.unit, "criteria")
        self.assertIn("supports autoimmune pancreatitis", calculation.interpretation)

    def test_tips_survival_probability_calculates_risk_score_and_survival(self):
        result = tips_survival_probability(
            metadata("TIPS生存预测", "TIPS Survival Prediction"),
            {
                "creatinine_mg_dl": 1.2,
                "bilirubin_mg_dl": 2.0,
                "inr": 1.5,
                "cause": "viral_or_other",
                "days": 90,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["risk_score"], 1.5332, places=4)
        self.assertAlmostEqual(result.value["survival_probability"], 0.5942, places=4)
        self.assertEqual(result.unit, "probability")
        self.assertIn("90-day", result.interpretation)

    def test_tips_survival_from_risk_score_uses_supported_baseline_day(self):
        result = tips_survival_from_risk_score(
            metadata("TIPS生存预测", "TIPS Survival From Risk Score"),
            {"risk_score": 1.127, "days": 365},
        )

        self.assertAlmostEqual(result.value, 0.5510, places=4)
        self.assertEqual(result.unit, "probability")

    def test_severe_lower_gi_bleeding_risk_score_stratifies_strate_risk(self):
        result = severe_lower_gi_bleeding_risk_score(
            metadata("严重下消化道出血风险", "Severe Lower GI Bleeding Risk"),
            {
                "pulse_100_or_more": True,
                "systolic_bp_115_or_less": True,
                "syncope": True,
                "nontender_abdomen": True,
                "rectal_bleeding_first_4_hours": True,
                "aspirin_use": True,
                "three_or_more_comorbidities": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 7)
        self.assertEqual(result.value["risk_percent"], 84)
        self.assertIn("high", result.interpretation)

    def test_bclc_hepatocellular_carcinoma_stage_maps_advanced_disease(self):
        result = bclc_hepatocellular_carcinoma_stage(
            metadata("BCLC肝癌分期", "BCLC Hepatocellular Carcinoma Stage"),
            {
                "ecog_performance_status": 1,
                "child_pugh_class": "A",
                "single_tumor": False,
                "tumor_count": 4,
                "largest_tumor_cm": 5,
                "portal_invasion": True,
                "extrahepatic_spread": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["stage"], "C")
        self.assertIn("advanced", result.interpretation)

    def test_bclc_hepatocellular_carcinoma_stage_identifies_very_early_stage(self):
        result = bclc_hepatocellular_carcinoma_stage(
            metadata("BCLC肝癌分期", "BCLC Hepatocellular Carcinoma Stage"),
            {
                "ecog_performance_status": 0,
                "child_pugh_class": "A",
                "single_tumor": True,
                "tumor_count": 1,
                "largest_tumor_cm": 1.8,
                "portal_invasion": False,
                "extrahepatic_spread": False,
            },
        )

        self.assertEqual(result.value["stage"], "0")
        self.assertIn("very early", result.interpretation)


if __name__ == "__main__":
    unittest.main()
