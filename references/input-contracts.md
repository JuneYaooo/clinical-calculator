# 输入契约

内置可执行计算器的输入契约位于 `clinical_calculators/contracts/`。文件按
`clinical_calculators/calculators/common/` 下的实现模块命名，顶层以计算器 ID 为键：

```json
{
  "CALC-XXXX": {
    "inputs": [
      {
        "name": "implementation_input_name",
        "type": "number",
        "unit": "source-backed unit",
        "minimum": 0,
        "item_text": "来源中的条目原文",
        "description": "来源中的输入说明"
      }
    ]
  }
}
```

完整字段和约束见 `clinical_calculators/contracts/_schema.md`。加载器会拒绝未知字段、非法类型、
倒置边界、无效 choices/points、孤儿 ID，以及与实现 `required_inputs` 不一致的输入名。

## 优先级

`CalculatorSkill` 按以下顺序确定输入 schema：

1. 调用方显式传入的 `input_schema`，供自定义 manifest 使用；
2. `clinical_calculators/contracts/` 中按 ID 声明的内置契约；
3. 旧的 `_infer_input_spec` 启发式兜底，仅服务尚未回填的内置条目。

覆盖率脚本会统计第三类兜底及其 `any`/空描述缺口，CI 基线只允许覆盖改善或持平。

## 为计算器编写契约

1. 确认条目是可执行实现，并复制实现注册的全部输入名，不改名、不漏项。
2. 从该条目已有的 `metadata.formula`、`metadata.inputs`、`metadata.interpretation` 或已记录来源
   摘录 `item_text` 与 `description`；保持原文，不翻写成新的医学定义。
3. 只从现有实现的取值调用和边界检查记录 `type`、`minimum`、`maximum`；单位、choices 和 points
   同样必须有明确来源。
4. 来源不能证明的字段保留默认空值。空值会进入覆盖缺口，便于之后人工回源；猜测值却会形成
   看似完整、实际不可审计的错误契约，因此留空始终优于臆造。
5. 运行 `validate`、覆盖率报告和完整 pytest，并随有意改善同步下调覆盖率基线。

新增或修改可执行计算器时，契约 JSON 必须与实现、测试一起提交。
