import unittest

from clinical_calculators.calculators.common.respiratory_acidbase import (
    alveolar_arterial_gradient,
    oxygenation_index,
    winters_formula_estimated_pco2,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="respiratory acid-base",
        scenario="unit test",
        name_cn=name_cn,
        name_en=name_cn,
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


class CommonRespiratoryAcidBaseCalculatorsTest(unittest.TestCase):
    def test_alveolar_arterial_gradient_room_air(self):
        result = alveolar_arterial_gradient(
            metadata("A-a 梯度"),
            {
                "fio2": 0.21,
                "barometric_pressure_mm_hg": 760,
                "water_vapor_pressure_mm_hg": 47,
                "paco2_mm_hg": 40,
                "pao2_mm_hg": 95,
                "respiratory_quotient": 0.8,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 4.73, places=2)
        self.assertEqual(result.unit, "mmHg")

    def test_oxygenation_index(self):
        result = oxygenation_index(
            metadata("氧合指数"),
            {"fio2": 0.5, "mean_airway_pressure_cm_h2o": 10, "pao2_mm_hg": 100},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 5)
        self.assertEqual(result.unit, "index")

    def test_winters_formula_estimates_expected_pco2_and_range(self):
        result = winters_formula_estimated_pco2(
            metadata("Winters公式估算PCO2"),
            {"bicarbonate_mmol_l": 12},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 26)
        self.assertEqual(result.unit, "mmHg")
        self.assertIn("24-28", result.interpretation)

    def test_invalid_fio2_raises_value_error(self):
        calculators = [
            (
                alveolar_arterial_gradient,
                {
                    "fio2": 1.2,
                    "barometric_pressure_mm_hg": 760,
                    "water_vapor_pressure_mm_hg": 47,
                    "paco2_mm_hg": 40,
                    "pao2_mm_hg": 95,
                },
            ),
            (
                oxygenation_index,
                {"fio2": -0.1, "mean_airway_pressure_cm_h2o": 10, "pao2_mm_hg": 100},
            ),
        ]

        for calculator, inputs in calculators:
            with self.subTest(calculator=calculator.__name__):
                with self.assertRaises(ValueError):
                    calculator(metadata("invalid fio2"), inputs)


if __name__ == "__main__":
    unittest.main()
