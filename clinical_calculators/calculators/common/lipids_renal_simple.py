from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def friedewald_ldl_cholesterol(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    total_cholesterol_mg_dl = number(inputs, "total_cholesterol_mg_dl")
    hdl_mg_dl = number(inputs, "hdl_mg_dl")
    triglycerides_mg_dl = number(inputs, "triglycerides_mg_dl")

    if triglycerides_mg_dl >= 400:
        raise ValueError("triglycerides_mg_dl must be < 400 for Friedewald LDL calculation")

    value = total_cholesterol_mg_dl - hdl_mg_dl - triglycerides_mg_dl / 5
    return result(metadata, value, "mg/dL", "estimated LDL cholesterol by Friedewald formula")


def vldl_cholesterol(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    triglycerides_mg_dl = number(inputs, "triglycerides_mg_dl")

    value = triglycerides_mg_dl / 5
    return result(metadata, value, "mg/dL", "estimated VLDL cholesterol from triglycerides")


def urine_albumin_creatinine_ratio_category(
    metadata: CalculatorMetadata, inputs: dict[str, Any]
) -> CalculationResult:
    albumin_mg_g_creatinine = number(inputs, "albumin_mg_g_creatinine")

    if albumin_mg_g_creatinine < 30:
        interpretation = "A1 albuminuria category (<30 mg/g)"
    elif albumin_mg_g_creatinine <= 300:
        interpretation = "A2 albuminuria category (30-300 mg/g)"
    else:
        interpretation = "A3 albuminuria category (>300 mg/g)"

    return result(metadata, albumin_mg_g_creatinine, "mg/g", interpretation)


def urine_protein_excretion_estimate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    urine_protein_mg_dl = number(inputs, "urine_protein_mg_dl")
    urine_volume_ml = number(inputs, "urine_volume_ml")
    collection_hours = number(inputs, "collection_hours")

    value = urine_protein_mg_dl * (urine_volume_ml / 100) * 24 / collection_hours
    return result(metadata, value, "mg/day", "estimated urine protein excretion normalized to 24 hours")


def hemodialysis_percent_urea_reduction(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    pre_bun_mg_dl = number(inputs, "pre_bun_mg_dl")
    post_bun_mg_dl = number(inputs, "post_bun_mg_dl")

    value = (pre_bun_mg_dl - post_bun_mg_dl) / pre_bun_mg_dl * 100
    return result(metadata, value, "%", "percent urea reduction during hemodialysis")
