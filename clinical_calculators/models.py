from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CalculatorMetadata:
    id: str
    category: str
    subspecialty: str
    scenario: str
    name_cn: str
    name_en: str
    inputs: str
    output: str
    formula: str
    interpretation: str
    purpose: str
    source_type: str
    source: str
    source_url: str
    channel: str
    evidence_tier: str
    commonness: str
    coverage_note: str
    clinical_note: str
    version: str
    entry_source: str
    source_group: str
    notes: str


@dataclass(frozen=True)
class SkillCheck:
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputSpec:
    """Machine-readable contract for one calculator input."""

    name: str
    value_type: str = "any"
    unit: str = ""
    required: bool = True
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class CalculationResult:
    calculator_id: str
    status: str
    message: str
    value: Any = None
    unit: str = ""
    interpretation: str = ""
    required_inputs: tuple[str, ...] = ()
