# Case-driven calculator workbench

The workbench adds a case-oriented orchestration layer without duplicating calculator formulas.
It is designed to be embedded in a larger clinical workflow, not deployed as a public clinical
application by itself.

## Workflow

```text
de-identified narrative or structured values
                    |
                    v
       explainable intent detection
                    |
                    v
       local evidence-catalog search
                    |
                    v
    candidate calculators + reasons + gaps
                    |
             explicit user selection
                    |
                    v
       missing-input confirmation form
                    |
                    v
     existing calculator implementations
                    |
                    v
 result + input snapshot + formula + source + trace
```

Intent detection identifies assessment opportunities from conservative cues. It does not diagnose
the patient. An absent fact remains unknown; it is never converted to `false`, normal, or zero.
No calculator runs until the user explicitly selects it and confirms every required input.

## Python integration

```python
from clinical_calculators import calculate_selected, recommend_for_case

recommendation = recommend_for_case(
    query="",  # Optional; leave blank for case-driven discovery.
    case_text="74岁男性，非瓣膜性房颤，有高血压和既往脑卒中，无糖尿病。",
    supplied_values={},  # Optional structured EHR/FHIR values take precedence.
)

result = calculate_selected(
    {
        "CALC-0049": {
            "age_years": 74,
            "sex": "male",
            "hypertension": True,
            "diabetes": False,
            "congestive_heart_failure": False,
            "stroke_tia_thromboembolism": True,
            "vascular_disease": False,
        }
    },
    session_id=recommendation["session_id"],
)
```

`recommend_for_case` returns the detected directions, recommendation reasons, match diagnostics,
input contracts, extracted values, missing fields, formulas, sources, review gaps, and an audit
log. `calculate_selected` accepts exact calculator IDs and returns immutable input snapshots and a
four-step calculation trace.

## Local HTTP integration

Start the standard-library server:

```bash
python3 scripts/clinical_workbench.py
```

Endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Process health and storage mode |
| `POST /api/recommend` | Case-driven or goal-constrained recommendation |
| `POST /api/calculate` | Execute explicitly selected calculators |

The included server has no authentication, TLS, user management, durable audit store, or EHR
write-back. It binds to `127.0.0.1` by default and is intended for local use. A production system
should call the Python orchestration functions behind its existing authenticated backend instead
of exposing this development server.

## Recommended surrounding systems

| Layer | Responsibility |
| --- | --- |
| De-identification gateway | Remove direct identifiers before text reaches this project |
| EHR/FHIR adapter | Supply structured observations, conditions, units, and encounter context |
| Terminology service | Normalize SNOMED CT, ICD, LOINC, medications, and local terms |
| Guideline/literature RAG | Retrieve current primary sources and preserve cited passages |
| This project | Route, validate inputs, execute formulas, and produce reproducible traces |
| Clinical review workflow | Approve calculator versions, populations, and release status |
| Governance/audit platform | Identity, access control, signatures, retention, and result write-back |

The evidence RAG layer must not install a newly discovered formula directly. It should create a
source-backed draft with version, population, units, rules, and known-answer tests; a reviewer then
approves installation and clinical release separately.
