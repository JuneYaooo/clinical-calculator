import unittest

from clinical_calculators.calculators.common.hemodynamics_more import (
    arterial_oxygen_content,
    body_surface_area_du_bois_for_hemodynamics,
    cardiac_index,
    fick_cardiac_output_from_contents,
    stroke_volume,
    stroke_volume_index,
    venous_oxygen_content,
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


class CommonHemodynamicsMoreTest(unittest.TestCase):
    def test_arterial_oxygen_content_uses_bound_and_dissolved_oxygen(self):
        result = arterial_oxygen_content(
            metadata("心输出量"),
            {"hemoglobin_g_dl": 15, "oxygen_saturation_percent": 98, "pao2_mm_hg": 90},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 199.77, places=4)
        self.assertEqual(result.unit, "mL O2/L blood")

    def test_venous_oxygen_content_uses_venous_saturation_and_pvo2(self):
        result = venous_oxygen_content(
            metadata("心输出量"),
            {"hemoglobin_g_dl": 15, "venous_oxygen_saturation_percent": 75, "pvo2_mm_hg": 40},
        )

        self.assertAlmostEqual(result.value, 151.99, places=4)
        self.assertEqual(result.unit, "mL O2/L blood")

    def test_fick_cardiac_output_from_oxygen_contents(self):
        result = fick_cardiac_output_from_contents(
            metadata("心输出量"),
            {
                "oxygen_consumption_ml_min": 250,
                "arterial_oxygen_content_ml_dl": 20,
                "venous_oxygen_content_ml_dl": 15,
            },
        )

        self.assertEqual(result.value, 50)
        self.assertEqual(result.unit, "dL/min")

    def test_cardiac_index_divides_output_by_bsa(self):
        result = cardiac_index(metadata("心输出量Multicalc"), {"cardiac_output_l_min": 5.2, "bsa_m2": 1.8})

        self.assertAlmostEqual(result.value, 2.8889, places=4)
        self.assertEqual(result.unit, "L/min/m2")

    def test_stroke_volume_converts_liters_to_milliliters_per_beat(self):
        result = stroke_volume(metadata("心输出量Multicalc"), {"cardiac_output_l_min": 5.2, "heart_rate_bpm": 70})

        self.assertAlmostEqual(result.value, 74.2857, places=4)
        self.assertEqual(result.unit, "mL/beat")

    def test_stroke_volume_index_divides_stroke_volume_by_bsa(self):
        result = stroke_volume_index(metadata("心输出量Multicalc"), {"stroke_volume_ml": 75, "bsa_m2": 1.8})

        self.assertAlmostEqual(result.value, 41.6667, places=4)
        self.assertEqual(result.unit, "mL/beat/m2")

    def test_du_bois_bsa_for_hemodynamics(self):
        result = body_surface_area_du_bois_for_hemodynamics(
            metadata("心输出量Multicalc"), {"height_cm": 175, "weight_kg": 70}
        )

        self.assertAlmostEqual(result.value, 1.8481, places=4)
        self.assertEqual(result.unit, "m2")


if __name__ == "__main__":
    unittest.main()
