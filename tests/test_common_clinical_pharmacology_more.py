import unittest

from clinical_calculators.calculators.common.clinical_pharmacology_more import (
    carboplatin_calvert_dose,
    corrected_phenytoin_level,
    levothyroxine_full_replacement_dose,
    morphine_milligram_equivalents,
    sodium_bicarbonate_deficit,
    vancomycin_auc_mic_ratio,
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


class CommonClinicalPharmacologyMoreTest(unittest.TestCase):
    def test_carboplatin_calvert_dose_uses_target_auc_and_gfr(self):
        calculation = carboplatin_calvert_dose(
            metadata("卡铂Calvert剂量"),
            {"target_auc_mg_ml_min": 5, "gfr_ml_min": 80},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 525)
        self.assertEqual(calculation.unit, "mg")

    def test_sodium_bicarbonate_deficit_uses_weight_and_bicarbonate_gap(self):
        calculation = sodium_bicarbonate_deficit(
            metadata("碳酸氢钠补碱估算"),
            {"weight_kg": 70, "current_bicarbonate_mEq_l": 12, "target_bicarbonate_mEq_l": 24},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 420)
        self.assertEqual(calculation.unit, "mEq")

    def test_sodium_bicarbonate_deficit_rejects_target_below_current(self):
        with self.assertRaisesRegex(ValueError, "target_bicarbonate"):
            sodium_bicarbonate_deficit(
                metadata("碳酸氢钠补碱估算"),
                {"weight_kg": 70, "current_bicarbonate_mEq_l": 24, "target_bicarbonate_mEq_l": 12},
            )

    def test_levothyroxine_full_replacement_dose_uses_weight_factor(self):
        calculation = levothyroxine_full_replacement_dose(
            metadata("甲状腺素替代初始剂量估算"),
            {"weight_kg": 70},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 112)
        self.assertEqual(calculation.unit, "mcg/day")

    def test_levothyroxine_allows_custom_factor_for_context_specific_estimates(self):
        calculation = levothyroxine_full_replacement_dose(
            metadata("甲状腺素替代初始剂量估算"),
            {"weight_kg": 70, "dose_factor_mcg_kg_day": 1.2},
        )

        self.assertEqual(calculation.value, 84)

    def test_morphine_milligram_equivalents_uses_daily_dose_and_conversion_factor(self):
        calculation = morphine_milligram_equivalents(
            metadata("吗啡毫克当量"),
            {
                "dose_mg_per_administration": 10,
                "administrations_per_day": 3,
                "mme_conversion_factor": 1.5,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 45)
        self.assertEqual(calculation.unit, "MME/day")

    def test_vancomycin_auc_mic_ratio_divides_auc24_by_mic(self):
        calculation = vancomycin_auc_mic_ratio(
            metadata("万古霉素AUC/MIC估算"),
            {"auc24_mg_h_l": 500, "mic_mg_l": 1},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 500)
        self.assertEqual(calculation.unit, "AUC/MIC")

    def test_corrected_phenytoin_level_uses_updated_albumin_coefficients(self):
        calculation = corrected_phenytoin_level(
            metadata("苯妥英校正浓度"),
            {"measured_total_phenytoin_mcg_ml": 10, "albumin_g_dl": 2.5, "renal_failure": False},
        )
        renal = corrected_phenytoin_level(
            metadata("苯妥英校正浓度"),
            {"measured_total_phenytoin_mcg_ml": 10, "albumin_g_dl": 2.5, "renal_failure": True},
        )

        self.assertAlmostEqual(calculation.value["corrected_total_phenytoin_mcg_ml"], 12.6984, places=4)
        self.assertAlmostEqual(renal.value["corrected_total_phenytoin_mcg_ml"], 16.6667, places=4)
        self.assertEqual(calculation.unit, "mcg/mL")

    def test_corrected_phenytoin_rejects_string_boolean(self):
        with self.assertRaisesRegex(ValueError, "renal_failure must be a boolean or 0/1"):
            corrected_phenytoin_level(
                metadata("苯妥英校正浓度"),
                {"measured_total_phenytoin_mcg_ml": 10, "albumin_g_dl": 2.5, "renal_failure": "false"},
            )


if __name__ == "__main__":
    unittest.main()
