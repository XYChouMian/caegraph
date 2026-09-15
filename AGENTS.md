# AGENTS.md — CAEGraph 全局开发约束

本文件对所有人类与 AI 贡献者生效，优先级高于任何单次对话指令。开始任何工作前，先通读本文件与 `architecture/ARCHITECTURE.md`。

---

## 1. 环境约束

- Conda environment：**caegraph-dev**（Python **3.10**）
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
python --version      # 应为 3.10.x
which python          # 应指向 .../envs/caegraph-dev/bin/python
```

环境不正确时：停止修改代码，提醒用户切换环境。

---

## 2. 开发平台约束

- 操作系统：WSL Linux
- IDE：VSCode
- Git：用户可使用 VSCode GUI；Agent 可在既有仓库中按 `.agent/skills/git/SKILL.md` 使用 Git CLI
  - 禁止 `git init`
  - 禁止修改 remote 配置
  - 未经要求禁止修改 `.gitignore`

---

## 3. 项目约束

- 项目：CAEGraph —— 连接 CAE 仿真与 Physics AI 的工作流框架（CAE 数据 → 图表示 → GNN 训练 → 新网格神经仿真 → 实验数据同化）
- 定位冻结（ADR-008）：未经新 ADR 不得引入 solver 抽象、trainer 抽象、替代图后端层
- 当前阶段以 `architecture/phases/CURRENT.md` 指针为准（绑定表格：`architecture/ARCHITECTURE.md` §6；战略总览：根目录 `ROADMAP.md`）；禁止实现当前 Phase 之外的功能
- 阶段红线（Phase 0）：不实现 CAE 算法、GNN 模型、数据处理功能，不创建临时工具脚本

---

## 4. 架构约束（UML-first）

七者必须始终一致：

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing ⇔ Environment ⇔ Release
```

- 产品代码的结构变更前必须先更新 Design UML（`architecture/design/`）并记录 ADR（`architecture/decisions/`）；仅修改 Agent 治理结构且不影响产品架构时，不得连带修改产品 UML 或 ADR
- 合并前比对 Design UML 与 Generated UML（`diagrams/generated/`，仅工具生成，禁止手改）
- Markdown 中需要表达架构、依赖、流程或状态转换的图，必须使用 Mermaid，不得以 ASCII / 纯文本箭头图替代；仅在图能比段落、列表或表格明显提升理解时使用，禁止为装饰而大量添加。所有 Mermaid 流程图必须定义并应用 `classDef nowrap white-space:nowrap`——`<br>` 是唯一受控换行手段，禁止依赖自动换行。排版以渲染效果为准：TB（纵向）排版的小图标签保持单行、禁止换行；LR（横向）排版下应控制每个块的横向宽度——标签按内容适度 `<br>` 换行，横向块数多时（长链）尽量多次换行，保证在 md 中渲染后整图不过宽、字号可读。图由 agent 创建，人类依据实际渲染效果修改。
- 依赖分层：utils ← core ← {geometry, io} ← graph ← transforms ← dataset ← physics ← {models, assimilation} ← {workflow, inference} ← visualization，下层禁止依赖上层，同层禁止互依（兄弟层互不依赖）；PyG 自 graph 层起可用，core/geometry/io 永不 import PyG（ADR-007）；physics 可由 models、assimilation、workflow 消费，但不得反向依赖它们

---

## 5. Agent 约束（不自由编码）

- 全局协作流程见 `.agent/WORKFLOW.md`：任何请求先经 Project Management Agent 分类，再按任务影响范围进入 Architecture、Environment、Coding、Testing、Validation、Documentation 等必要角色，最后由独立 Reviewer 审查；禁止把所有任务机械套入同一条线性链路
- 各 Agent 角色规则见 `.agent/skills/*/SKILL.md`
- Git 是所有 Agent 共享的基础工程能力，所有 Git 操作必须遵守 `.agent/skills/git/SKILL.md`
- 同一 Agent 实现可以在一次任务中依次承担多个执行角色，但必须显式交接并遵守每个角色的职责边界；任务作者可以自检，不得对自己的变更给出最终 `Approve`
- 工作流：完成开工门禁与 PM 派单后，按 `.agent/WORKFLOW.md` 的 `Route` 依次执行必要角色；只有产品结构受影响时才走 Design UML / ADR 先行链路
- 禁止在无设计依据时创建新抽象、新文件、新依赖
- 所有源码位于 `src/caegraph/`，禁止根目录 Python 文件
- 依赖分层：utils ← core ← {geometry, io} ← graph ← transforms ← dataset ← physics ← {models, assimilation} ← {workflow, inference} ← visualization，下层禁止依赖上层，同层禁止互依；PyG 自 graph 层起可用，core/geometry/io 永不 import PyG（ADR-007）

---

## 6. 工程约束

- 安装项目：`pip install -e .`
- 运行测试：`pytest`
- 开发工具：`pip install -r requirements-dev.txt`（覆盖 pyproject `[dev] + [docs]` extras）
- 格式化 / 检查：`black`、`ruff`、`mypy`
- 提交前钩子：`pre-commit install` 后自动执行 black / ruff / pytest
- 文档：`mkdocs`（Material + mkdocstrings），提交前 `mkdocs build --strict`
- **Agent 规范语言**：`AGENTS.md`、`.agent/WORKFLOW.md` 与 `.agent/skills/*/SKILL.md` 以中文为主要说明语言；命令、路径、代码符号、API 名称、Git 提交格式及 `Approve` / `Request Changes` / `Reject`、`blocking` / `non-blocking` 等机器可识别状态保持英文
- **文本换行约定**：Markdown 是自适应文本（自动换行），段落、列表项、引用块**禁止人工强制换行**——一个逻辑单元（一个段落/一条列表项/一条引用）必须写成一行；仅在代码类文件（`.py`、`.puml` 等）或 Markdown 代码块内部结构行中才允许按宽度折行。mermaid 流程图另遵守 §4 图示规范。
- CI：`.github/workflows/test.yml`（安装 → pytest → 构建 MkDocs）
- 环境可复现描述：根目录 `environment.yml`
