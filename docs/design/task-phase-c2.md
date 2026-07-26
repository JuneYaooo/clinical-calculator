# 阶段 C2 任务书：修复阶段 C 自查发现的两个缺陷

## 背景

阶段 C（commit `b833f72`）已落地，但我在验收时发现两个自己引入的问题。本轮**只修这两个问题 + 把 held-out 用例入库**，不做新功能、不改检索算法、不改医学内容。

## 绝对不要做的事

1. **不要修改 `clinical_calculator_inventory_full.csv` 的任何医学内容**（条目原文、分值、阈值、单位、边界、来源）。
2. **不要新增或修改 `clinical_calculator_search_terms.csv` 的任何行。** 本轮不允许用加同义词的方式提升指标。
3. **不要改 `clinical_calculators/search.py` 的打分逻辑**：`FIELD_WEIGHTS`、`_qualifies`、`_contains_term`、`_is_better`、分词函数一律不动。本轮是重构 + 门禁，不是调优。
4. **不要为了让指标好看而删改评测用例。**
5. **不要执行任何 git 命令**（`git add` / `git commit` / `git push` 都不要）。改完留在工作区，我来审查和提交。
6. 运行时只允许 Python 标准库。测试用 `python3.12 -m pytest -q`（`python3` 是 3.13，没装 pytest）。

## 任务 1：把检索诊断数据从可变状态改挂到返回值上

### 缺陷

`CalculatorRegistry` 把上一次检索的诊断结果存在实例字段 `_last_search_response` 上，
`search_response()` 和 `search_match()` 读这个字段。第二次检索会冲掉第一次的数据：

```python
r = load_registry()
first = r.search("chads vasc")[0].metadata.id
r.search("脓毒症")                  # 第二次检索
r.search_match(first)              # -> None，第一次的 match 已经丢了
```

调用方拿到 `list[CalculatorSkill]` 之后无法安全地再问诊断信息。这是设计缺陷：
诊断数据应该挂在返回值上，而不是挂在 registry 上。

### 现状（已核对的行号）

- `clinical_calculators/registry.py:112` — `__init__` 里初始化 `self._last_search_response = SearchResponse("no_match", ())`
- `clinical_calculators/registry.py:147` — `def search_response(self)`
- `clinical_calculators/registry.py:152` — `def search_match(self, calculator_id)`
- `clinical_calculators/registry.py:185-186` — `_search` 结尾写入 `self._last_search_response` 并据此返回
- `clinical_calculators/search.py:122/138/144` — 已有 `SearchMatch` / `SearchHit` / `SearchResponse`

调用点（全仓库，已 grep 确认，只有这些）：

- `scripts/clinical_calculator.py:577,582,585,588`
- `tests/test_search.py:41`（`registry.search_match("CALC-0049")`）
- `tests/test_search.py:86`（`registry.search_response()`）

### 要做的改动

**1.1** 在 `clinical_calculators/registry.py` 里新增两个 frozen dataclass（放 registry.py 而不是 search.py，
因为 search.py 不认识 `CalculatorSkill`，放过去会产生 import 环）：

```python
@dataclass(frozen=True)
class CalculatorSearchResult:
    skill: CalculatorSkill
    match: SearchMatch


@dataclass(frozen=True)
class CalculatorSearchResponse:
    status: str
    results: tuple[CalculatorSearchResult, ...]
    suggestions: tuple[str, ...] = ()

    @property
    def skills(self) -> list[CalculatorSkill]:
        """返回技能列表，供保持旧签名的 search* 方法复用。"""

    def match_for(self, calculator_id: str) -> SearchMatch | None:
        """在本次响应内按 ID 找 match；不读任何 registry 状态。"""
```

两个类都要加进 `clinical_calculators/__init__.py` 的导出（跟现有导出风格一致）。

**1.2** 新增 4 个 `*_detailed` 方法，返回 `CalculatorSearchResponse`：

