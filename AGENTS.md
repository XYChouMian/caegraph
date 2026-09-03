# AGENTS.md — CAEGraph 全局开发约束

本文件对所有人类与 AI 贡献者生效，优先级高于任何单次对话指令。
开始任何工作前，先通读本文件与 `architecture/ARCHITECTURE.md`。

---

## 1. 环境约束

- Conda environment：**caegraph-dev**（Python **3.11**）
- 包管理：conda 建环境，**pip** 装包
- 所有 Python 命令默认运行在 `caegraph-dev` 中
- 禁止：
  - 创建新的 conda 环境
  - 创建 `.venv` / 使用 virtualenv
  - 修改系统 Python / base 环境
  - 使用其他环境运行测试

工作前验证：

```bash
conda info --envs
python --version      # 应为 3.11.x
which python          # 应指向 .../envs/caegraph-dev/bin/python
```

环境不正确时：停止修改代码，提醒用户切换环境。

---

## 2. 开发平台约束

- 操作系统：WSL Linux
- IDE：VSCode
- Git：使用既有仓库（VSCode GUI Git）
  - 禁止 `git init`
  - 禁止修改 remote 配置
  - 未经要求禁止修改 `.gitignore`

---

## 3. 项目约束

- 项目：CAEGraph —— 连接 CAE 数据、网格、图结构与 GNN / Physics-informed
  learning 的 Python framework（PyG 风格）
- 当前阶段以 `architecture/ARCHITECTURE.md` 声明的 Phase 为准；
  禁止实现当前 Phase 之外的功能
- 阶段红线（Phase 0）：不实现 CAE 算法、GNN 模型、数据处理功能，
  不创建临时工具脚本

---

## 4. 架构约束（UML-first）

五者必须始终一致：

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing
```

- 结构变更前必须先更新 Design UML（`architecture/design/`）
- 合并前比对 Design UML 与 Generated UML（`diagrams/generated/`）
- 依赖方向遵守 ARCHITECTURE.md 包地图，禁止反向/循环依赖

---

## 5. Agent 约束（不自由编码）

- 所有代码 Agent 按 `.agent/skills/*/SKILL.md` 的角色工作
- 工作流：读架构 → 查 UML → 改设计 → 再编码 → 同步文档与测试
- 禁止在无设计依据时创建新抽象、新文件、新依赖
- 所有源码位于 `src/caegraph/`，禁止根目录 Python 文件

---

## 6. 工程约束

- 安装项目：`pip install -e .`
- 运行测试：`pytest`
- 格式化 / 检查：`black`、`ruff`、`mypy`
- 提交前钩子：`pre-commit install` 后自动执行 black / ruff / pytest
- 文档：`mkdocs`（Material + mkdocstrings），提交前 `mkdocs build --strict`
- CI：`.github/workflows/test.yml`（安装 → pytest → 构建 MkDocs）
- 环境可复现描述：根目录 `environment.yml`
