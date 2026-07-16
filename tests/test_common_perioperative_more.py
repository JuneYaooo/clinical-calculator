import unittest

from clinical_calculators.calculators.common.perioperative_more import (
    ariscat_postoperative_pulmonary_complications_risk,
    caprini_vte_risk_score,
    clavien_dindo_classification,
    comprehensive_complication_index,
    cormack_lehane_laryngoscopy_grade,
    eras_compliance_score,
    lemon_airway_assessment,
    p_possum_score,
    possum_score,
    rcri_perioperative_cardiac_risk_index,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="perioperative",
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


class CommonPerioperativeMoreTest(unittest.TestCase):
    def test_rcri_no_risk_factors_is_class_i(self):
        result = rcri_perioperative_cardiac_risk_index(
            metadata("RCRI围手术期心脏风险指数", "Revised Cardiac Risk Index"),
            {
                "high_risk_surgery": False,
                "ischemic_heart_disease": 0,
                "congestive_heart_failure": False,
                "cerebrovascular_disease": 0,
                "insulin_treated_diabetes": False,
                "creatinine_gt_2_mg_dl": 0,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("class I", result.interpretation)

    def test_rcri_three_risk_factors_is_class_iv(self):
        result = rcri_perioperative_cardiac_risk_index(
            metadata("RCRI围手术期心脏风险指数", "Revised Cardiac Risk Index"),
            {
                "high_risk_surgery": True,
                "ischemic_heart_disease": 1,
                "congestive_heart_failure": True,
                "cerebrovascular_disease": 0,
                "insulin_treated_diabetes": False,
                "creatinine_gt_2_mg_dl": 0,
            },
        )

        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("class IV", result.interpretation)

    def test_ariscat_low_risk_with_low_point_profile(self):
        result = ariscat_postoperative_pulmonary_complications_risk(
            metadata("ARISCAT术后肺部并发症风险", "ARISCAT Postoperative Pulmonary Complications Risk"),
            {
                "age_years": 50,
                "spo2_percent": 96,
                "respiratory_infection_last_month": False,
                "preoperative_anemia_hb_le_10": 0,
                "surgical_incision": "peripheral",
                "duration_hours": 1.99,
                "emergency_surgery": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("low", result.interpretation)

    def test_ariscat_intermediate_risk_at_lower_threshold(self):
        result = ariscat_postoperative_pulmonary_complications_risk(
            metadata("ARISCAT术后肺部并发症风险", "ARISCAT Postoperative Pulmonary Complications Risk"),
            {
                "age_years": 51,
                "spo2_percent": 91,
                "respiratory_infection_last_month": False,
                "preoperative_anemia_hb_le_10": 0,
                "surgical_incision": "upper_abdominal",
                "duration_hours": 1,
                "emergency_surgery": False,
            },
        )

        self.assertEqual(result.value, 26)
        self.assertEqual(result.unit, "points")
        self.assertIn("intermediate", result.interpretation)

    def test_ariscat_high_risk_profile(self):
        result = ariscat_postoperative_pulmonary_complications_risk(
            metadata("ARISCAT术后肺部并发症风险", "ARISCAT Postoperative Pulmonary Complications Risk"),
            {
                "age_years": 81,
                "spo2_percent": 90,
                "respiratory_infection_last_month": True,
                "preoperative_anemia_hb_le_10": 1,
                "surgical_incision": "intrathoracic",
                "duration_hours": 3.1,
                "emergency_surgery": True,
            },
        )

        self.assertEqual(result.value, 123)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_ariscat_rejects_unknown_incision(self):
        with self.assertRaises(ValueError):
            ariscat_postoperative_pulmonary_complications_risk(
                metadata("ARISCAT术后肺部并发症风险", "ARISCAT Postoperative Pulmonary Complications Risk"),
                {
                    "age_years": 60,
                    "spo2_percent": 96,
                    "respiratory_infection_last_month": False,
                    "preoperative_anemia_hb_le_10": False,
                    "surgical_incision": "laparoscopic",
                    "duration_hours": 1,
                    "emergency_surgery": False,
                },
            )

    def test_caprini_zero_points_is_very_low(self):
        result = caprini_vte_risk_score(
            metadata("Caprini静脉血栓风险评分", "Caprini VTE Risk Score"),
            {"risk_factor_points": []},
        )

        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("very low", result.interpretation)

    def test_caprini_valid_point_values_sum_to_high_risk(self):
        result = caprini_vte_risk_score(
            metadata("Caprini静脉血栓风险评分", "Caprini VTE Risk Score"),
            {"risk_factor_points": [1, 2, 3, 5]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 11)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_caprini_rejects_uncoded_point_value(self):
        with self.assertRaises(ValueError):
            caprini_vte_risk_score(
                metadata("Caprini静脉血栓风险评分", "Caprini VTE Risk Score"),
                {"risk_factor_points": [1, 4]},
            )

    def test_clavien_dindo_grade_ii_therapy_is_grade_ii(self):
        calculation = clavien_dindo_classification(
            metadata("Clavien-Dindo手术并发症分级", "Clavien-Dindo Classification"),
            {
                "death": False,
                "icu_management": False,
                "organ_dysfunction": "none",
                "intervention": "none",
                "grade_ii_therapy": True,
                "disability_at_discharge": False,
            },
        )

        self.assertEqual(calculation.value["grade"], "II")
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("Grade II", calculation.interpretation)

    def test_clavien_dindo_prioritizes_death_as_grade_v_with_disability_suffix(self):
        calculation = clavien_dindo_classification(
            metadata("Clavien-Dindo手术并发症分级", "Clavien-Dindo Classification"),
                {
                    "death": True,
                    "icu_management": True,
                    "organ_dysfunction": "multiple",
                    "intervention": "with_general_anesthesia",
                    "grade_ii_therapy": True,
                    "disability_at_discharge": True,
                },
        )

        self.assertEqual(calculation.value["grade"], "V")
        self.assertTrue(calculation.value["disability_suffix"])
        self.assertIn("Grade V", calculation.interpretation)

    def test_clavien_dindo_rejects_icu_without_organ_dysfunction(self):
        with self.assertRaises(ValueError):
            clavien_dindo_classification(
                metadata("Clavien-Dindo手术并发症分级", "Clavien-Dindo Classification"),
                {
                    "death": False,
                    "icu_management": True,
                    "organ_dysfunction": "none",
                    "intervention": "none",
                    "grade_ii_therapy": False,
                    "disability_at_discharge": False,
                },
            )

    def test_lemon_airway_assessment_counts_five_coded_risk_features(self):
        calculation = lemon_airway_assessment(
            metadata("LEMON困难气道评估", "LEMON Airway Assessment"),
            {
                "look_external_abnormal": True,
                "evaluate_332_abnormal": False,
                "mallampati_ge_3": True,
                "obstruction_present": False,
                "neck_mobility_limited": True,
            },
        )

        self.assertEqual(calculation.value, 3)
        self.assertEqual(calculation.unit, "features")
        self.assertIn("3 of 5", calculation.interpretation)

    def test_lemon_airway_assessment_rejects_non_boolean_component(self):
        with self.assertRaises(ValueError):
            lemon_airway_assessment(
                metadata("LEMON困难气道评估", "LEMON Airway Assessment"),
                {
                    "look_external_abnormal": True,
                    "evaluate_332_abnormal": "yes",
                    "mallampati_ge_3": False,
                    "obstruction_present": False,
                    "neck_mobility_limited": False,
                },
            )

    def test_cormack_lehane_grade_four_marks_difficult_laryngoscopy(self):
        calculation = cormack_lehane_laryngoscopy_grade(
            metadata("Cormack-Lehane喉镜分级", "Cormack-Lehane Classification"),
            {"grade": 4},
        )

        self.assertEqual(calculation.value["grade"], 4)
        self.assertTrue(calculation.value["difficult_laryngoscopy"])
        self.assertEqual(calculation.unit, "grade")
        self.assertIn("Grade 4", calculation.interpretation)

    def test_cormack_lehane_rejects_out_of_range_grade(self):
        with self.assertRaises(ValueError):
            cormack_lehane_laryngoscopy_grade(
                metadata("Cormack-Lehane喉镜分级", "Cormack-Lehane Classification"),
                {"grade": 5},
            )

    def test_possum_uses_precoded_component_points_for_morbidity_and_mortality(self):
        calculation = possum_score(
            metadata("POSSUM评分", "POSSUM Score"),
            {
                "physiological_component_points": [1] * 12,
                "operative_component_points": [1] * 6,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["physiological_score"], 12)
        self.assertEqual(calculation.value["operative_score"], 6)
        self.assertAlmostEqual(calculation.value["morbidity_risk_percent"], 5.5, places=1)
        self.assertAlmostEqual(calculation.value["mortality_risk_percent"], 1.1, places=1)

    def test_p_possum_uses_portsmouth_mortality_equation(self):
        calculation = p_possum_score(
            metadata("P-POSSUM评分", "Portsmouth POSSUM Score"),
            {
                "physiological_component_points": [4] * 12,
                "operative_component_points": [4] * 6,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["physiological_score"], 48)
        self.assertEqual(calculation.value["operative_score"], 24)
        self.assertAlmostEqual(calculation.value["mortality_risk_percent"], 94.1, places=1)

    def test_comprehensive_complication_index_combines_clavien_dindo_grades(self):
        calculation = comprehensive_complication_index(
            metadata("综合并发症指数", "Comprehensive Complication Index"),
            {"complication_grades": ["I", "II", "IIIb"]},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value["score"], 40.6, places=1)
        self.assertEqual(calculation.unit, "points")

    def test_eras_compliance_score_counts_applicable_completed_items(self):
        calculation = eras_compliance_score(
            metadata("ERAS依从性评分", "ERAS Compliance Score"),
            {"items": [True] * 12 + [False] * 3 + [None]},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["completed_items"], 12)
        self.assertEqual(calculation.value["applicable_items"], 15)
        self.assertEqual(calculation.value["compliance_percent"], 80.0)
        self.assertIn("high", calculation.interpretation.lower())


if __name__ == "__main__":
    unittest.main()