- `search_detailed(query, limit=20)`
- `search_runnable_detailed(query, limit=20)`
- `search_layer_detailed(query, layer, limit=20)`
- `search_released_detailed(query, limit=20)`

**1.3** 现有 4 个方法 `search` / `search_runnable` / `search_layer` / `search_released`
**签名和返回类型完全不变**（仍返回 `list[CalculatorSkill]`），内部改成调用对应的
`*_detailed` 再取 `.skills`。这样外部调用方零改动。

**1.4** 删除 `search_response()`、`search_match()`、以及 `_last_search_response` 字段的所有赋值和读取。
改完后 `registry.py` 里不能再有任何"上一次检索"的可变状态。
`_search` 改成返回 `CalculatorSearchResponse`（`no_match` 时的 catalog 兜底建议逻辑保持原样，不要改行为）。

**1.5** 顺手删掉 `search_runnable` 附近那段永远不会执行的死代码（生成时留下的 `if False` 分支，如果还在）。

**1.6** 更新 `scripts/clinical_calculator.py` 的 `search` 分支改用 `*_detailed`。
**输出的 JSON 字段名、字段顺序、语义必须完全不变**（`query` / `scope` / `status` / `count` / `results` / `suggestions`）。

**1.7** 更新 `tests/test_search.py:41` 和 `:86` 两处改用新 API。

**1.8** 新增 `tests/test_search_result_isolation.py`，回归保护这个缺陷：
先做一次检索拿到 `CalculatorSearchResponse`，再做一次不同的检索，
断言第一个响应对象的 `results` 和 `match_for(...)` 仍然返回原来的值（不受第二次检索影响）。

## 任务 2：给路由棘轮留余量，并加一个绝不许回归的 critical 子集

### 缺陷

`reports/routing_baseline.json` 现在是这样，把基线钉死在满分：

```json
{"case_count": 130, "mrr": 1.0, "recall_at_1": 1.0, "recall_at_5": 1.0, "zero_result_rate": 0.0}
```

零容忍。我在阶段 C 自查时就已经撞过一次：一个正确的改动让 recall@1 掉到 0.961538，CI 直接红。
而这个 1.0 本身含水分——130 条用例里 81 条（62%）是把库存全名原样贴回去当查询，
接近恒等映射，没什么区分度。所以既要留余量，又要保证真正重要的用例一条都不许掉。

### 要做的改动

**2.1** 给 `evaluation/routing_cases.csv` 加一列 `critical`，取值 `yes` / `no`。
下面这 11 条标 `yes`，其余全部 `no`。这 11 条 = 我实测过的 5 个失败查询 + Wells DVT/PE 同名歧义
+ CHA₂DS₂-VASc 的缩写变体（当前它们都在 recall@1 命中，标 critical 不会一上线就红）：

```
肺栓塞概率
脓毒症
小儿脱水
预测死亡率的评分
chads vasc
Wells DVT
Wells PE
CHA（2）DS（2）-VASc
CHA₂DS₂-VASc
cha2ds2vasc
qSOFA
```

**2.2** `scripts/evaluate_routing.py`：

- `REQUIRED_COLUMNS` 加上 `critical`；`load_cases` 校验取值只能是 `yes` / `no`。
- `category` 的白名单从 `{direct, synonym}` 扩到 `{direct, synonym, abbrev, scenario, partial}`
  （held-out 用例集用到了后三个，见任务 3）。
- 报告里新增 `critical_recall_at_1` 和 `critical_case_count` 两个顶层指标。
- 现有的 `by_category` / `by_locale` / `failures` 保持不变。
- `main()` 加两个可选参数 `--cases` 和 `--report`，默认值就是现在的默认路径。
  这样同一个脚本能跑两个用例集。

**2.3** 把 `reports/routing_baseline.json` 改成"观测值 + 门槛值"两段结构：

