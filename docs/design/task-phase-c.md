# 阶段 C 执行任务书：检索重写与路由评测门禁

前置阅读：`docs/design/2026-07-26-extensible-calculator-skill.md` 第 3.3、3.4、5 节。
前置状态：阶段 A 已完成（commit `f7f97bc`），契约基础设施与棘轮已就位。

## 要解决的问题

当前中文检索无分词，把整个查询串当一个 token 做子串匹配。实测失败：

| 查询 | 现状 | 库内实际情况 |
| --- | --- | --- |
| `肺栓塞概率` | 0 条 | `肺栓塞` 相关 10 条 |
| `脓毒症` | 0 条 | 库内存在脓毒症相关条目 |
| `小儿脱水` | 0 条 | `脱水` 相关 3 条 |
| `预测死亡率的评分` | 0 条 | 大量死亡率预测评分 |
| `chads vasc` | 0 条 | CALC-0049 |

检索返回 0 条时，Agent 会退回记忆自行编造公式，这是本仓库最需要防止的失败模式。

## 交付物

### 1. 新增 `clinical_calculators/search.py`

把 `registry.py` 里的 `_normalize_search_text`、`_query_groups`、`_matches_groups`、
`SEARCH_ALIASES` 与 `CalculatorRegistry.search` 的打分逻辑全部迁出到这个新模块。
`CalculatorRegistry.search / search_runnable / search_layer / search_released` 的
**函数签名与返回类型必须保持不变**（仍返回 `list[CalculatorSkill]`），只换内部实现。

- **归一化**：NFKC、casefold、全角转半角、标点与连字符转空格、压缩空白。
  `CHA（2）DS（2）-VASc`、`CHA₂DS₂-VASc`、`cha2ds2 vasc` 必须归一到可互相命中的形态。
- **分词**：拉丁段按空白与大小写边界切词，并额外产出去数字/去标点变体
  （`CHA2DS2-VASc` → `cha2ds2vasc`、`chadsvasc`）；CJK 段同时产出单字与相邻 bigram
  （`肺栓塞` → `肺`、`栓`、`塞`、`肺栓`、`栓塞`）。
- **倒排索引**：`token -> {(calculator_id, field)}`，在注册表加载时构建一次并缓存，
  不要每次查询重扫全表。索引字段：`name_cn`、`name_en`、`category`、`subspecialty`、
  `scenario`、`purpose`、`source`，外加自定义 manifest 的 `tags`/`aliases`（若阶段 D 未做则跳过）。
- **字段权重**：`name_cn`/`name_en` 10、`scenario` 6、`subspecialty` 4、`category` 3、
  `purpose` 2、`source` 1。权重表定义为模块级常量，便于调整。
- **打分**：`加权命中和 × 查询 token 覆盖率`。完全等名、名称前缀命中给额外加成。
  覆盖率机制是关键：`肺栓塞概率` 中 `概率` 未命中时，仍应靠 `肺栓塞` 的高覆盖返回结果。
- **排序稳定性**：同分时按 `name_cn`、再按 `id` 排序，保证结果可复现。

### 2. 同义词表数据化

新增 `clinical_calculator_search_terms.csv`，列：`term`,`expands_to`,`note`。
`expands_to` 用分号分隔多个展开词。把现在硬编码在 `registry.py` 的 `SEARCH_ALIASES`
全部迁进来，并补充实测失败查询所需的真实临床同义词。

加载时校验：`term` 与 `expands_to` 非空、无自环、无重复 `term`、展开词去重。
**只允许真实临床同义关系**（缩写、别名、中英对照、常用简称），不得为了让某条评测用例
通过而塞入牵强映射。

### 3. 零结果兜底与可解释性

- 查询无结果时降级为部分 token 匹配，返回 `suggestions`（最多 5 条候选名称）
  并在 CLI 输出中带 `status: "no_match"`，明确提示 Agent 应改换检索词而非依赖记忆。
- 每条搜索结果附加 `match` 对象：`{score, coverage, matched_fields, matched_terms}`。
- 这些都是 CLI 输出的**新增**字段，不得改变现有字段的名称与语义。

