# 全面且可扩展的临床计算器 Skill：设计稿

状态：待执行
日期：2026-07-26
执行方式：由 codex 分阶段实现，每阶段独立可验证、可回滚

## 1. 现状与问题

基线（`python3 scripts/clinical_calculator.py summary`）：1054 个有效条目、643 可执行、937 项测试。
分层（executable / source_candidate / guidance_knowledge / controlled_content）与"可执行 ≠ 已临床发布"
的设计是这个仓库最强的部分，本设计全部保留。

实测发现四个会直接导致 Agent 给出错误结果的缺口：

| 编号 | 问题 | 实测证据 | 后果 |
| --- | --- | --- | --- |
| P1 | 内置计算器的输入契约靠命名启发式推断，不是声明的 | 2334 个输入中 1358 个 `value_type=any`，2334 个全部 `description=""`；`CALC-0049` 的 `congestive_heart_failure` 类型为 `any` | Agent 不知道该传 bool 还是分数；不知道"血管疾病"含哪些病；越界值不被拦截 |
| P2 | 中文检索无分词，整串子串匹配 | `肺栓塞` 库内 10 条，查 `肺栓塞概率` 返回 0；`脓毒症`、`小儿脱水`、`预测死亡率的评分` 均返回 0 | 检索失败后 Agent 退回记忆编公式，正是本项目要防的失败模式 |
| P3 | 来源与版本治理缺位 | 643 个可执行条目中 624 个无版本号，344 个 `source_url` 指向 mdcalc.com / qxmd.com 等落地页 | 无法判断实现对应哪个版本；`medical_review_ready` 只有 19 条 |
| P4 | 只测公式，不测路由 | 53 个测试文件全部针对公式正确性，零覆盖"自然语言 → 正确计算器 ID" | 文献一致指出选错计算器是 LLM 用计算器的首要失败点，本仓库无门禁 |

外加两个扩展性问题：

- 注册表是 `calculators/common/__init__.py` 里 3362 行手写字典，输入名在函数、注册元组、测试三处重复。
- 自定义计算器只有 `scaffold / validate-custom / install-custom`，装完无法 `list`、`uninstall`、`export`；不支持可选输入、缺省值、单位换算。

## 2. 设计原则

1. **声明优先于推断。** 每个可执行计算器的输入契约必须是声明的数据，不是从变量名猜的。
2. **内置与自定义同一套契约。** `info` 的输出结构对两者完全一致，Agent 只需学一种格式。
3. **不新增医学内容。** 描述与条目原文只能来自仓库已有的 `metadata.formula` / `inputs` / `interpretation`
   字段或明确来源，禁止由模型补写系数、阈值、表格单元格、版本。
4. **棘轮而非大爆炸。** 契约回填按专科分批，用 CI 断言"未声明数量只减不增"，避免一次性改 643 个条目引入臆造。
5. **运行时仅标准库。** 测试依赖 pytest，不引入 jieba 等分词库；中文检索用字符 bigram 自建索引。
6. **形态保持单一 Skill 仓库。** 不加 MCP server、不发 PyPI；精力全部投入覆盖度、契约、检索、扩展。

## 3. 目标架构

### 3.1 输入契约（解决 P1）

新增 `clinical_calculators/contracts/`，按专科一个 JSON 文件，与计算器实现模块同名：

```
clinical_calculators/contracts/
├── _schema.md              # 字段说明
├── egfr.json
├── cardiac_risk_scores.json
└── ...
```

单个条目的结构：

```json
{
  "CALC-0049": {
    "inputs": [
      {
        "name": "congestive_heart_failure",
        "type": "boolean",
        "item_text": "充血性心衰 / 左心功能障碍",
        "description": "既往或当前充血性心衰、或影像证实的左心室功能障碍",
        "points": 1
      },
      {
        "name": "age_years",
        "type": "number",
        "unit": "years",
        "minimum": 0,
        "maximum": 130,
        "item_text": "年龄",
        "description": "65-74 岁计 1 分，≥75 岁计 2 分"
      }
    ]
  }
}
```

`InputSpec`（`models.py`）新增可选字段：`item_text`、`points`、`optional`、`default`、
`unit_alternatives`。全部有默认值，现有构造调用不受影响。

契约解析优先级，在 `CalculatorSkill.__init__` 内确定：

1. 自定义 manifest 显式传入的 `input_schema`（最高）
2. `contracts/` 中按 ID 声明的契约
3. 现有 `_infer_input_spec` 启发式（兜底，仅供未回填条目）

`registry.py` 在加载时校验：契约声明的 `name` 集合必须与 `IMPLEMENTATIONS_BY_ID` 里该 ID 的
`required_inputs` 完全一致（顺序无关），不一致直接报错。这样契约与实现无法静默漂移。