```json
{
  "observed": { ... 主用例集实测值 ... },
  "thresholds": { ... 门槛，留余量 ... },
  "heldout_observed": { ... },
  "heldout_thresholds": { ... },
  "notes": [ ... ]
}
```

门槛值这样设（余量是有意留的，不是实测值）：

- 主集：`recall_at_1 >= 0.97`、`recall_at_5 >= 0.98`、`mrr >= 0.97`、`zero_result_rate <= 0.02`
- 主集 `critical_recall_at_1 >= 1.0` — **这一项不留任何余量，必须严格满分**
- held-out：`recall_at_1 >= 0.83`、`recall_at_5 >= 0.96`、`mrr >= 0.90`、`zero_result_rate <= 0.02`

`notes` 数组里必须如实写清两件事（不要美化、不要删）：

- 主用例集 130 条里有 81 条是把库存全名原样贴回来当查询，接近恒等映射，
  所以主集的高分**不能**当作泛化能力的证据。
- `thresholds` 是有意预留的余量，不等于实测值；只有 `critical_recall_at_1` 不留余量。

**2.4** `tests/test_routing_evaluation.py`：

- 断言改成拿实测值跟 `thresholds` 比，而不是跟上一次的观测值比。
- `critical_recall_at_1` 必须 `== 1.0`。
- **失败信息必须点名具体掉了哪条 critical 用例**（列出 query、expected_ids、实际 top5），
  不能只报一个数字。这是这条门禁有用的前提。
- 再加一条守卫测试：断言 `critical` 列里至少包含 2.1 列出的那 11 条查询，
  防止后人靠把用例改成 `no` 来绕过门禁。
- 保留现有的 `test_routing_case_set_is_large_and_categorized`，按新的 category 白名单调整。

## 任务 3：把 30 条 held-out 用例入库

### 背景

我在阶段 C 验收时另建了 30 条 codex 没见过的查询，实测 recall@1 从 73.33% 提到 86.67%。
但这批用例当时只存在我的 shell 历史里，仓库里没人能复现这个数字。现在把它入库。

**这 30 条的 `expected_ids` 我已经逐条对照 `clinical_calculator_inventory_full.csv` 的名称和 ID 核过，
直接照抄下表，不要改动、不要增删、不要"顺手修正"。**

**3.1** 新建 `evaluation/routing_cases_heldout.csv`，列结构跟主用例集一致
（`query,expected_ids,locale,category,critical,note`），`critical` 全部填 `no`。
30 行内容（`query | expected_ids | locale | category`）：

```
SOFA | CALC-0004 | en | abbrev
APACHE | CALC-0019 | en | abbrev
MAP | CALC-0008 | en | abbrev
肝纤维化 | CALC-0736;CALC-0737 | zh-CN | scenario
上消化道出血风险 | CALC-0728;CALC-0729 | zh-CN | scenario
早产风险 | CALC-0764 | zh-CN | scenario
川崎病 | CALC-0773;CALC-0774 | zh-CN | scenario
意识障碍 | CALC-0001;CALC-0827 | zh-CN | scenario
婴儿发热低危 | CALC-0690;CALC-0691 | zh-CN | partial
新生儿风险 | CALC-0771;CALC-0772 | zh-CN | partial
肝癌分期 | CALC-0739 | zh-CN | partial
子痫 | CALC-0765 | zh-CN | partial
liver fibrosis | CALC-0736;CALC-0737 | en | scenario
upper GI bleed | CALC-0728;CALC-0729 | en | scenario
preterm birth risk | CALC-0764 | en | scenario
Kawasaki disease | CALC-0773;CALC-0774 | en | scenario
consciousness impaired | CALC-0001;CALC-0827 | en | scenario
儿童对乙酰氨基酚 | CALC-1099 | zh-CN | partial
儿童布洛芬剂量 | CALC-1100 | zh-CN | direct
pediatric acetaminophen | CALC-1099 | en | scenario
肩难产 | CALC-0767 | zh-CN | partial
产科早期预警 | CALC-0766 | zh-CN | partial
肌松恢复 | CALC-0832 | zh-CN | scenario
train of four | CALC-0832 | en | abbrev
胶质瘤疗效 | CALC-0795 | zh-CN | scenario
RANO criteria | CALC-0795 | en | abbrev
不良童年 | CALC-0874 | zh-CN | partial
pulmonary embolism wells | CALC-0051 | en | partial
dvt wells score | CALC-0050 | en | partial
儿童肥胖BMI | CALC-0775 | zh-CN | partial
```

