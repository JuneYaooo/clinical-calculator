import unittest

from clinical_calculators.calculators.common.general import body_surface_area_du_bois, ideal_body_weight
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
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


class CommonGeneralCalculatorsTest(unittest.TestCase):
    def test_body_surface_area_du_bois_returns_meters_squared(self):
        calc_metadata = metadata("体表面积（Du Bois 法）", "Body Surface Area by Du Bois Formula")

        calculation = body_surface_area_du_bois(calc_metadata, {"height_cm": 170, "weight_kg": 70})

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 1.8097, places=4)
        self.assertEqual(calculation.unit, "m^2")

    def test_ideal_body_weight_returns_male_devine_estimate(self):
        calc_metadata = metadata("理想体重", "Ideal Body Weight")

        calculation = ideal_body_weight(calc_metadata, {"sex": "male", "height_cm": 177.8})

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 73.0, places=4)
        self.assertEqual(calculation.unit, "kg")
        self.assertIn("adult", calculation.interpretation)

    def test_ideal_body_weight_returns_female_devine_estimate(self):
        calc_metadata = metadata("理想体重", "Ideal Body Weight")

        calculation = ideal_body_weight(calc_metadata, {"sex": "female", "height_cm": 165.1})

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 57.0, places=4)
        self.assertEqual(calculation.unit, "kg")


if __name__ == "__main__":
    unittest.main()
