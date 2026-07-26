# Search and routing

The registry builds one standard-library-only inverted index when it loads. Search does not scan
the inventory again for each query. The indexed fields and weights are:

| Field | Weight |
| --- | ---: |
| `name_cn`, `name_en` | 10 |
| custom `tags`, `aliases` when a future manifest schema exposes them | 10 |
| `scenario` | 6 |
| `subspecialty` | 4 |
| `category` | 3 |
| `purpose` | 2 |
| `source` | 1 |

## Normalization and tokens

Search applies Unicode NFKC normalization, case folding, punctuation/hyphen-to-space conversion,
and whitespace compression. Latin text produces word tokens plus compact and digit-free forms.
Thus `CHA（2）DS（2）-VASc`, `CHA₂DS₂-VASc`, `cha2ds2 vasc`, and `chads vasc` share searchable
forms. Every CJK run produces single-character tokens, adjacent bigrams, and a full-run token. No
external segmenter is used.

Candidates come from the token postings. Their base score is the sum of weights for every matched
token/field pair multiplied by the fraction of query tokens covered. Exact names, name prefixes,
and name substrings receive descending bonuses. Ties sort by Chinese name and then calculator ID,
so repeated runs are deterministic. A minimum amount of distinctive token evidence prevents a
single common Chinese character from becoming a match.

## Maintaining synonyms

`clinical_calculator_search_terms.csv` has `term`, semicolon-separated `expands_to`, and `note`
columns. Add only genuine clinical abbreviations, aliases, Chinese/English equivalents, or common
short names. Do not add a phrase merely to satisfy one evaluation case, and do not rewrite
inventory metadata. Loading rejects empty terms/expansions, self-expansion, and duplicate terms;
duplicate expansions within a row are removed.

Mark an evaluation case `synonym` only when it depends on this table. Cases whose identifying text
is already in an indexed inventory field are `direct`.

## No-match behavior

The CLI returns `status: "no_match"`, an empty `results` array, and at most five partial-token
`suggestions`. Treat that status as a request to reformulate the search with a calculator name,
clinical scenario, population, or standard abbreviation. Never choose a remembered formula just
because search returned no result. Successful results include a `match` object containing score,
coverage, matched fields, and matched terms.

## Extending the evaluation set

Add cases to `evaluation/routing_cases.csv`. Confirm every `expected_ids` value by looking up the
name and ID in `clinical_calculator_inventory_full.csv`, then record that evidence in `note`.
Multiple IDs may be listed when several inventory entries are valid. Use `expected_inputs` only
when the exact declared input tuple has also been checked; the evaluator treats it as a contract
drift assertion.

Run:

```bash
python3 scripts/evaluate_routing.py
```

The command rewrites `reports/routing_evaluation.json` with overall, category, and locale
recall@1, recall@5, MRR, and zero-result metrics. `tests/test_routing_evaluation.py` compares the
regression metrics with `reports/routing_baseline.json`.
