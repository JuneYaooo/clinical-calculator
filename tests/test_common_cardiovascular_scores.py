import unittest

from clinical_calculators.calculators.common.cardiovascular_scores import (
    ankle_brachial_index,
    adult_blood_pressure_category,
    aortic_stenosis_severity_grading,
    cha2ds2_vasc_score,
    ehra_atrial_fibrillation_symptom_scale,
    has_bled_score,
    mitral_regurgitation_severity_grading,
    rutherford_chronic_limb_ischemia_classification,
    simon_broome_familial_hypercholesterolemia_criteria,
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


class CommonCardiovascularScoresTest(unittest.TestCase):
    def test_cha2ds2_vasc_female_76_with_hypertension_and_diabetes_scores_five(self):
        calculation = cha2ds2_vasc_score(
            metadata(
                "房颤中风危险的CHA（2）DS（2）-VASc评分",
                "CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk",
            ),
            {
                "congestive_heart_failure": False,
                "hypertension": True,
                "age_years": 76,
                "diabetes": True,
                "stroke_tia_thromboembolism": False,
                "vascular_disease": False,
                "sex": "female",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high stroke risk", calculation.interpretation)
        self.assertIn("bleeding risk", calculation.interpretation)

    def test_cha2ds2_vasc_male_60_with_no_risks_scores_zero(self):
        calculation = cha2ds2_vasc_score(
            metadata(
                "房颤中风危险的CHA（2）DS（2）-VASc评分",
                "CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk",
            ),
            {
                "congestive_heart_failure": 0,
                "hypertension": 0,
                "age_years": 60,
                "diabetes": 0,
                "stroke_tia_thromboembolism": 0,
                "vascular_disease": 0,
                "sex": "male",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("low stroke risk", calculation.interpretation)

    def test_has_bled_all_false_age_60_scores_zero(self):
        calculation = has_bled_score(
            metadata("与HAS-BLED出血风险评分对应的临床特点", "HAS-BLED Bleeding Risk Score"),
            {
                "hypertension": False,
                "abnormal_renal_function": False,
                "abnormal_liver_function": False,
                "stroke_history": False,
                "bleeding_history_or_predisposition": False,
                "labile_inr": False,
                "age_years": 60,
                "drugs_predisposing_bleeding": False,
                "alcohol_use": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("not high bleeding risk", calculation.interpretation)

    def test_has_bled_age_70_hypertension_renal_and_alcohol_scores_four(self):
        calculation = has_bled_score(
            metadata("与HAS-BLED出血风险评分对应的临床特点", "HAS-BLED Bleeding Risk Score"),
            {
                "hypertension": 1,
                "abnormal_renal_function": 1,
                "abnormal_liver_function": 0,
                "stroke_history": 0,
                "bleeding_history_or_predisposition": 0,
                "labile_inr": 0,
                "age_years": 70,
                "drugs_predisposing_bleeding": 0,
                "alcohol_use": 1,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("high bleeding risk", calculation.interpretation)
        self.assertIn("not a reason alone to withhold anticoagulation", calculation.interpretation)

    def test_ankle_brachial_index_uses_higher_ankle_over_higher_brachial_pressure(self):
        result = ankle_brachial_index(
            metadata("ABI踝肱指数", "Ankle-Brachial Index"),
            {
                "left_dorsalis_pedis_sbp": 92,
                "left_posterior_tibial_sbp": 100,
                "right_brachial_sbp": 130,
                "left_brachial_sbp": 120,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0.7692)
        self.assertEqual(result.unit, "ratio")
        self.assertIn("abnormal", result.interpretation)

    def test_simon_broome_adult_high_ldl_with_tendon_xanthomas_is_definite_fh(self):
        calculation = simon_broome_familial_hypercholesterolemia_criteria(
            metadata("Simon Broome家族性高胆固醇血症标准", "Simon Broome Criteria"),
            {
                "age_years": 40,
                "ldl_cholesterol_mmol_l": 5.0,
                "tendon_xanthomas_patient_or_relative": True,
                "pathogenic_mutation": False,
                "family_history_premature_mi": False,
                "family_history_high_cholesterol": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 2)
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("definite familial hypercholesterolemia", calculation.interpretation)

    def test_simon_broome_child_high_total_cholesterol_with_family_history_is_possible_fh(self):
        calculation = simon_broome_familial_hypercholesterolemia_criteria(
            metadata("Simon Broome家族性高胆固醇血症标准", "Simon Broome Criteria"),
            {
                "age_years": 12,
                "total_cholesterol_mmol_l": 6.8,
                "tendon_xanthomas_patient_or_relative": False,
                "pathogenic_mutation": False,
                "family_history_premature_mi": True,
                "family_history_high_cholesterol": False,
            },
        )

        self.assertEqual(calculation.value, 1)
        self.assertIn("possible familial hypercholesterolemia", calculation.interpretation)

    def test_simon_broome_requires_cholesterol_threshold_before_family_history_classification(self):
        calculation = simon_broome_familial_hypercholesterolemia_criteria(
            metadata("Simon Broome家族性高胆固醇血症标准", "Simon Broome Criteria"),
            {
                "age_years": 40,
                "ldl_cholesterol_mmol_l": 4.8,
                "tendon_xanthomas_patient_or_relative": True,
                "pathogenic_mutation": False,
                "family_history_premature_mi": True,
                "family_history_high_cholesterol": True,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertIn("criteria not met", calculation.interpretation)

    def test_rutherford_chronic_limb_ischemia_classifies_minor_tissue_loss(self):
        calculation = rutherford_chronic_limb_ischemia_classification(
            metadata("Rutherford慢性肢体缺血分级", "Rutherford Chronic Limb Ischemia"),
            {"category": 5},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "category")
        self.assertIn("minor tissue loss", calculation.interpretation)

    def test_aortic_stenosis_severity_grading_uses_worst_echo_threshold(self):
        calculation = aortic_stenosis_severity_grading(
            metadata("主动脉瓣狭窄严重程度", "Aortic Stenosis Severity Grading"),
            {
                "peak_velocity_m_s": 3.2,
                "mean_gradient_mm_hg": 18,
                "aortic_valve_area_cm2": 0.9,
            },
        )

        self.assertEqual(calculation.value["severity"], "severe")
        self.assertTrue(calculation.value["discordant"])
        self.assertIn("severe", calculation.interpretation)

    def test_mitral_regurgitation_severity_grading_identifies_mild_when_all_markers_mild(self):
        calculation = mitral_regurgitation_severity_grading(
            metadata("二尖瓣反流严重程度", "Mitral Regurgitation Severity Grading"),
            {
                "vena_contracta_width_cm": 0.2,
                "eroa_cm2": 0.1,
                "regurgitant_volume_ml": 20,
                "regurgitant_fraction_percent": 20,
            },
        )

        self.assertEqual(calculation.value["severity"], "mild")
        self.assertFalse(calculation.value["discordant"])
        self.assertIn("mild", calculation.interpretation)

    def test_mitral_regurgitation_severity_grading_uses_severe_quantitative_thresholds(self):
        calculation = mitral_regurgitation_severity_grading(
            metadata("二尖瓣反流严重程度", "Mitral Regurgitation Severity Grading"),
            {
                "vena_contracta_width_cm": 0.4,
                "eroa_cm2": 0.42,
                "regurgitant_volume_ml": 45,
            },
        )

        self.assertEqual(calculation.value["severity"], "severe")
        self.assertTrue(calculation.value["discordant"])

    def test_ehra_atrial_fibrillation_symptom_scale_accepts_class_2b(self):
        calculation = ehra_atrial_fibrillation_symptom_scale(
            metadata("EHRA房颤症状分级", "EHRA AF Symptom Scale"),
            {"class": "2b"},
        )

        self.assertEqual(calculation.value, "2b")
        self.assertEqual(calculation.unit, "class")
        self.assertIn("troublesome symptoms", calculation.interpretation)

    def test_adult_blood_pressure_category_uses_aha_acc_thresholds(self):
        calculation = adult_blood_pressure_category(
            metadata("成人血压分级", "Adult Blood Pressure Category"),
            {"systolic_bp_mm_hg": 134, "diastolic_bp_mm_hg": 78},
        )
        crisis = adult_blood_pressure_category(
            metadata("成人血压分级", "Adult Blood Pressure Category"),
            {"systolic_bp_mm_hg": 181, "diastolic_bp_mm_hg": 70},
        )

        self.assertEqual(calculation.value["category"], "stage 1 hypertension")
        self.assertEqual(crisis.value["category"], "severe hypertension")
        self.assertEqual(calculation.unit, "classification")


if __name__ == "__main__":
    unittest.main()