### 3.2 回填批次与 CI 棘轮

按 `metadata.commonness` 与专科分批，顺序：

1. 急诊与重症医学
2. 心血管医学
3. 肾脏与电解质
4. 肝病与消化
5. 呼吸
6. 儿科
7. 其余专科

每批交付：契约 JSON + 该批的契约一致性测试 + 至少一个越界/错类型被拒绝的断言。

新增 `tests/test_input_contract_coverage.py`，读取 `reports/contract_coverage.json` 里的基线：

```json
{"undeclared_calculators": 643, "any_typed_inputs": 1358, "inputs_without_description": 2334}
```

断言当前实测值 **小于或等于** 基线，并在回填后同步下调基线。数值只能单调下降。

### 3.3 检索与路由（解决 P2）

新增 `clinical_calculators/search.py`，替换 `registry.py` 里的 `_normalize_search_text` /
`_query_groups` / `search`。`registry.search*` 的签名与返回类型保持不变。

- **归一化**：NFKC、casefold、全角转半角、标点转空格；`CHA（2）DS（2）` 与 `CHA2DS2` 归一到同形。
- **分词**：拉丁段按词切分并保留去标点/去数字变体（`CHA2DS2-VASc` → `cha2ds2vasc`、`chadsvasc`）；
  CJK 段同时产出单字与 bigram（`肺栓塞` → `肺`、`栓`、`塞`、`肺栓`、`栓塞`）。
- **倒排索引**：token → (calculator_id, field)，注册表加载时构建一次。
- **字段权重**：`name_cn`/`name_en`/`alias` 10，`scenario` 6，`subspecialty` 4，`category` 3，
  `purpose` 2，`source` 1。
- **打分**：加权命中和 × 查询 token 覆盖率；完全等名、前缀命中额外加成。覆盖率机制让
  `肺栓塞概率` 在 `概率` 未命中时仍能靠 `肺栓塞` 返回结果。
- **同义词数据化**：现在硬编码在 `registry.py` 的 `SEARCH_ALIASES` 迁到
  `clinical_calculator_search_terms.csv`（列：`term`,`expands_to`,`note`），可由临床同事直接维护，
  加载时校验非空、无自环。
- **零结果兜底**：降级为部分 token 匹配并返回 `suggestions`，同时给出
  `status: "no_match"`，让 Agent 知道该换词而不是退回记忆。
- **可解释**：每条结果附 `match: {score, coverage, matched_fields, matched_terms}`。

### 3.4 路由评测与质量门（解决 P4）

```
evaluation/
├── routing_cases.csv     # query, expected_ids(分号分隔), locale, note
└── README.md
```

新增 `scripts/evaluate_routing.py`：跑全部 case，计算 recall@1 / recall@5 / MRR 与零结果率，
输出 `reports/routing_evaluation.json`。纯确定性、无需 LLM，可进 CI。

首批 case ≥ 120 条，必须覆盖：中文全名、中文简称（房颤评分）、英文缩写（qSOFA）、
缩写变体（chads vasc）、场景化提问（评估房颤卒中风险用什么）、易混同名（Wells DVT vs PE）、
本次实测失败的全部查询（肺栓塞概率、脓毒症、小儿脱水、预测死亡率的评分）。

再加一项零成本的契约漂移检查：每个 case 可选声明 `expected_inputs`，断言目标计算器的契约
恰好声明了这些输入名。

CI 门禁：`reports/routing_baseline.json` 记录基线，recall@1 与 recall@5 不得低于基线，
零结果率不得高于基线。

### 3.5 自定义计算器全流程 UX

新增 CLI 子命令：

| 命令 | 作用 |
| --- | --- |
| `list-custom` | 列出所有已发现的自定义计算器（ID、名称、来源、目录、schema 版本） |
| `uninstall-custom <ID>` | 删除已安装 manifest；先打印将删除的文件，`--yes` 才实际删除 |
| `export-custom <ID> --output <path>` | 导出为可分享 manifest |
| `test-custom <path\|ID>` | 单独跑 manifest 内嵌 test_cases 并输出逐例结果 |

schema 保持 v2，只加**可选**字段（旧 manifest 继续有效）：

- `inputs[].optional` + `inputs[].default`：可选输入与缺省值。
- `inputs[].unit_alternatives`：`[{"unit": "µmol/L", "divide": 88.4}]`，声明式换算，禁止推断。
  CLI 增加 `--input-unit <name>=<unit>`，运行结果同时回报原始值、换算值与所用换算因子。
