from __future__ import annotations

from math import sqrt
from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def bazett_qtc(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    qt_seconds = number(inputs, "qt_seconds")
    if qt_seconds <= 0:
        raise ValueError("qt_seconds must be positive")
    if "rr_seconds" in inputs:
        rr_seconds = number(inputs, "rr_seconds")
        if rr_seconds <= 0:
            raise ValueError("rr_seconds must be positive")
    else:
        heart_rate = number(inputs, "heart_rate")
        if heart_rate <= 0:
            raise ValueError("heart_rate must be positive")
        rr_seconds = 60 / heart_rate
    value = qt_seconds / sqrt(rr_seconds)
    return result(metadata, value, "seconds", "Bazett-corrected QT interval; interpret by age, sex, rhythm, and context")
