# Routing evaluation

`routing_cases.csv` is an independent, deterministic routing set. Every `expected_ids` value is
checked against the corresponding Chinese or English name and ID in
`clinical_calculator_inventory_full.csv`; it must not be inferred from current search output.

- `direct` means the inventory fields contain the identifying terms after normalization.
- `synonym` means the query relies on a real abbreviation, alias, Chinese/English equivalent, or
  common clinical short name from `clinical_calculator_search_terms.csv`.
- Multiple IDs mean that any listed inventory entry is a clinically valid routing target.

Run `python3 scripts/evaluate_routing.py` to regenerate `reports/routing_evaluation.json`.