- 顶层 `tags`、`aliases`：进检索索引，让自定义计算器也能被自然语言找到。

单位换算同样支持内置计算器：契约 JSON 的 `unit_alternatives` 走同一条代码路径。这是本轮
最直接的临床安全收益（mg/dL 与 µmol/L 混用是肌酐类计算器的经典事故）。

草稿闭环补齐：`custom_calculators/drafts/` 下的草稿由 `validate-custom` 报出确切缺口，
`install-custom` 继续拒绝占位来源，安装后必须 `info` + 一个来源已知答案 `run` 验证。

### 3.6 来源与版本治理（解决 P3）

`CalculatorSkill` 新增派生属性 `source_quality`，按规则判定：

| 等级 | 判定规则 |
| --- | --- |
| `primary` | source_url 指向原始文献 / DOI / 官方指南全文，且有版本或年份 |
| `official_tool` | 指向官方机构的具体计算器页面（CDC、WHO、KDIGO 等），且有版本或年份 |
| `platform` | 指向 MDCalc、QxMD 等平台的**具体**计算器页面 |
| `landing_page` | 指向平台或机构根路径 / 汇总页（当前 344 条） |
| `unknown` | 无可用来源信息 |

人工核对结果记录在 `reports/calculator_source_provenance.csv`（列：`id`,`source_quality`,
`source_url`,`version`,`verified_by`,`verified_at`,`note`），规则判定仅作默认值，CSV 可覆盖。

`search` / `info` / `run` 输出统一带 `source_quality` 与 `caveats`。当质量为 `landing_page`
或 `unknown`、或缺版本时，`caveats` 明确写入"来源为平台落地页、版本未知，使用前须回原始文献核对"，
让 Agent 必须向用户如实转述，而不是默认可信。

新增 `provenance-backlog` 子命令：按 `commonness` 排序输出最该补来源的条目，把 P3 变成
可认领的贡献任务。

### 3.7 文档与仓库整理

- `SKILL.md` 保持精简（当前 7.2 KB 合理），新增细节全部下沉到 `references/`：
  `references/search-and-routing.md`、`references/input-contracts.md`、`references/evaluation.md`。
- `CONTRIBUTING.md` 补充：新增/修改计算器必须同时提交契约 JSON 与路由 case。
- `README.md`、`docs/implementation-readiness.md` 里的所有数字改为由脚本从注册表实测生成后填入，
  不再手写（当前 `implementation-readiness.md` 的 667/55/325/91 与实测 593/50/316/95 已经不一致）。
- `docs/parallel_handoffs/`、`docs/superpowers/` 已在 `.gitignore` 中，确认未被跟踪即可。

## 4. 执行阶段

| 阶段 | 内容 | 验证 |
| --- | --- | --- |
| A | 契约基础设施：`InputSpec` 扩展、`contracts/` 加载器、一致性校验、覆盖率报告与棘轮测试 | `validate` 通过；棘轮测试通过；937 项存量测试全绿 |
| B | 契约回填批次 1-3（急诊重症、心血管、肾脏电解质） | 每批含越界拒绝断言；棘轮基线下调 |
| C | 检索重写 + 同义词 CSV + 评测集 + CI 门禁 | 实测失败的 4 个查询全部返回正确条目；recall 门禁生效 |
| D | 自定义计算器 UX：4 个新子命令 + 可选输入 + 单位换算 | 新命令有测试；旧 manifest 兼容性测试通过 |
| E | 来源治理：`source_quality` + provenance CSV + caveats + backlog 命令 | `info`/`run` 输出含 caveats；backlog 排序正确 |
| F | 文档下沉、数字自动生成、契约回填批次 4-7 | 文档数字与 `summary` 实测一致 |

阶段 A 是其余全部阶段的前置。C 与 D、E 相互独立，可并行。

## 5. 约束（对执行方的硬性要求）

1. 运行时只用 Python 标准库；测试只用 pytest。
2. **不得新增任何医学内容**。契约里的 `item_text`、`description`、`points` 只能取自该条目已有的
   `metadata.formula` / `inputs` / `interpretation` 文本或已记录来源。取不到就留空并计入棘轮缺口，
   绝不允许由模型补写。系数、阈值、表格单元格、版本号同理。
3. 不改变现有 ID、输入名、输出结构与 CLI 现有子命令的行为；新字段一律可选。
4. 每阶段结束必须跑 `python3 scripts/clinical_calculator.py validate` 与 `python3 -m pytest -q`，
   全绿才算完成。
5. 文档与 README 中的任何统计数字必须来自实测输出，不得手写或沿用旧值。
6. 分层语义不得弱化：`complete` ≠ 已临床发布，`released` 允许列表保持为空。
