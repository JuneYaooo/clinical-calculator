from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

from .models import CalculationResult, CalculatorMetadata, InputSpec, SkillCheck


REQUIRED_METADATA_FIELDS = (
    "id",
    "category",
    "scenario",
    "name_cn",
    "name_en",
    "inputs",
    "output",
    "formula",
    "interpretation",
    "purpose",
    "source_type",
    "source",
    "source_url",
    "channel",
    "evidence_tier",
    "commonness",
    "coverage_note",
    "clinical_note",
    "entry_source",
)


_UNIT_SUFFIXES = {
    "_kg": "kg",
    "_cm": "cm",
    "_mm": "mm",
    "_mm_hg": "mmHg",
    "_mg_dl": "mg/dL",
    "_g_dl": "g/dL",
    "_mmol_l": "mmol/L",
    "_mEq_l": "mEq/L",
    "_years": "years",
    "_months": "months",
    "_weeks": "weeks",
    "_seconds": "seconds",
    "_percent": "%",
    "_bpm": "beats/min",
    "_breaths_min": "breaths/min",
    "_mg_l": "mg/L",
    "_10e9_l": "10^9/L",
    "_ml_min_1_73m2": "mL/min/1.73m^2",
    "_mg_g": "mg/g",
    "_umol_l": "µmol/L",
    "_u_l": "U/L",
    "_cigarettes_day": "cigarettes/day",
    "_micrometers": "µm",
    "_db": "dB",
}

_SEQUENCE_MARKERS = ("items", "components", "component_points", "item_scores", "part_scores")
_BOOLEAN_KEYS = {
    "more_than_50_seizures_per_month",
    "developmental_disability_or_iq_below_70",
    "renal_failure",
    "black",
    "pediatric",
    "solid_components_under_7mm",
    "closed_circle",
    "numbers_in_correct_positions",
    "all_twelve_numbers_present",
    "hands_show_requested_time",
    "family_premature_chd_or_ldl_above_95th",
    "family_xanthoma_arcus_or_child_ldl_above_95th",
    "personal_premature_chd",
    "personal_premature_cerebral_or_peripheral_vascular_disease",
    "tendon_xanthoma",
    "corneal_arcus_under_45",
    "causative_ldlr_apob_pcsk9_mutation",
    "confusion_disorientation_impulsivity",
    "symptomatic_depression",
    "altered_elimination",
    "dizziness_or_vertigo",
    "antiepileptics",
    "benzodiazepines",
    "nosocomial",
    "north_america",
    "concomitant_cis",
    "current_smoker",
    "urgent_or_emergency_surgery",
    "pneumonectomy",
    "malignant_diagnosis",
    "diabetes",
    "copd",
    "heart_failure_diagnosed_at_least_18_months",
    "has_chest_pain_or_dyspnea",
    "family_history_sudden_cardiac_death",
    "nonsustained_ventricular_tachycardia",
    "unexplained_syncope",
    "history_bleeding",
    "history_heart_failure_or_lvef_below_40",
    "history_stroke",
    "moderate_severe_ckd",
    "history_coronary_or_peripheral_vascular_disease",
    "dementia",
    "current_antiplatelet_drug",
    "carotid_occlusive_disease",
    "family_history_diabetes",
    "hypertension",
    "physically_active",
}

_CHOICE_KEYS = {
    "respiratory_effort": ("normal", "mild", "moderate", "severe_or_apnea"),
    "oxygen_therapy": ("room_air", "low", "high"),
    "race_ethnicity_garfield": (
        "hispanic_latino",
        "asian",
        "black_mixed_other",
        "caucasian",
    ),
    "tumor_count_category": ("single", "two_to_seven", "eight_or_more"),
    "tumor_size_category": ("under_3_cm", "at_least_3_cm"),
    "prior_recurrence_rate": ("primary", "at_most_one_per_year", "more_than_one_per_year"),
    "t_category": ("ta", "t1"),
    "who_1973_grade": ("g1", "g2", "g3"),
    "race_ethnicity_plco": (
        "white",
        "black",
        "hispanic",
        "asian",
        "american_indian_or_alaska_native",
        "native_hawaiian_or_pacific_islander",
    ),
}

_ADL_LEVEL_KEYS = {
    "mobility_adl_0_to_4",
    "eating_adl_0_to_4",
    "toileting_adl_0_to_4",
    "hygiene_adl_0_to_4",
}
_GENERIC_SOURCE_URLS = {
    "https://www.mdcalc.com/",
    "https://qxmd.com/calculate/",
    "https://www.merckmanuals.com/professional/pages-with-widgets/clinical-calculators",
}
_GENERIC_INTERPRETATION = "具体单位、正常范围和临床阈值按外部来源执行"


