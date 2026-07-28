# Routing evaluation

`routing_cases.csv` is an independent, deterministic routing set. Every `expected_ids` value is
checked against the corresponding Chinese or English name and ID in
`clinical_calculator_inventory_full.csv`; it must not be inferred from current search output.

- `direct` means the inventory fields contain the identifying terms after normalization.
- `synonym` means the query relies on a real abbreviation, alias, Chinese/English equivalent, or
  common clinical short name from `clinical_calculator_search_terms.csv`.
- `abbrev` means the held-out query uses an abbreviation or shortened score name.
- `scenario` means the held-out query describes a clinical scenario rather than a full inventory
  name.
- `partial` means the held-out query contains only part of the identifying name or context.
- Multiple IDs mean that any listed inventory entry is a clinically valid routing target.

Run `python3 scripts/evaluate_routing.py` to regenerate `reports/routing_evaluation.json`.

## Held-out evaluation

`routing_cases_heldout.csv` contains the 22 independently checked executable-calculator cases
retained from the phase C acceptance run. Regenerate its report with:

```bash
python3 scripts/evaluate_routing.py --cases evaluation/routing_cases_heldout.csv \
    --report reports/routing_evaluation_heldout.json
```

> 这 22 条来自阶段 C 验收时的独立 held-out 集，其中 `abbrev` / `scenario` / `partial`
> 三类查询不在主用例集里。原始集合中指向已移除条目的用例已同步删除。当前 recall@1 **不是干净的泛化估计**——
> 在看到失败案例之后，同义词表补了 4 条短语级映射，指标才从 73.33% 提到 86.67%。
> 也就是说这批用例已经被拟合过一次。下一轮评测需要再建一批全新的、
> 从未参与过任何调优的用例，才能得到干净的泛化估计。

主用例集 125 条里仍有大量库存全名原样查询，接近恒等映射；因此主集的高分不代表泛化能力。
