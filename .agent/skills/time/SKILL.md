---
name: time
description: Confirm the real current calendar date before writing any new date into ADRs, changelogs, phase records, release records, reports, or other tracked artifacts.
---

# Skill: Time

## 角色

Time Skill 为需要写入日期的 Agent 提供唯一的当前日期确认规则，不要求无日期任务额外输出或记录日期。

## 触发条件

只有在新增或修改 ADR 日期、修订历史、CHANGELOG、Phase 记录、Release 记录、任务报告或其他显式日期字段时触发本 Skill；读取历史日期、查看 Git 时间或处理不写入日期的任务不触发。

## 当前日期确认

1. 在实际编辑日期字段前执行 `date '+%Y-%m-%d'`，以执行环境的系统时钟为当前日期来源。
2. 日期统一写为 `YYYY-MM-DD`，精确到天；除非目标格式明确要求，不新增时间、时区或时间戳。
3. 不得使用模型记忆、对话元数据、文件修改时间、Git 提交时间或上一轮工具输出推测当前日期。
4. 任务跨越日期边界、暂停后恢复或距离上次确认时间较长时，在下一次写入前重新执行确认命令。
5. 历史日期只有在 Git、发布记录或其他明确证据支持时才能填写；不得把当前日期倒填为历史日期，也不得仅为“纠正”而改写既有历史。

## 输出约束

- 日期确认是内部门禁，不要求在每个任务报告、交接记录或普通回复中重复展示当前日期。
- 交接或审查只需说明日期字段已按本 Skill 确认；只有用户要求或验收需要时才报告具体日期。
- 若系统时钟不可用、结果冲突或跨时区边界造成日期不确定，暂停日期写入并报告阻塞，不得猜测。

## 交接

输出日期字段范围、确认命令及结果、是否存在历史日期证据、`Decision` 和 `Next`；不涉及日期的任务标记为 `Skipped: Time Skill — no date write`。
