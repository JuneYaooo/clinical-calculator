import unittest

from clinical_calculators.calculators.common.pediatric_neuro_radiation_more import (
    biologically_effective_dose,
    corrected_csf_wbc_traumatic_tap,
    equivalent_dose_2gy_fractions,
    cdc_boys_bmi_for_age_percentile_from_lms,
    cdc_boys_bmi_for_age_z_from_lms,
    cdc_boys_weight_for_age_percentile_from_lms,
    cdc_boys_weight_for_age_z_from_lms,
    cdc_girls_bmi_for_age_percentile_from_lms,
    cdc_girls_bmi_for_age_z_from_lms,
    cdc_girls_weight_for_age_percentile_from_lms,
    cdc_girls_weight_for_age_z_from_lms,
    neonatal_respiratory_severity_score,
    percentile_from_z_score,
    bedside_schwartz_egfr,
    who_head_circumference_for_age_percentile_from_lms,
    who_head_circumference_for_age_z_from_lms,
    who_infant_length_for_age_percentile_from_lms,
    who_infant_length_for_age_z_from_lms,
    who_infant_weight_for_age_percentile_from_lms,
    who_infant_weight_for_age_z_from_lms,
    who_weight_for_length_percentile_from_lms,
    who_weight_for_length_z_from_lms,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str = "calculator") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_cn}",
        category="common",
        subspecialty="",
        scenario="",
        name_cn=name_cn,
        name_en="Calculator",
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


class CommonPediatricNeuroRadiationMoreTest(unittest.TestCase):
    def test_percentile_from_z_score_matches_standard_normal_distribution(self):
        calculation = percentile_from_z_score(metadata("Z分数转百分位"), {"z_score": 1})

        self.assertAlmostEqual(calculation.value, 84.1345, places=4)
        self.assertEqual(calculation.unit, "percentile")

    def test_bedside_schwartz_egfr(self):
        result = bedside_schwartz_egfr(
            metadata("Schwartz儿童eGFR"), {"height_cm": 120, "serum_creatinine_mg_dl": 0.6}
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 82.6, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m2")

    def test_neonatal_respiratory_severity_score_multiplies_map_by_fractional_fio2(self):
        result = neonatal_respiratory_severity_score(
            metadata("新生儿呼吸支持风险指数"), {"mean_airway_pressure_cm_h2o": 12, "fio2": 0.4}
        )

        self.assertAlmostEqual(result.value, 4.8, places=4)
        self.assertEqual(result.unit, "cm H2O")

    def test_corrected_csf_wbc_traumatic_tap_subtracts_blood_contamination(self):
        result = corrected_csf_wbc_traumatic_tap(
            metadata("血液污染脑脊液的白细胞计数校正"),
            {
                "csf_wbc_per_uL": 100,
                "blood_wbc_10e3_per_uL": 10,
                "csf_rbc_per_uL": 100000,
                "blood_rbc_10e6_per_uL": 5,
            },
        )

        self.assertAlmostEqual(result.value, 99.8, places=4)
        self.assertEqual(result.unit, "cells/uL")

    def test_eqd2_compares_fractionation_to_2gy_fractions(self):
        result = equivalent_dose_2gy_fractions(
            metadata("等效2Gy分割剂量"),
            {"total_dose_gy": 60, "dose_per_fraction_gy": 3, "alpha_beta_gy": 10},
        )

        self.assertAlmostEqual(result.value, 65, places=4)
        self.assertEqual(result.unit, "Gy")

    def test_bed_uses_linear_quadratic_model(self):
        result = biologically_effective_dose(
            metadata("生物有效剂量"),
            {"total_dose_gy": 60, "dose_per_fraction_gy": 2, "alpha_beta_gy": 10},
        )

        self.assertAlmostEqual(result.value, 72, places=4)
        self.assertEqual(result.unit, "Gy")

    def test_who_infant_length_for_age_z_from_lms_uses_box_cox_lms(self):
        result = who_infant_length_for_age_z_from_lms(
            metadata("WHO婴儿身长年龄别Z值"),
            {"length_cm": 55, "l": 1, "m": 50, "s": 0.1},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 1.0, places=4)
        self.assertEqual(result.unit, "z-score")

    def test_who_infant_length_for_age_percentile_from_lms_converts_z_to_percentile(self):
        result = who_infant_length_for_age_percentile_from_lms(
            metadata("WHO婴儿身长年龄别百分位"),
            {"length_cm": 55, "l": 1, "m": 50, "s": 0.1},
        )

        self.assertAlmostEqual(result.value, 84.1345, places=4)
        self.assertEqual(result.unit, "percentile")

    def test_who_infant_weight_for_age_supports_zero_l_with_log_transform(self):
        result = who_infant_weight_for_age_z_from_lms(
            metadata("WHO婴儿体重年龄别Z值"),
            {"weight_kg": 12.21402758, "l": 0, "m": 10, "s": 0.1},
        )

        self.assertAlmostEqual(result.value, 2.0, places=4)

    def test_candidate_growth_lms_wrappers_accept_their_expected_measurement_keys(self):
        cases = [
            (who_infant_weight_for_age_percentile_from_lms, "weight_kg"),
            (who_weight_for_length_z_from_lms, "weight_kg"),
            (who_weight_for_length_percentile_from_lms, "weight_kg"),
            (who_head_circumference_for_age_z_from_lms, "head_circumference_cm"),
            (who_head_circumference_for_age_percentile_from_lms, "head_circumference_cm"),
            (cdc_girls_bmi_for_age_z_from_lms, "bmi"),
            (cdc_girls_bmi_for_age_percentile_from_lms, "bmi"),
            (cdc_boys_bmi_for_age_z_from_lms, "bmi"),
            (cdc_boys_bmi_for_age_percentile_from_lms, "bmi"),
            (cdc_girls_weight_for_age_z_from_lms, "weight_kg"),
            (cdc_girls_weight_for_age_percentile_from_lms, "weight_kg"),
            (cdc_boys_weight_for_age_z_from_lms, "weight_kg"),
            (cdc_boys_weight_for_age_percentile_from_lms, "weight_kg"),
        ]

        for function, measurement_key in cases:
            with self.subTest(function=function.__name__):
                result = function(
                    metadata(function.__name__),
                    {measurement_key: 22, "l": 1, "m": 20, "s": 0.1},
                )

                self.assertEqual(result.status, "implemented")
                self.assertIsInstance(result.value, float)

    def test_growth_lms_rejects_non_positive_lms_parameters(self):
        with self.assertRaisesRegex(ValueError, "m must be positive"):
            who_infant_weight_for_age_z_from_lms(
                metadata("WHO婴儿体重年龄别Z值"),
                {"weight_kg": 4, "l": 1, "m": 0, "s": 0.1},
            )


if __name__ == "__main__":
    unittest.main()