### 4. 路由评测集

新增 `evaluation/routing_cases.csv`，列：`query`,`expected_ids`,`locale`,`category`,`note`。
`expected_ids` 用分号分隔（允许多个正确答案）。至少 120 条，必须覆盖：

- 中文全名、中文常用简称（如"房颤评分"）
- 英文全名、英文缩写（`qSOFA`、`MELD`）、缩写变体（`chads vasc`、`cha2ds2vasc`）
- 场景化自然提问（如"评估房颤卒中风险用什么"、"预测死亡率的评分"）
- 易混同名歧义（Wells DVT vs Wells PE 应各自返回对应 ID）
- 上表列出的 5 个实测失败查询，全部必须通过
- 单位/人群变体（成人 vs 儿童 eGFR、SI vs 常规单位）

`expected_ids` **必须通过查 `clinical_calculator_inventory_full.csv` 的名称与 ID 确认**，
不得只看新检索的输出来反填期望值（那样评测会变成自我循环）。每条 case 的 `note`
要写清期望依据。

**防作弊要求**：`category` 列需标注该 case 是否依赖同义词表（`synonym` / `direct`）。
评测脚本必须分别报告这两类的 recall，避免用堆同义词的方式刷分。

### 5. 评测脚本与 CI 门禁

新增 `scripts/evaluate_routing.py`：跑全部 case，输出 `reports/routing_evaluation.json`，
含 recall@1、recall@5、MRR、零结果率，以及按 `category` 与 `locale` 分组的同口径指标。
纯确定性，不依赖 LLM 或网络。

新增 `reports/routing_baseline.json` 记录基线，新增 `tests/test_routing_evaluation.py`：
recall@1 与 recall@5 不得低于基线，零结果率不得高于基线。失败信息要提示
"路由质量不得倒退，如确为有意变更请同步更新基线文件"。接入 `.github/workflows/test.yml`。

可选字段 `expected_inputs`：若某 case 填了，断言目标计算器的契约恰好声明了这些输入名
（零成本的契约漂移检查，复用阶段 A 的契约数据）。

### 6. 文档

新增 `references/search-and-routing.md`：归一化与分词规则、字段权重、打分方式、
同义词表如何维护、零结果时 Agent 应如何处理、评测集如何扩充。
`SKILL.md` 仅在核心流程处加一句指向该文档的引用，保持精简。

## 不要做的事

- 不引入 jieba 等任何第三方分词或检索依赖，运行时只用标准库。
- 不改动阶段 A 的契约数据与加载器。
- 不动 `extensions.py` 的 manifest schema（阶段 D）。
- 不加 `source_quality` 或 caveats（阶段 E）。
- 不改现有 calculator ID、输入名、输出结构，不改 CLI 现有字段语义。
- 不修改 `clinical_calculator_inventory_full.csv` 的医学内容。
- 不为了让评测通过而修改库存元数据或塞入牵强同义词。

## 验收

```bash
python3 scripts/clinical_calculator.py validate
python3 scripts/evaluate_routing.py
python3.12 -m pytest -q        # 存量 956 项 + 新增全绿
# 实测失败查询必须全部返回正确条目：
python3 scripts/clinical_calculator.py search "肺栓塞概率"
python3 scripts/clinical_calculator.py search "脓毒症"
python3 scripts/clinical_calculator.py search "小儿脱水"
python3 scripts/clinical_calculator.py search "预测死亡率的评分"
python3 scripts/clinical_calculator.py search "chads vasc"
# 零结果路径也要能看到 no_match 与 suggestions：
python3 scripts/clinical_calculator.py search "完全不存在的东西xyz"
```

`tests/test_calculator_skills.py` 中已有的检索断言（含 `CHA₂DS₂-VASc`、`房颤 卒中`、
`肾功能`、`房颤卒中风险`）必须继续通过。

最后报告：recall@1 / recall@5 / MRR / 零结果率、`direct` 与 `synonym` 两类分别的 recall、
评测集条数、以及仍未能正确路由的 case 逐条列出（含你判断的原因）。