`note` 列如实写，例如「阶段 C 验收独立 held-out 用例，ID 已对照库存核查」，
其中依赖同义词表的那几条注明依赖关系。不要编造理由。

**3.2** held-out 指标写进 `reports/routing_baseline.json` 的 `heldout_observed`，
并生成 `reports/routing_evaluation_heldout.json`。

**3.3** `tests/test_routing_evaluation.py` 把 held-out 集也纳入门禁（用 `heldout_thresholds`）。

**3.4** `evaluation/README.md` 补一节说明 held-out 集，其中**必须原样保留**这段坦白
（不许省略、不许改写成好听的说法）：

> 这 30 条是阶段 C 验收时的独立 held-out 集，其中 `abbrev` / `scenario` / `partial`
> 三类查询不在主用例集里。需要注意：86.67% 这个 recall@1 **不是干净的泛化估计**——
> 在看到失败案例之后，同义词表补了 4 条短语级映射，指标才从 73.33% 提到 86.67%。
> 也就是说这批用例已经被拟合过一次。下一轮评测需要再建一批全新的、
> 从未参与过任何调优的用例，才能得到干净的泛化估计。

同时补一句：主用例集 130 条里 81 条是全名原样贴回，说明主集的高分不代表泛化能力。

**3.5** `.github/workflows/test.yml` 在现有 "Evaluate routing quality" 之后加一步跑 held-out 集
（用 `--cases` / `--report` 参数指到 held-out 的两个路径）。

## 验收

改完请自己跑并把结果贴给我：

```bash
# 1. 全量测试（改动前是 969 passed）
python3.12 -m pytest -q

# 2. 两个用例集的指标
python3 scripts/evaluate_routing.py
python3 scripts/evaluate_routing.py --cases evaluation/routing_cases_heldout.csv \
    --report reports/routing_evaluation_heldout.json

# 3. 注册表校验
python3 scripts/clinical_calculator.py validate
```

**4. 重构等价性验证（这条最重要）。**
我已经把改动前的 CLI 输出存在 `/tmp/c2_before/` 了，共 8 个查询：
`肺栓塞概率`、`脓毒症`、`小儿脱水`、`预测死亡率的评分`、`chads vasc`、`完全不存在的东西xyz`、`Wells DVT`、`Wells PE`
（文件名是把查询里的空格换成下划线，`.json` 结尾）。
改完后对每个查询重新跑 `python3 scripts/clinical_calculator.py search "<query>"`（注意：**不带** `--all`，
跟存基线时的命令一致），跟 `/tmp/c2_before/` 里对应文件做 diff。
**8 个 diff 必须全为空。** 如果有任何一个不为空，说明重构改变了行为，要修到为空为止，
不要改基线文件来迁就。

**5. 门禁有效性验证。** 证明 critical 门禁真的会拦住回归：
临时改坏检索（比如注掉 `search.py` 里 CJK bigram 的生成），跑测试，
确认它失败**并且点名了具体掉落的 critical 用例**，然后把改动还原。
把这一步的失败输出也贴给我。注意还原后要重新跑一遍全量测试确认干净。

最后汇报：主集指标、critical 指标、held-out 指标各是多少，
门槛余量是多少，8 个 CLI diff 是否全空，门禁有效性验证的输出。

