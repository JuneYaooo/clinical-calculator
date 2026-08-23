"""Clinical calculator skill registry."""

from .models import CalculationResult, CalculatorMetadata, InputSpec
from .extensions import ManifestError, load_custom_manifest
from .registry import (
    CalculatorRegistry,
    CalculatorSearchResponse,
    CalculatorSearchResult,
    load_registry,
)
from .workbench import (
    calculate_selected,
    detect_case_intents,
    detect_privacy_risks,
    recommend_for_case,
)

__all__ = [
    "CalculationResult",
    "CalculatorMetadata",
    "CalculatorRegistry",
    "CalculatorSearchResponse",
    "CalculatorSearchResult",
    "InputSpec",
    "ManifestError",
    "load_registry",
    "load_custom_manifest",
    "calculate_selected",
    "detect_case_intents",
    "detect_privacy_risks",
    "recommend_for_case",
]
