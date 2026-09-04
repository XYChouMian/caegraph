# ADR-006: 标准开发环境降为 Python 3.10

- 编号：ADR-006
- 标题：标准开发环境 `caegraph-dev` 从 Python 3.11 降为 Python 3.10
- 日期：2026-09-04
- 状态：accepted
- 关联：Phase 0；取代 ADR-005；关联 ADR-003；`environment.yml`；`.github/workflows/test.yml`

## 背景（Context）

ADR-005 曾决策"开发环境保持 3.11、仅由 CI 验证 3.10 兼容性"，并明确否决了
"将唯一开发环境降为 3.10"。此后用户明确提出以 Python 3.10 作为标准开发环境
的需求，环境版本成为已裁决事项，ADR-005 的环境条款不再符合当前意图。

约束：唯一 Conda 环境 `caegraph-dev`（ADR-003）不得并存第二个本地环境；
禁止就地跨 minor 版本改动解释器（易留下混合安装状态）。

## 决策（Decision）

- 标准开发环境 `caegraph-dev` 重建为 **Python 3.10**，仍由根目录
  `environment.yml` 唯一描述，环境名不变。
- 包的最低支持版本保持 Python 3.10（继承 ADR-005）；Black/Ruff 的
  `py310` 目标不变。
- CI 测试矩阵继续同时运行 **3.10 与 3.11**，Python 3.11 兼容性声明保留，
  由 CI 而非本地环境保证。
- MkDocs 文档构建任务改用 3.10，与标准开发环境一致。
- 本地不再维护 Python 3.11 环境；3.11 回归只能由 CI 捕获。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 就地 `conda install python=3.10` 降级 | 否决 | 跨 minor 就地降级易留下损坏的混合安装状态 |
| 保持 ADR-005 现状（开发环境 3.11） | 否决 | 与用户裁决的标准环境版本直接冲突 |
| 重建 `caegraph-dev` 为 3.10，CI 继续测 3.10/3.11 | 采纳 | 环境与需求一致，且不丢失 3.11 兼容性验证 |

## 影响（Consequences）

- 所有环境约束文件（`AGENTS.md`、Environment SKILL、`WORKFLOW.md`、
  `README.md`、`ARCHITECTURE.md`、Phase 0 文档）必须同步更新为 3.10。
- 重建后必须完整执行 `pip install -e .` → `pytest` →
  `mkdocs build --strict` 验证，全部通过才算完成。
- 新代码不得使用 Python 3.11 独有语法（继承 ADR-005 约束，继续生效）。
- 若未来需要恢复 3.11 标准环境，须以新 ADR 取代本决策。
