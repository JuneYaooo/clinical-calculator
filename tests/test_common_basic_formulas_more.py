import unittest

from clinical_calculators.calculators.common.basic_formulas_more import (
    albumin_corrected_anion_gap,
    basal_energy_expenditure_harris_benedict,
    estimated_average_glucose_from_hba1c,
    henderson_hasselbalch_ph,
    ireton_jones_energy_expenditure,
    left_ventricular_ejection_fraction,
    penn_state_energy_expenditure,
    pediatric_maintenance_fluid_holliday_segar,
    pediatric_maintenance_fluid_hourly_rate,
    transferrin_saturation,
    urine_anion_gap,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str = "Basic formula") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_cn}",
        category="common",
        subspecialty="",
        scenario="",
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


class CommonBasicFormulasMoreTest(unittest.TestCase):
    def test_left_ventricular_ejection_fraction_returns_percent(self):
        calculation = left_ventricular_ejection_fraction(
            metadata("左室射血分数简化计算"),
            {"end_diastolic_volume_ml": 120, "end_systolic_volume_ml": 50},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 58.3333, places=4)
        self.assertEqual(calculation.unit, "%")
        self.assertIn("preserved", calculation.interpretation)

    def test_henderson_hasselbalch_ph_uses_bicarbonate_and_paco2(self):
        calculation = henderson_hasselbalch_ph(
            metadata("Henderson-Hasselbach 方程"),
            {"bicarbonate_mmol_l": 24, "paco2_mm_hg": 40},
        )

        self.assertAlmostEqual(calculation.value, 7.401, places=4)
        self.assertEqual(calculation.unit, "pH")

    def test_albumin_corrected_anion_gap_adds_2_5_per_albumin_deficit(self):
        calculation = albumin_corrected_anion_gap(
            metadata("低白蛋白血症时的阴离子间隙"),
            {"anion_gap_mEq_l": 12, "albumin_g_dl": 2.0},
        )

        self.assertAlmostEqual(calculation.value, 17.0, places=4)
        self.assertEqual(calculation.unit, "mEq/L")
        self.assertIn("elevated", calculation.interpretation)

    def test_urine_anion_gap_subtracts_chloride(self):
        calculation = urine_anion_gap(
            metadata("尿液阴离子间隙"),
            {"urine_sodium_mEq_l": 30, "urine_potassium_mEq_l": 20, "urine_chloride_mEq_l": 70},
        )

        self.assertEqual(calculation.value, -20)
        self.assertEqual(calculation.unit, "mEq/L")
        self.assertIn("negative", calculation.interpretation)

    def test_estimated_average_glucose_from_hba1c_uses_adag_equation(self):
        calculation = estimated_average_glucose_from_hba1c(
            metadata("糖化血红蛋白估算平均血糖"),
            {"hba1c_percent": 7.0},
        )

        self.assertAlmostEqual(calculation.value, 154.2, places=4)
        self.assertEqual(calculation.unit, "mg/dL")

    def test_transferrin_saturation_returns_percent(self):
        calculation = transferrin_saturation(
            metadata("转铁蛋白饱和度"),
            {"serum_iron_ug_dl": 80, "tibc_ug_dl": 320},
        )

        self.assertEqual(calculation.value, 25)
        self.assertEqual(calculation.unit, "%")

    def test_pediatric_maintenance_fluid_holliday_segar_uses_100_50_20_rule(self):
        calculation = pediatric_maintenance_fluid_holliday_segar(
            metadata("儿童维持液量的计算"),
            {"weight_kg": 25},
        )

        self.assertEqual(calculation.value, 1600)
        self.assertEqual(calculation.unit, "mL/day")

    def test_pediatric_maintenance_fluid_hourly_rate_divides_daily_volume_by_24(self):
        calculation = pediatric_maintenance_fluid_hourly_rate(
            metadata("儿童维持液量的计算"),
            {"daily_fluid_ml": 1200},
        )

        self.assertEqual(calculation.value, 50)
        self.assertEqual(calculation.unit, "mL/hour")

    def test_basal_energy_expenditure_harris_benedict_male(self):
        calculation = basal_energy_expenditure_harris_benedict(
            metadata("基础热量需要量"),
            {"sex": "male", "weight_kg": 70, "height_cm": 175, "age_years": 40},
        )

        self.assertAlmostEqual(calculation.value, 1634.295, places=4)
        self.assertEqual(calculation.unit, "kcal/day")

    def test_penn_state_energy_expenditure_uses_mifflin_temperature_and_ventilation(self):
        calculation = penn_state_energy_expenditure(
            metadata("Penn State危重症能量公式"),
            {
                "sex": "male",
                "weight_kg": 70,
                "height_cm": 175,
                "age_years": 40,
                "max_temperature_c": 38,
                "minute_ventilation_l_min": 10,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 1972.8, places=4)
        self.assertEqual(calculation.unit, "kcal/day")

    def test_ireton_jones_energy_expenditure_supports_ventilated_and_spontaneous_forms(self):
        ventilated = ireton_jones_energy_expenditure(
            metadata("Ireton-Jones能量公式"),
            {
                "ventilation": "ventilated",
                "sex": "male",
                "age_years": 40,
                "weight_kg": 70,
                "trauma": False,
                "burn": False,
            },
        )
        spontaneous = ireton_jones_energy_expenditure(
            metadata("Ireton-Jones能量公式"),
            {
                "ventilation": "spontaneous",
                "age_years": 40,
                "weight_kg": 70,
                "obesity": True,
            },
        )

        self.assertAlmostEqual(ventilated.value, 2177, places=4)
        self.assertAlmostEqual(spontaneous.value, 1330, places=4)
        self.assertEqual(ventilated.unit, "kcal/day")


if __name__ == "__main__":
    unittest.main()
