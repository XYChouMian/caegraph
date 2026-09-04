# ADR-003: Python 支持与开发环境策略

- 编号：ADR-003
- 标题：以 Python 3.10 的 `caegraph-dev` 为唯一开发环境，使用 pip 管理包，并由 CI 验证 Python 3.10/3.11
- 日期：2026-09-03
- 更新：2026-09-04（合并已退役的 ADR-005、ADR-006）
- 状态：accepted
- 关联：Phase 0；`.agent/skills/environment/SKILL.md`；ADR-001

## 背景

CAEGraph 依赖 PyTorch 生态，CUDA 与 BLAS 栈对安装方式敏感。团队与 Agent 需要
共享唯一、可复现的开发环境，同时发布包需要明确最低 Python 版本并持续验证兼容
范围。环境规则还必须区分运行时依赖、开发工具和文档工具，避免声明漂移。

项目早期曾先以 Python 3.11 为标准环境，再通过 CI 引入 Python 3.10 兼容性，最终
决定将本地标准环境统一到 Python 3.10。该演化曾记录在 ADR-005、ADR-006；Phase 0
整理后，本 ADR 吸收其最终有效决策，过程仍可从 Git 历史追溯。

## 决策

- 唯一开发环境为 Conda 环境 `caegraph-dev`（Python 3.10），平台为 WSL Linux。
- Conda 只负责环境与 Python 本体；所有 Python 包通过 pip 安装。
- 包最低支持 Python 3.10；Black 与 Ruff 使用 `py310` 作为最低语法目标。
- CI 测试矩阵覆盖 Python 3.10 和 3.11；文档构建使用标准环境版本 3.10。
- 不维护第二个本地 Python 3.11 环境；3.11 兼容性由 CI 验证。
- 三个依赖声明的职责为：
  - `environment.yml`：完整、可复现的标准环境描述，覆盖 runtime/dev/docs。
  - `pyproject.toml`：运行时依赖与 `[dev]`、`[docs]` 可选组，是 PyPI 元数据真相。
  - `requirements-dev.txt`：贡献者完整工具链，等价覆盖 `[dev] + [docs]`；不锁版本。
- 禁止创建其他虚拟环境；PyTorch/CUDA 变更必须获得批准并走依赖变更流程。

## 备选方案

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 纯 Conda 管理所有包 | 否决 | 与 PyPI 发布路径分裂，容易产生 Conda/pip 混装漂移 |
| 纯 venv + pip | 否决 | 不符合团队既有 Conda 工作流，CUDA 栈控制较弱 |
| 本地同时维护 Python 3.10/3.11 | 否决 | 违反唯一环境原则，增加本地漂移风险 |
| `caegraph-dev` 使用 3.11，仅由 CI 测 3.10 | 否决 | 不符合标准开发环境统一到 3.10 的项目决策 |
| `caegraph-dev` 使用 3.10，CI 测 3.10/3.11 | 采纳 | 本地环境单一，同时保留跨版本兼容验证 |

## 影响

- 开工前必须确认 `caegraph-dev`、Python 3.10 和正确解释器路径。
- 新代码不得使用 Python 3.11 独有语法，除非新 ADR 提高最低支持版本。
- 依赖变化必须同步相关声明文件，并运行 `pip install -e .`、pytest 和严格文档构建。
- Python 3.11 的兼容性结论以 CI 为准。
- ADR-005、ADR-006 已合并删除，其编号永久保留，不得复用；下一 ADR 编号为 007。
