from __future__ import annotations

from typing import Any

from clinical_calculators.calculators._helpers import number, result
from clinical_calculators.models import CalculationResult, CalculatorMetadata


def body_mass_index(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    weight_kg = number(inputs, "weight_kg")
    height_cm = number(inputs, "height_cm")
    if weight_kg <= 0:
        raise ValueError("weight_kg must be positive")
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        interpretation = "underweight by standard adult BMI categories"
    elif bmi < 25:
        interpretation = "normal adult BMI range"
    elif bmi < 30:
        interpretation = "overweight adult BMI range"
    else:
        interpretation = "obesity adult BMI range"
    return result(metadata, bmi, "kg/m^2", interpretation)


def body_surface_area_du_bois(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    """Body surface area by the Du Bois & Du Bois 1916 equation."""
    height_cm = number(inputs, "height_cm")
    weight_kg = number(inputs, "weight_kg")
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    if weight_kg <= 0:
        raise ValueError("weight_kg must be positive")
    bsa = 0.007184 * (height_cm**0.725) * (weight_kg**0.425)
    return result(metadata, bsa, "m^2", "body surface area estimate by Du Bois formula")


def ideal_body_weight(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    """Ideal body weight by the adult Devine 1974 equation."""
    height_cm = number(inputs, "height_cm")
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    sex = str(inputs["sex"]).strip().lower()
    height_in = height_cm / 2.54

    if sex == "male":
        ibw = 50 + 2.3 * (height_in - 60)
    elif sex == "female":
        ibw = 45.5 + 2.3 * (height_in - 60)
    else:
        raise ValueError("sex must be 'male' or 'female'")

    return result(metadata, ibw, "kg", "adult ideal body weight estimate by Devine formula")


def pediatric_bmi_intermediate(metadata: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
    """Calculate pediatric BMI without falsely claiming an age percentile."""
    age_years = number(inputs, "age_years")
    if age_years < 2 or age_years > 20:
        raise ValueError("age_years must be between 2 and 20")
    weight_kg = number(inputs, "weight_kg")
    height_cm = number(inputs, "height_cm")
    if weight_kg <= 0:
        raise ValueError("weight_kg must be positive")
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    bmi = weight_kg / ((height_cm / 100) ** 2)
    return CalculationResult(
        calculator_id=metadata.id,
        status="partial",
        message="BMI calculated; CDC age/sex percentile lookup is still required",
        value=round(bmi, 4),
        unit="kg/m^2",
        interpretation=(
            "Pediatric BMI intermediate value only. Do not apply adult BMI categories; "
            "use the age- and sex-specific CDC growth reference to obtain a percentile."
        ),
    )
