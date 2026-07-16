import unittest

from clinical_calculators.calculators.common.heme_rheum_scores import (
    acr_eular_2010_rheumatoid_arthritis_classification,
    acr_eular_2015_gout_classification,
    adjusted_gapss_antiphospholipid_syndrome_risk,
    asdas_ankylosing_spondylitis_disease_activity,
    basdai_ankylosing_spondylitis,
    basfi_ankylosing_spondylitis,
    cdai_rheumatoid_arthritis,
    cll_international_prognostic_index,
    das28_esr,
    dapsa_psoriatic_arthritis,
    dipss_myelofibrosis,
    eln_2022_aml_risk_stratification,
    essdai_sjogrens_disease_activity,
    hct_ci,
    heparin_induced_thrombocytopenia_4ts_score,
    isth_bleeding_assessment_tool_prescored,
    isth_overt_dic_score,
    jaam_dic_score,
    polycythemia_vera_thrombosis_risk,
    rapid3_rheumatoid_arthritis,
    revised_international_prognostic_scoring_system_mds,
    revised_international_staging_system_multiple_myeloma,
    sdai_rheumatoid_arthritis,
    sledai_2k_disease_activity,
    sle_2019_eular_acr_classification,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="hematology_rheumatology",
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


class CommonHemeRheumScoresTest(unittest.TestCase):
    def test_isth_bat_prescored_uses_adult_female_abnormal_threshold(self):
        result = isth_bleeding_assessment_tool_prescored(
            metadata("ISTH出血评估工具", "ISTH Bleeding Assessment Tool"),
            {"total_score": 6, "sex": "female", "pediatric": False},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 6)
        self.assertTrue(result.value["abnormal_screen"])
        self.assertEqual(result.unit, "points")
        self.assertIn("abnormal", result.interpretation)

    def test_isth_bat_prescored_uses_pediatric_threshold_without_sex(self):
        result = isth_bleeding_assessment_tool_prescored(
            metadata("ISTH出血评估工具", "ISTH Bleeding Assessment Tool"),
            {"total_score": 3, "pediatric": True},
        )

        self.assertTrue(result.value["abnormal_screen"])
        self.assertEqual(result.value["threshold"], 3)

    def test_isth_bat_prescored_rejects_negative_total_score(self):
        with self.assertRaises(ValueError):
            isth_bleeding_assessment_tool_prescored(
                metadata("ISTH出血评估工具", "ISTH Bleeding Assessment Tool"),
                {"total_score": -1, "sex": "male", "pediatric": False},
            )

    def test_4ts_score_eight_is_high_probability(self):
        result = heparin_induced_thrombocytopenia_4ts_score(
            metadata(
                "肝素诱导的血小板减少（4-T分数）的验前概率",
                "4Ts Score for Heparin-Induced Thrombocytopenia",
            ),
            {
                "thrombocytopenia": 2,
                "timing": 2,
                "thrombosis": 2,
                "other_causes": 2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("high probability", result.interpretation)

    def test_4ts_score_zero_is_low_probability(self):
        result = heparin_induced_thrombocytopenia_4ts_score(
            metadata(
                "肝素诱导的血小板减少（4-T分数）的验前概率",
                "4Ts Score for Heparin-Induced Thrombocytopenia",
            ),
            {
                "thrombocytopenia": 0,
                "timing": 0,
                "thrombosis": 0,
                "other_causes": 0,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low probability", result.interpretation)

    def test_4ts_rejects_out_of_range_coded_integer(self):
        with self.assertRaises(ValueError):
            heparin_induced_thrombocytopenia_4ts_score(
                metadata(
                    "肝素诱导的血小板减少（4-T分数）的验前概率",
                    "4Ts Score for Heparin-Induced Thrombocytopenia",
                ),
                {
                    "thrombocytopenia": 3,
                    "timing": 0,
                    "thrombosis": 0,
                    "other_causes": 0,
                },
            )

    def test_das28_esr_known_example_is_high_activity(self):
        result = das28_esr(
            metadata("DAS28类风湿活动度", "DAS28-ESR Rheumatoid Arthritis Disease Activity"),
            {
                "tender_joint_count_28": 10,
                "swollen_joint_count_28": 8,
                "esr_mm_hr": 30,
                "patient_global_health": 50,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 5.6437, places=4)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_dapsa_sums_joint_counts_patient_scores_and_crp(self):
        result = dapsa_psoriatic_arthritis(
            metadata("DAPSA银屑病关节炎活动度", "Disease Activity in Psoriatic Arthritis"),
            {
                "tender_joint_count_68": 12,
                "swollen_joint_count_66": 8,
                "patient_global_assessment": 6.5,
                "patient_pain": 5.5,
                "crp_mg_dl": 1.2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 33.2, places=4)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_cdai_score_twenty_seven_is_high_activity(self):
        result = cdai_rheumatoid_arthritis(
            metadata("类风湿临床疾病活动指数", "Clinical Disease Activity Index"),
            {
                "tender_joint_count_28": 10,
                "swollen_joint_count_28": 8,
                "patient_global_assessment": 5,
                "provider_global_assessment": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 27)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_adjusted_gapss_all_true_is_seventeen_points(self):
        result = adjusted_gapss_antiphospholipid_syndrome_risk(
            metadata(
                "调整后GAPSS抗磷脂综合征风险",
                "Adjusted GAPSS Antiphospholipid Syndrome Risk",
            ),
            {
                "anticardiolipin": True,
                "anti_beta2_glycoprotein_i": True,
                "lupus_anticoagulant": True,
                "hyperlipidemia": True,
                "arterial_hypertension": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 17)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher thrombotic risk", result.interpretation)

    def test_adjusted_gapss_rejects_non_boolean_code(self):
        with self.assertRaises(ValueError):
            adjusted_gapss_antiphospholipid_syndrome_risk(
                metadata(
                    "调整后GAPSS抗磷脂综合征风险",
                    "Adjusted GAPSS Antiphospholipid Syndrome Risk",
                ),
                {
                    "anticardiolipin": 2,
                    "anti_beta2_glycoprotein_i": False,
                    "lupus_anticoagulant": False,
                    "hyperlipidemia": False,
                    "arterial_hypertension": False,
                },
            )

    def test_isth_overt_dic_score_five_is_compatible_with_overt_dic(self):
        result = isth_overt_dic_score(
            metadata("ISTH弥散性血管内凝血评分", "ISTH DIC Score"),
            {
                "platelets_10e9_l": 45,
                "fibrin_marker_increase": "strong",
                "pt_prolongation_seconds": 4,
                "fibrinogen_g_l": 1.2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("overt DIC", result.interpretation)

    def test_isth_overt_dic_rejects_unknown_fibrin_marker_category(self):
        with self.assertRaises(ValueError):
            isth_overt_dic_score(
                metadata("ISTH弥散性血管内凝血评分", "ISTH DIC Score"),
                {
                    "platelets_10e9_l": 120,
                    "fibrin_marker_increase": "mild",
                    "pt_prolongation_seconds": 1,
                    "fibrinogen_g_l": 2.0,
                },
            )

    def test_sdai_score_uses_joint_counts_globals_and_crp(self):
        result = sdai_rheumatoid_arthritis(
            metadata("类风湿简化疾病活动指数", "Simplified Disease Activity Index"),
            {
                "tender_joint_count_28": 10,
                "swollen_joint_count_28": 8,
                "patient_global_assessment": 5,
                "provider_global_assessment": 4,
                "crp_mg_dl": 1.2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 28.2, places=4)
        self.assertIn("high", result.interpretation)

    def test_basdai_averages_first_four_and_morning_stiffness_pair(self):
        result = basdai_ankylosing_spondylitis(
            metadata("强直性脊柱炎疾病活动指数", "Bath Ankylosing Spondylitis Disease Activity Index"),
            {"items": [6, 5, 4, 5, 8, 6]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5.4)
        self.assertIn("active", result.interpretation)

    def test_basfi_averages_ten_function_items(self):
        result = basfi_ankylosing_spondylitis(
            metadata("强直性脊柱炎功能指数", "Bath Ankylosing Spondylitis Functional Index"),
            {"items": [2, 3, 4, 5, 6, 2, 3, 4, 5, 6]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "score")

    def test_cll_ipi_counts_five_risk_domains(self):
        result = cll_international_prognostic_index(
            metadata("CLL国际预后指数", "CLL International Prognostic Index"),
            {
                "age_years": 70,
                "clinical_stage": "rai_i_iv",
                "beta2_microglobulin_mg_l": 4.2,
                "ighv_unmutated": True,
                "del17p_or_tp53_mutated": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("very high", result.interpretation)

    def test_rapid3_sums_three_patient_reported_components(self):
        result = rapid3_rheumatoid_arthritis(
            metadata("RAPID3类风湿疾病活动指数", "RAPID3"),
            {"physical_function": 4, "pain": 5, "patient_global": 6},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 15)
        self.assertIn("high", result.interpretation)

    def test_2010_acr_eular_ra_classification_uses_component_points(self):
        result = acr_eular_2010_rheumatoid_arthritis_classification(
            metadata("2010 ACR/EULAR类风湿关节炎分类标准", "2010 ACR/EULAR RA Classification"),
            {
                "joint_involvement": 5,
                "serology": 3,
                "acute_phase_reactants": 1,
                "symptom_duration": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 10)
        self.assertTrue(result.value["definite_ra_classification"])

    def test_2019_sle_classification_requires_ana_entry_and_ten_points(self):
        result = sle_2019_eular_acr_classification(
            metadata("2019 EULAR/ACR SLE分类标准", "2019 EULAR/ACR SLE Classification"),
            {"ana_positive": True, "weighted_domain_scores": [6, 4], "clinical_criterion_present": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 10)
        self.assertTrue(result.value["classified_as_sle"])

    def test_2019_sle_classification_requires_at_least_one_clinical_criterion(self):
        result = sle_2019_eular_acr_classification(
            metadata("2019 EULAR/ACR SLE分类标准", "2019 EULAR/ACR SLE Classification"),
            {
                "ana_positive": True,
                "weighted_domain_scores": [10],
                "clinical_criterion_present": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 10)
        self.assertFalse(result.value["classified_as_sle"])

    def test_asdas_crp_uses_official_weighted_formula(self):
        result = asdas_ankylosing_spondylitis_disease_activity(
            metadata("强直性脊柱炎疾病活动评分", "ASDAS"),
            {
                "inflammatory_back_pain": 6,
                "morning_stiffness": 4,
                "patient_global": 5,
                "peripheral_pain_swelling": 3,
                "crp_mg_l": 10,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 3.1108, places=4)
        self.assertEqual(result.unit, "score")
        self.assertIn("high", result.interpretation)

    def test_asdas_esr_uses_official_weighted_formula(self):
        result = asdas_ankylosing_spondylitis_disease_activity(
            metadata("强直性脊柱炎疾病活动评分", "ASDAS"),
            {
                "inflammatory_back_pain": 6,
                "morning_stiffness": 4,
                "patient_global": 5,
                "peripheral_pain_swelling": 3,
                "esr_mm_hr": 30,
            },
        )

        self.assertAlmostEqual(result.value, 3.1684, places=4)
        self.assertIn("high", result.interpretation)

    def test_gout_classification_uses_prescored_acr_eular_domains(self):
        result = acr_eular_2015_gout_classification(
            metadata("2015 ACR/EULAR痛风分类标准", "2015 ACR/EULAR Gout Classification"),
            {
                "entry_criterion": True,
                "sufficient_msu_crystals": False,
                "clinical_pattern": 2,
                "episode_characteristics": 2,
                "time_course": 2,
                "tophus": 4,
                "serum_urate": 3,
                "synovial_fluid": 0,
                "imaging_urate_deposition": 4,
                "imaging_gout_erosion": 4,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 21)
        self.assertTrue(result.value["classified_as_gout"])
        self.assertIn("classified", result.interpretation)

    def test_gout_classification_sufficient_msu_crystals_classifies_directly(self):
        result = acr_eular_2015_gout_classification(
            metadata("2015 ACR/EULAR痛风分类标准", "2015 ACR/EULAR Gout Classification"),
            {"entry_criterion": True, "sufficient_msu_crystals": True},
        )

        self.assertIsNone(result.value["score"])
        self.assertTrue(result.value["classified_as_gout"])

    def test_gout_classification_rejects_invalid_prescored_domain(self):
        with self.assertRaises(ValueError):
            acr_eular_2015_gout_classification(
                metadata("2015 ACR/EULAR痛风分类标准", "2015 ACR/EULAR Gout Classification"),
                {
                    "entry_criterion": True,
                    "sufficient_msu_crystals": False,
                    "clinical_pattern": 3,
                    "episode_characteristics": 0,
                    "time_course": 0,
                    "tophus": 0,
                    "serum_urate": 0,
                    "synovial_fluid": 0,
                    "imaging_urate_deposition": 0,
                    "imaging_gout_erosion": 0,
                },
            )

    def test_ipss_r_mds_scores_very_high_risk_from_public_point_rules(self):
        result = revised_international_prognostic_scoring_system_mds(
            metadata("IPSS-R骨髓增生异常综合征", "Revised International Prognostic Scoring System"),
            {
                "cytogenetic_risk": "very_poor",
                "bone_marrow_blast_percent": 11,
                "hemoglobin_g_dl": 7.5,
                "platelets_10e9_l": 45,
                "absolute_neutrophil_count_10e9_l": 0.5,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("very high", result.interpretation)

    def test_ipss_r_mds_rejects_unknown_cytogenetic_category(self):
        with self.assertRaises(ValueError):
            revised_international_prognostic_scoring_system_mds(
                metadata("IPSS-R骨髓增生异常综合征", "Revised International Prognostic Scoring System"),
                {
                    "cytogenetic_risk": "unknown",
                    "bone_marrow_blast_percent": 1,
                    "hemoglobin_g_dl": 12,
                    "platelets_10e9_l": 200,
                    "absolute_neutrophil_count_10e9_l": 2,
                },
            )

    def test_r_iss_multiple_myeloma_stage_three_uses_iss_ldh_and_cytogenetics(self):
        result = revised_international_staging_system_multiple_myeloma(
            metadata("R-ISS多发性骨髓瘤分期", "Revised International Staging System"),
            {
                "beta2_microglobulin_mg_l": 6,
                "albumin_g_dl": 3.0,
                "ldh_above_upper_limit_normal": True,
                "high_risk_cytogenetics": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "III")
        self.assertEqual(result.unit, "stage")
        self.assertIn("stage III", result.interpretation)

    def test_r_iss_multiple_myeloma_stage_one_requires_iss_one_and_no_adverse_features(self):
        result = revised_international_staging_system_multiple_myeloma(
            metadata("R-ISS多发性骨髓瘤分期", "Revised International Staging System"),
            {
                "beta2_microglobulin_mg_l": 3.0,
                "albumin_g_dl": 4.0,
                "ldh_above_upper_limit_normal": False,
                "high_risk_cytogenetics": False,
            },
        )

        self.assertEqual(result.value, "I")
        self.assertIn("stage I", result.interpretation)

    def test_sledai_2k_uses_coded_weight_counts_without_item_text(self):
        result = sledai_2k_disease_activity(
            metadata("SLEDAI狼疮活动指数", "SLE Disease Activity Index"),
            {"weight_8_count": 2, "weight_4_count": 3, "weight_2_count": 1, "weight_1_count": 2},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 32)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_sledai_2k_rejects_negative_weight_count(self):
        with self.assertRaises(ValueError):
            sledai_2k_disease_activity(
                metadata("SLEDAI狼疮活动指数", "SLE Disease Activity Index"),
                {"weight_8_count": -1, "weight_4_count": 0, "weight_2_count": 0, "weight_1_count": 0},
            )

    def test_essdai_uses_prescored_domain_activity_levels_and_weights(self):
        result = essdai_sjogrens_disease_activity(
            metadata("干燥综合征疾病活动指数", "EULAR Sjogren's Syndrome Disease Activity Index"),
            {
                "constitutional": 1,
                "lymphadenopathy": 0,
                "glandular": 0,
                "articular": 0,
                "cutaneous": 0,
                "pulmonary": 2,
                "renal": 0,
                "muscular": 3,
                "peripheral_nervous_system": 0,
                "central_nervous_system": 0,
                "hematological": 0,
                "biological": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 32)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_essdai_rejects_domain_level_above_high_activity(self):
        with self.assertRaises(ValueError):
            essdai_sjogrens_disease_activity(
                metadata("干燥综合征疾病活动指数", "EULAR Sjogren's Syndrome Disease Activity Index"),
                {
                    "constitutional": 4,
                    "lymphadenopathy": 0,
                    "glandular": 0,
                    "articular": 0,
                    "cutaneous": 0,
                    "pulmonary": 0,
                    "renal": 0,
                    "muscular": 0,
                    "peripheral_nervous_system": 0,
                    "central_nervous_system": 0,
                    "hematological": 0,
                    "biological": 0,
                },
            )

    def test_hct_ci_sums_public_comorbidity_weights(self):
        result = hct_ci(
            metadata("造血细胞移植合并症指数", "Hematopoietic Cell Transplantation-Comorbidity Index"),
            {
                "arrhythmia": True,
                "cardiac": False,
                "inflammatory_bowel_disease": False,
                "diabetes": True,
                "cerebrovascular_disease": False,
                "psychiatric_disturbance": False,
                "mild_hepatic": False,
                "obesity": False,
                "infection": True,
                "rheumatologic": False,
                "peptic_ulcer": False,
                "moderate_or_severe_renal": True,
                "moderate_pulmonary": False,
                "prior_solid_tumor": False,
                "heart_valve_disease": False,
                "severe_pulmonary": True,
                "moderate_or_severe_hepatic": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 11)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_hct_ci_rejects_mutually_exclusive_pulmonary_categories(self):
        with self.assertRaises(ValueError):
            hct_ci(
                metadata("造血细胞移植合并症指数", "Hematopoietic Cell Transplantation-Comorbidity Index"),
                {
                    "arrhythmia": False,
                    "cardiac": False,
                    "inflammatory_bowel_disease": False,
                    "diabetes": False,
                    "cerebrovascular_disease": False,
                    "psychiatric_disturbance": False,
                    "mild_hepatic": False,
                    "obesity": False,
                    "infection": False,
                    "rheumatologic": False,
                    "peptic_ulcer": False,
                    "moderate_or_severe_renal": False,
                    "moderate_pulmonary": True,
                    "prior_solid_tumor": False,
                    "heart_valve_disease": False,
                    "severe_pulmonary": True,
                    "moderate_or_severe_hepatic": False,
                },
            )

    def test_jaam_dic_score_eight_meets_dic_threshold(self):
        result = jaam_dic_score(
            metadata("JAAM急性期DIC评分", "JAAM DIC Score"),
            {
                "sirs_criteria_count": 3,
                "platelets_10e9_l": 70,
                "platelet_decrease_percent_24h": 10,
                "fdp_mcg_ml": 30,
                "pt_ratio": 1.3,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertEqual(result.unit, "points")
        self.assertIn("DIC", result.interpretation)

    def test_jaam_dic_rejects_negative_fdp(self):
        with self.assertRaises(ValueError):
            jaam_dic_score(
                metadata("JAAM急性期DIC评分", "JAAM DIC Score"),
                {
                    "sirs_criteria_count": 0,
                    "platelets_10e9_l": 150,
                    "platelet_decrease_percent_24h": 0,
                    "fdp_mcg_ml": -1,
                    "pt_ratio": 1,
                },
            )

    def test_dipss_myelofibrosis_scores_high_risk(self):
        result = dipss_myelofibrosis(
            metadata("骨髓纤维化DIPSS评分", "Dynamic International Prognostic Scoring System"),
            {
                "age_years": 70,
                "hemoglobin_g_dl": 9.5,
                "leukocyte_count_10e9_l": 30,
                "circulating_blast_percent": 1,
                "constitutional_symptoms": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_dipss_myelofibrosis_zero_is_low_risk(self):
        result = dipss_myelofibrosis(
            metadata("骨髓纤维化DIPSS评分", "Dynamic International Prognostic Scoring System"),
            {
                "age_years": 60,
                "hemoglobin_g_dl": 12,
                "leukocyte_count_10e9_l": 10,
                "circulating_blast_percent": 0,
                "constitutional_symptoms": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low risk", result.interpretation)

    def test_eln_2022_aml_favorable_for_npm1_without_flt3_itd(self):
        result = eln_2022_aml_risk_stratification(
            metadata("ELN急性髓系白血病风险分层", "ELN AML Risk Stratification"),
            {
                "favorable_recurrent_genetic_abnormality": False,
                "mutated_npm1": True,
                "flt3_itd": False,
                "bzip_in_frame_cebpa": False,
                "t_9_11": False,
                "adverse_risk_cytogenetics": False,
                "adverse_risk_gene_mutation": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "favorable")
        self.assertEqual(result.unit, "risk")
        self.assertIn("favorable", result.interpretation)

    def test_eln_2022_aml_adverse_cytogenetics_override_npm1(self):
        result = eln_2022_aml_risk_stratification(
            metadata("ELN急性髓系白血病风险分层", "ELN AML Risk Stratification"),
            {
                "favorable_recurrent_genetic_abnormality": False,
                "mutated_npm1": True,
                "flt3_itd": False,
                "bzip_in_frame_cebpa": False,
                "t_9_11": False,
                "adverse_risk_cytogenetics": True,
                "adverse_risk_gene_mutation": False,
            },
        )

        self.assertEqual(result.value, "adverse")
        self.assertIn("adverse", result.interpretation)

    def test_polycythemia_vera_thrombosis_risk_high_with_age_over_sixty(self):
        result = polycythemia_vera_thrombosis_risk(
            metadata("真性红细胞增多症血栓风险", "Polycythemia Vera Thrombosis Risk"),
            {"age_years": 61, "prior_thrombosis": False},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "high")
        self.assertEqual(result.unit, "risk")
        self.assertIn("high", result.interpretation)

    def test_polycythemia_vera_thrombosis_risk_low_without_age_or_thrombosis(self):
        result = polycythemia_vera_thrombosis_risk(
            metadata("真性红细胞增多症血栓风险", "Polycythemia Vera Thrombosis Risk"),
            {"age_years": 45, "prior_thrombosis": False},
        )

        self.assertEqual(result.value, "low")
        self.assertIn("low", result.interpretation)


if __name__ == "__main__":
    unittest.main()
