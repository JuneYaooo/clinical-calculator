from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def _fio2_fraction(inputs: dict[str, Any]) -> float:
    fio2 = number(inputs, "fio2")
    if not 0 <= fio2 <= 1:
        raise ValueError("fio2 must be a fraction between 0 and 1")
    return fio2


def alveolar_arterial_gradient(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    fio2 = _fio2_fraction(inputs)
    barometric_pressure_mm_hg = number(inputs, "barometric_pressure_mm_hg")
    water_vapor_pressure_mm_hg = number(inputs, "water_vapor_pressure_mm_hg")
    paco2_mm_hg = number(inputs, "paco2_mm_hg")
    pao2_mm_hg = number(inputs, "pao2_mm_hg")
    respiratory_quotient = float(inputs.get("respiratory_quotient", 0.8))

    alveolar_oxygen_mm_hg = (
        fio2 * (barometric_pressure_mm_hg - water_vapor_pressure_mm_hg)
        - paco2_mm_hg / respiratory_quotient
    )
    gradient = alveolar_oxygen_mm_hg - pao2_mm_hg
    return result(metadata, gradient, "mmHg", "alveolar-arterial oxygen gradient estimate")


def oxygenation_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    fio2 = _fio2_fraction(inputs)
    mean_airway_pressure_cm_h2o = number(inputs, "mean_airway_pressure_cm_h2o")
    pao2_mm_hg = number(inputs, "pao2_mm_hg")

    value = fio2 * mean_airway_pressure_cm_h2o * 100 / pao2_mm_hg
    return result(metadata, value, "index", "oxygenation index")


def winters_formula_estimated_pco2(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    bicarbonate_mmol_l = number(inputs, "bicarbonate_mmol_l")

    expected_pco2 = 1.5 * bicarbonate_mmol_l + 8
    lower = expected_pco2 - 2
    upper = expected_pco2 + 2
    interpretation = f"expected PaCO2 range {lower:g}-{upper:g} mmHg by Winter's formula"
    return result(metadata, expected_pco2, "mmHg", interpretation)


__all__ = [
    "alveolar_arterial_gradient",
    "oxygenation_index",
    "winters_formula_estimated_pco2",
]
