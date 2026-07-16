from __future__ import annotations

import math
from typing import Any

from clinical_calculators.models import CalculationResult, CalculatorMetadata


def number(inputs: dict[str, Any], key: str) -> float:
    if key not in inputs:
        raise KeyError(key)
    value = inputs[key]
    if isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be numeric") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{key} must be finite")
    return numeric


def boolean(inputs: dict[str, Any], key: str, *, default: bool | None = None) -> bool:
    if key not in inputs:
        if default is not None:
            return default
        raise KeyError(key)
    value = inputs[key]
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ValueError(f"{key} must be a boolean or 0/1")


def result(metadata: CalculatorMetadata, value: float, unit: str, interpretation: str) -> CalculationResult:
    if isinstance(value, bool):
        raise ValueError("calculation result must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("calculation result must be finite")
    return CalculationResult(
        calculator_id=metadata.id,
        status="implemented",
        message="calculation completed",
        value=round(numeric, 4),
        unit=unit,
        interpretation=interpretation,
    )
