# ADR-003: 环境策略（conda 建环境 + pip 装包 + 三声明文件分工）

- 编号：ADR-003
- 标题：caegraph-dev conda 环境为唯一开发环境；conda 只建环境，包一律 pip 安装；environment.yml / pyproject.toml / requirements-dev.txt 三文件分工
- 日期：2026-09-03
- 状态：accepted
- 关联：Phase 0；`.agent/skills/environment/SKILL.md`；ADR-001

## 背景

CAEGraph 依赖 PyTorch 生态（torch / torch-geometric），CUDA 与 BLAS 栈对
安装方式敏感。团队与 Agent 混合开发，需要防环境漂移；同时包要发布 PyPI。

## 决策

- 唯一开发环境：conda 环境 `caegraph-dev`（Python 3.11），WSL 平台。
- conda 仅负责创建环境与 Python 本体；所有 Python 包经 `pip` 安装。
- 声明文件分工：
  - `environment.yml`：环境创建与完整复现描述
  - `pyproject.toml`：运行时依赖 + 可选 extras（PyPI 唯一真相）
  - `requirements-dev.txt`：开发工具清单（不锁版本），供 CI/贡献者，
    必须与 `[dev]` extras 同步
- 禁止创建其他虚拟环境；PyTorch 升降级需批准。

## 备选方案

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 纯 conda 管理所有包 | 否决 | conda 与 PyPI 生态混装易冲突；PyPI 发布路径不标准 |
| 纯 venv + pip | 否决 | 团队既有 conda 工作流；CUDA 栈在 conda 下更可控 |
| conda 建环境 + pip 装包（采纳） | 采纳 | 兼顾 CUDA 可控性与 PyPI 生态一致性 |

## 影响

- 依赖变更必须同时回写相关声明文件（Environment Agent 工作流）。
- 环境验证命令写死在 AGENTS.md / Environment SKILL，Agent 开工前必须执行。
