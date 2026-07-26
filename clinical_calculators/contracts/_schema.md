# 内置计算器输入契约

契约 JSON 按实现模块命名，顶层对象的键是计算器 ID，值目前只能包含 `inputs`。`inputs`
必须是非空数组，且输入名不得重复。加载器会把每个输入转换为 `InputSpec`，并在注册表加载时
核对输入名集合与实现的 `required_inputs` 完全一致。

## 输入字段

| 字段 | 必填 | 类型与约束 | 含义 |
| --- | --- | --- | --- |
| `name` | 是 | 非空 Python 标识符 | 与实现完全一致的输入名 |
| `type` | 是 | `number`、`boolean`、`choice`、`string`、`sequence` | 运行时值类型；声明契约不接受 `any` |
| `unit` | 否 | 字符串，默认 `""` | 来源明确的输入单位；不明确时留空 |
| `required` | 否 | boolean，默认 `true` | 是否为必需输入 |
| `minimum` | 否 | 有限数值 | 包含式下界 |
| `maximum` | 否 | 有限数值，且不得小于 `minimum` | 包含式上界 |
| `choices` | `type=choice` 时是 | 至少两个互不重复的非空字符串 | 允许的离散值；其他类型禁止使用 |
| `description` | 否 | 字符串，默认 `""` | 来源中对该输入的说明 |
| `item_text` | 否 | 字符串，默认 `""` | 原量表中的中文条目原文 |
| `points` | 否 | 有限数值；仅 `boolean` 或 `number` | 来源可核对的固定条目分值 |
| `optional` | 否 | boolean，默认 `false` | 可选输入标记；本阶段的内置示范批次均为必需输入 |
| `default` | 否 | 任意 JSON 值，默认 `null` | 可选输入的缺省值 |
| `unit_alternatives` | 否 | 三元数组的数组，默认 `[]` | 每项为 `[unit, op, factor]`；`op` 只能为 `multiply` 或 `divide` |

`unit_alternatives` 本阶段只声明和序列化，不执行换算。所有文本、分值、choices、单位和边界
都必须能回溯到该条目已有 metadata 或实现代码；来源不足时保留默认空值，不得推测补写。

JSON 中不得出现本文件未声明的字段。计算器定义层也只允许 `inputs`；未知字段、解析错误、
非法类型、倒置边界、少于两个 choices，以及非 boolean/number 输入上的 points 都会使加载失败。
