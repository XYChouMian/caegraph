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

如 Architecture Agent 决定创建同目录的可选伴随登记 `ADR-NNN-invariants.yaml`，Markdown ADR 仍是唯一决策真源，YAML 只提供机器可读的核验索引。创建条件、语义变更和重构判断见 [Architecture Agent Skill](../../.agent/skills/architecture/SKILL.md)。

```yaml
adr: "ADR-NNN"
version: "vN"
extracted_from: "vN decision text (baseline commit <git-commit-hash>)"
invariants:
  - id: "ADR-NNN-D1-01"
    statement: "中文、可判定真伪的不变式。"
    decision: "D1"
    test_mapping:
      - "tests/package/test_module.py::test_invariant"
    # 若尚无测试：test_mapping: "TEST_MISSING"
    # Phase 收尾时仍缺失：missing_reason: "中文、可审查的保留理由。"
explicitly_not_frozen:
  - item: "中文描述的刻意未冻结项。"
    source: "D1"
```

- `adr`、`version` 和 `extracted_from` 标识登记来源；`extracted_from` 必须写明 ADR 版本与可由 Git 解析的基线 commit。
- 每个 `invariants` 条目摘录 ADR 已冻结的可判定约束：`id` 是稳定标识，`statement` 使用中文，`decision` 指向 ADR 决策，`test_mapping` 列出守护它的 `path::test_name`。
- 无测试证据时使用 `TEST_MISSING`；若 Phase 收尾时仍保留，必须提供中文 `missing_reason`。该理由、是否保留缺口及是否升格待办属于 Architecture 判断。
- `explicitly_not_frozen` 只记录 ADR 明确保留的自由度，不能被实现或测试当作约束。
- 初始登记及任何语义内容都从 ADR 的架构判断得出，不能从 diff 自动生成。经 PM 明确授权时，执行 Agent 只能依据同一任务中客观可验证的测试 diff，同步既有条目的 `test_mapping`；测试证据以外的内容必须交回 Architecture。
