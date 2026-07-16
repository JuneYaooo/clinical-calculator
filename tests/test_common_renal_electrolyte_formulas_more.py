import unittest

from clinical_calculators.calculators.common.renal_electrolyte_formulas_more import (
    albumin_corrected_calcium_mg_dl,
    estimated_urinary_ammonium,
    hemodialysis_kt_v_barth,
    hemodialysis_kt_v_basile,
    hemodialysis_kt_v_jindal,
    hemodialysis_kt_v_kerr,
    hemodialysis_kt_v_keshaviah,
    hemodialysis_kt_v_lowrie,
    hyponatremia_infusate_rate,
    serum_sodium_change_from_hyperproteinemia,
    serum_sodium_change_from_hypertriglyceridemia,
    serum_sodium_change_per_liter_infusate,
    urine_osmolal_gap,
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


class CommonRenalElectrolyteFormulasMoreTest(unittest.TestCase):
    def test_hemodialysis_urea_clearance_index_variants(self):
        inputs = {"pre_bun_mg_dl": 70, "post_bun_mg_dl": 20}

        self.assertAlmostEqual(hemodialysis_kt_v_lowrie(metadata(), inputs).value, 1.2528, places=4)
        self.assertAlmostEqual(hemodialysis_kt_v_keshaviah(metadata(), inputs).value, 1.4557, places=4)
        self.assertAlmostEqual(hemodialysis_kt_v_barth(metadata(), inputs).value, 1.5543, places=4)
        self.assertAlmostEqual(hemodialysis_kt_v_basile(metadata(), inputs).value, 1.3589, places=4)
        self.assertAlmostEqual(hemodialysis_kt_v_jindal(metadata(), inputs).value, 1.6571, places=4)
        self.assertAlmostEqual(hemodialysis_kt_v_kerr(metadata(), inputs).value, 1.52, places=4)

    def test_albumin_corrected_calcium_mg_dl(self):
        result = albumin_corrected_calcium_mg_dl(
            metadata("低白蛋白血症血钙纠正"),
            {"measured_calcium_mg_dl": 8.2, "normal_albumin_g_dl": 4.0, "albumin_g_dl": 2.5},
        )

        self.assertAlmostEqual(result.value, 9.4, places=4)
        self.assertEqual(result.unit, "mg/dL")

    def test_hyponatremia_infusate_rate(self):
        result = hyponatremia_infusate_rate(
            metadata("低钠血症纠正时的输液速率"),
            {
                "desired_sodium_change_mEq_l_per_hour": 0.5,
                "serum_sodium_mEq_l": 120,
                "total_body_water_fraction": 0.6,
                "weight_kg": 70,
                "infusate_sodium_mEq_l": 513,
                "infusate_potassium_mEq_l": 0,
            },
        )

        self.assertAlmostEqual(result.value, 54.7074, places=4)
        self.assertEqual(result.unit, "mL/hour")

    def test_serum_sodium_change_per_liter_infusate(self):
        result = serum_sodium_change_per_liter_infusate(
            metadata("低钠血症纠正时的输液速率"),
            {
                "infusate_sodium_mEq_l": 513,
                "infusate_potassium_mEq_l": 0,
                "serum_sodium_mEq_l": 120,
                "total_body_water_fraction": 0.6,
                "weight_kg": 70,
            },
        )

        self.assertAlmostEqual(result.value, 9.1395, places=4)
        self.assertEqual(result.unit, "mEq/L per L infusate")

    def test_serum_sodium_change_from_hypertriglyceridemia(self):
        result = serum_sodium_change_from_hypertriglyceridemia(metadata(), {"triglycerides_mg_dl": 1500})

        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "mEq/L")

    def test_serum_sodium_change_from_hyperproteinemia(self):
        result = serum_sodium_change_from_hyperproteinemia(metadata(), {"serum_protein_g_dl": 12})

        self.assertEqual(result.value, 1)
        self.assertEqual(result.unit, "mEq/L")

    def test_urine_osmolal_gap_uses_calculated_osmolality_components(self):
        result = urine_osmolal_gap(
            metadata("尿渗透压间隙"),
            {
                "measured_urine_osmolality_mOsm_kg": 650,
                "urine_sodium_mEq_l": 45,
                "urine_potassium_mEq_l": 30,
                "urine_urea_nitrogen_mg_dl": 28,
                "urine_glucose_mg_dl": 90,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 485)
        self.assertEqual(result.unit, "mOsm/kg")
        self.assertIn("urine osmolal gap", result.interpretation)

    def test_estimated_urinary_ammonium_halves_urine_osmolal_gap(self):
        result = estimated_urinary_ammonium(
            metadata("尿铵估算"),
            {
                "measured_urine_osmolality_mOsm_kg": 650,
                "urine_sodium_mEq_l": 45,
                "urine_potassium_mEq_l": 30,
                "urine_urea_nitrogen_mg_dl": 28,
                "urine_glucose_mg_dl": 90,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 242.5)
        self.assertEqual(result.unit, "mEq/L")
        self.assertIn("urinary ammonium", result.interpretation)


if __name__ == "__main__":
    unittest.main()