def _infer_input_spec(name: str) -> InputSpec:
    unit = next((unit for suffix, unit in _UNIT_SUFFIXES.items() if name.endswith(suffix)), "")
    if name == "bmi":
        unit = "kg/m^2"
    if name == "sex":
        return InputSpec(name=name, value_type="choice", choices=("female", "male"))
    if name in _CHOICE_KEYS:
        return InputSpec(name=name, value_type="choice", choices=_CHOICE_KEYS[name])
    if name in _ADL_LEVEL_KEYS:
        return InputSpec(name=name, value_type="number", unit="points", minimum=0, maximum=4)
    if name in _BOOLEAN_KEYS or name.startswith(("has_", "history_", "on_")):
        return InputSpec(name=name, value_type="boolean")
    if any(marker in name for marker in _SEQUENCE_MARKERS):
        return InputSpec(name=name, value_type="sequence")

    numeric = bool(unit) or name in {
        "age",
        "score",
        "bmi",
        "l",
        "m",
        "s",
        "log_odds",
        "risk_score",
        "education_level_1_to_6",
        "mean_vertical_cup_disc_ratio",
        "asa_class",
        "ecog_performance_status",
        "mrc_dyspnea_grade",
        "comorbidity_count",
        "nyha_class",
    }
    numeric = numeric or name.endswith(("_score", "_points"))
    minimum = None
    maximum = None
    if name in {"age", "age_years"}:
        minimum, maximum = 0, 130
    elif name.endswith(("_percent", "_percentage")):
        minimum, maximum = 0, 100
    elif name in {"bmi", "height_cm", "weight_kg", "serum_creatinine_mg_dl", "serum_creatinine_umol_l"}:
        minimum = 0
    return InputSpec(
        name=name,
        value_type="number" if numeric else "any",
        unit=unit,
        minimum=minimum,
        maximum=maximum,
    )


def _validate_input(spec: InputSpec, value: Any) -> None:
    if spec.value_type == "number":
        if isinstance(value, bool):
            raise ValueError(f"{spec.name} must be numeric")
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{spec.name} must be numeric") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"{spec.name} must be finite")
        if spec.minimum is not None and numeric < spec.minimum:
            raise ValueError(f"{spec.name} must be at least {spec.minimum:g}")
        if spec.maximum is not None and numeric > spec.maximum:
            raise ValueError(f"{spec.name} must be at most {spec.maximum:g}")
    elif spec.value_type == "boolean":
        if not isinstance(value, bool) and value not in (0, 1):
            raise ValueError(f"{spec.name} must be a boolean or 0/1")
    elif spec.value_type == "choice":
        candidate = str(value).strip()
        if candidate not in spec.choices and candidate.lower() not in spec.choices:
            raise ValueError(f"{spec.name} must be one of: {', '.join(spec.choices)}")
    elif spec.value_type == "sequence":
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
            raise ValueError(f"{spec.name} must be a sequence")


class CalculatorSkill:
    def __init__(
        self,
        metadata: CalculatorMetadata,
        implementation: Callable[[CalculatorMetadata, dict[str, Any]], CalculationResult] | None = None,
        required_inputs: tuple[str, ...] = (),
        implementation_module: str = "",
        implementation_level: str = "metadata_only",
        input_schema: tuple[InputSpec, ...] | None = None,
        catalog_layer: str = "executable",
        pending_blocker_type: str = "",
    ) -> None:
        self.metadata = metadata
        self._implementation = implementation
        self.required_inputs = required_inputs
        self.input_schema = input_schema or tuple(_infer_input_spec(name) for name in required_inputs)
        self.implementation_module = implementation_module
        self.implementation_level = implementation_level
        self.catalog_layer = catalog_layer
        self.pending_blocker_type = pending_blocker_type

    @property
    def implemented(self) -> bool:
        return self._implementation is not None

    @property
    def complete(self) -> bool:
        return self.implementation_level == "complete"

    def self_check(self) -> SkillCheck:
        errors = []
        for field in REQUIRED_METADATA_FIELDS:
            if not str(getattr(self.metadata, field)).strip():
                errors.append(f"missing {field}")
        if not self.metadata.source_url.startswith("http"):
            errors.append("source_url must start with http")
        if self.metadata.evidence_tier.startswith("D："):
            errors.append("D-tier candidate cannot be an effective skill")
        return SkillCheck(ok=not errors, errors=tuple(errors))

    def medical_review_check(self) -> SkillCheck:
        """Report product-readiness gaps without removing metadata-only entries."""
        errors = []
        if self.implementation_level != "complete":
            errors.append(f"implementation level is {self.implementation_level}")
        if not self.metadata.version.strip():
            errors.append("missing source version/year")
        if self.metadata.source_url in _GENERIC_SOURCE_URLS:
            errors.append("source URL is a generic calculator-library landing page")
        if _GENERIC_INTERPRETATION in self.metadata.interpretation:
            errors.append("interpretation defers thresholds to an external source")
        if self.metadata.source_group == "custom":
            errors.append("custom extension requires independent clinical review")
        return SkillCheck(ok=not errors, errors=tuple(errors))

    def run(self, inputs: dict[str, Any]) -> CalculationResult:
        if self._implementation is None:
            return CalculationResult(
                calculator_id=self.metadata.id,
                status="needs_formula_implementation",
                message="metadata is available, but calculation logic still requires formula-level medical audit and implementation",
                required_inputs=(),
            )
        missing = tuple(key for key in self.required_inputs if key not in inputs)
        if missing:
            return CalculationResult(
                calculator_id=self.metadata.id,
                status="missing_inputs",
                message=f"missing required inputs: {', '.join(missing)}",
                required_inputs=missing,
            )
        try:
            for spec in self.input_schema:
                _validate_input(spec, inputs[spec.name])
            return self._implementation(self.metadata, inputs)
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            return CalculationResult(
                calculator_id=self.metadata.id,
                status="invalid_inputs",
                message=str(exc) or "invalid calculator inputs",
                required_inputs=self.required_inputs,
            )
