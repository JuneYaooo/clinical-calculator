# 阶段 A 执行任务书：输入契约基础设施

前置阅读：`docs/design/2026-07-26-extensible-calculator-skill.md` 第 3.1、3.2、5 节。

本阶段**只建基础设施 + 回填一个示范批次**，不回填全部 643 个计算器。

## 目标

让内置计算器的输入契约从"靠变量名猜"变成"声明的数据"，并建立防倒退的 CI 棘轮。

## 交付物

### 1. `InputSpec` 扩展（`clinical_calculators/models.py`）

新增可选字段，全部带默认值，现有所有构造调用不得受影响：

- `item_text: str = ""` — 该输入在原量表中的条目原文（中文）
- `points: float | None = None` — 该条目在量表中的分值（仅计分类量表）
- `optional: bool = False`
- `default: Any = None`
- `unit_alternatives: tuple[tuple[str, str, float], ...] = ()` — `(unit, op, factor)`，
  `op` 取 `"multiply"` 或 `"divide"`；本阶段只需能声明与序列化，换算逻辑留给阶段 D

`required` 字段已存在，保持不变。

### 2. 契约数据目录 `clinical_calculators/contracts/`

- 每个专科一个 JSON，文件名与 `clinical_calculators/calculators/common/` 下的实现模块同名
  （例：`emergency_scores.json` 对应 `emergency_scores.py`）。
- 结构见设计稿 3.1 节。顶层是 `{calculator_id: {"inputs": [...]}}`。
- 写 `clinical_calculators/contracts/_schema.md` 说明每个字段的含义、必填性与取值约束。
- JSON 里禁止出现未在 `_schema.md` 声明的字段；加载器遇到未知字段必须报错。

### 3. 契约加载与校验（`clinical_calculators/contracts.py` 或包内 `__init__.py`）

- 加载全部契约 JSON，返回 `dict[str, tuple[InputSpec, ...]]`。
- 解析失败、未知字段、`type` 非法、`minimum > maximum`、`choices` 少于 2 项、
  `points` 出现在非 boolean/number 输入上 —— 全部抛出明确异常。
- `CalculatorSkill.__init__` 的契约优先级改为：
  1. 显式传入的 `input_schema`（自定义 manifest）
  2. `contracts/` 中按 calculator ID 声明的契约
  3. 现有 `_infer_input_spec` 兜底

  第 3 条保留但必须可统计（见交付物 5）。
- `registry.load_registry` 加载时校验：契约声明的输入名集合必须与该 ID 在
  `IMPLEMENTATIONS_BY_ID` 中的 `required_inputs` **完全一致**（顺序无关）。不一致直接
  抛异常并指明 ID、多出的名、缺失的名。
- 契约中出现的 ID 若不在注册表内，同样报错（防止改名后留下孤儿契约）。

### 4. 示范批次：急诊与重症医学

只回填 `category == "急诊与重症医学"` 且 `implementation_level == "complete"` 的条目。
先用脚本列出这批 ID 与其 `required_inputs`，再逐个写契约。

**内容来源的硬约束（最重要）**：`item_text`、`description`、`points`、`choices`、
`minimum`/`maximum` 只能取自该条目已有的 `metadata.formula`、`metadata.inputs`、
`metadata.interpretation` 文本，或 `metadata.source_url` 指向的已记录来源。
取不到就**留空**，让它继续计入棘轮缺口。**绝对不允许**由模型凭记忆补写分值、阈值、
条目原文、单位、边界。宁可留空也不要臆造 —— 这是本仓库的核心红线。

类型判定可以从现有实现代码反推（例如函数内调用 `boolean(inputs, "x")` 即可确定
`x` 是 boolean，调用 `number(...)` 且检查 `<= 0` 即可确定下界），这属于读代码不是猜。

### 5. 覆盖率报告与 CI 棘轮

- 新增 `scripts/report_contract_coverage.py`，输出 `reports/contract_coverage.json`：

  ```json
  {
    "executable_calculators": 643,
    "calculators_with_declared_contract": 0,
    "calculators_without_declared_contract": 643,
    "inputs_total": 2334,
    "any_typed_inputs": 1358,
    "inputs_without_description": 2334
  }
  ```

- 新增 `reports/contract_coverage_baseline.json`，内容为**回填后**的实测值。
- 新增 `tests/test_input_contract_coverage.py`：实测值中
  `calculators_without_declared_contract`、`any_typed_inputs`、`inputs_without_description`
  必须 **≤** 基线中的对应值；`calculators_with_declared_contract` 必须 **≥** 基线。
  断言失败信息要写清"契约覆盖不得倒退，如确为有意变更请同步更新基线文件"。
- 把覆盖率报告生成与该测试接入 `.github/workflows/test.yml`。

### 6. 契约质量测试（`tests/test_input_contracts.py`）

- 契约与实现 `required_inputs` 一致性（正例 + 一个人为构造的不一致必须被拒绝）。
- 已声明契约的条目：`info` 输出的每个输入都有非空 `value_type` 且不为 `"any"`。
- 至少 3 个已回填计算器的边界拒绝断言：越上界、越下界、错类型分别返回
  `status == "invalid_inputs"`，且报错信息含该输入名。
- 至少 1 个 boolean 输入传字符串 `"true"` 被拒绝（现有实现只接受 JSON bool 或 0/1）。
- 契约里带 `points` 的条目：分值之和须与该量表 `metadata.formula` 中可核对的总分一致；
  无法核对的不要写这条断言。

### 7. 文档

- 新增 `references/input-contracts.md`：契约格式、优先级、如何为新计算器写契约、
  为什么留空优于臆造。
- `CONTRIBUTING.md` 增加一条：新增或修改可执行计算器必须同时提交契约 JSON。
- 不要改 `SKILL.md` 主体结构，只在"Availability and safety"或核心流程处加一句指向
  `references/input-contracts.md` 的引用（保持 SKILL.md 精简）。

## 不要做的事

- 不改任何现有 calculator ID、输入名、输出结构。
- 不改现有 CLI 子命令的行为与输出字段语义；新字段一律追加且可选。
- 不动 `clinical_calculators/extensions.py` 的 manifest schema（阶段 D 才改）。
- 不重构 `calculators/common/__init__.py` 那张注册字典（后续阶段评估）。
- 不实现单位换算逻辑（阶段 D）。
- 不改检索逻辑（阶段 C）。
- 不引入任何第三方运行时依赖。
- 不修改 `clinical_calculator_inventory_full.csv` 的医学内容。

## 验收

按顺序全部通过：

```bash
python3 scripts/clinical_calculator.py validate
python3 scripts/report_contract_coverage.py
python3.12 -m pytest -q          # 存量 937 项 + 新增测试必须全绿
python3 scripts/clinical_calculator.py info CALC-0009   # 已回填条目应显示具体类型与条目原文
```

最后在回复里报告：回填了多少个计算器、多少个输入、`any` 类型从 1358 降到多少、
缺描述从 2334 降到多少、以及哪些输入因为来源不足而**故意留空**（这部分要逐条列出，
便于人工回源）。
