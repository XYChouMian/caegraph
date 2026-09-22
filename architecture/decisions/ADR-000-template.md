# ADR-000: ADR 模板（Template）

> 复制本文件为 `ADR-NNN-短标题.md`（NNN 三位递增编号），删除本说明后填写。由 Architecture Agent 在重大架构决策时创建；状态只有 accepted / superseded（被 ADR-XXX 取代）两种。编号必须单调递增且不得复用已删除或合并的历史编号；当前下一编号为 ADR-020。

- 编号：ADR-NNN
- 标题：<一句话决策>
- 日期：<确认当前日期后填写 YYYY-MM-DD>
- 状态：accepted | superseded（被 ADR-XXX 取代）
- 关联：相关 Phase / UML 节点 / 被取代的 ADR

## 背景（Context）

<面对什么问题？约束是什么？>

## 决策（Decision）

<决定了什么？>

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| <方案 A> | 否决 | <为什么> |
| <方案 B（采纳）> | 采纳 | <为什么> |

## 影响（Consequences）

<正面影响、代价、后续必须做的事>

填写日期或修订历史前，必须读取并执行 `.agent/skills/time/SKILL.md`；历史日期必须有明确证据，不得凭当前日期猜测。

## 可选不变式登记（仅在符合条件时）

只有本 ADR 包含有限、可判定真伪且需要逐条关联测试的实现约束时，才创建同目录 `ADR-NNN-invariants.yaml`；原则、流程或定位类 ADR 不创建。Markdown ADR 是唯一决策真源，YAML 只登记可审计不变式与刻意未冻结项。

```yaml
adr: "ADR-NNN"
version: "vN"
extracted_from: "vN decision text (baseline commit <git-commit-hash>)"
invariants:
  - id: "ADR-NNN-D1-01"
    statement: "中文、可判定真伪的不变式。"
    decision: "D1"
    test_mapping: "TEST_MISSING"
    missing_reason: "中文理由；仅在 TEST_MISSING 于 Phase 收尾时必填。"
    # canonical_statement: "Optional English canonical statement."
explicitly_not_frozen:
  - item: "中文描述的刻意未冻结项。"
    source: "D1"
```

`extracted_from` 必须锚定来源 ADR 版本与可由 Git 解析的 commit hash；ADR 重构前后如宣称语义零变化，必须逐条比对登记的 `id`、`statement`、`decision` 和 `explicitly_not_frozen`。`test_mapping` 与 `missing_reason` 可由获授权的执行 Agent 随测试闭合机械更新；语义字段只由 Architecture Agent 修改。Phase 收尾时，每个 `TEST_MISSING` 必须闭合、附理由显式保留，或在对应 Phase 文档的 `## Backlog` 记录不变式 ID、缺口原因和目标 Phase。
