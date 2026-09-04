# Skill: Git Workflow

## Agent 角色

Git 是所有 CAEGraph Agent 共享的基础工程能力，不是独立交付角色。它保存代码
历史、架构演化、协作边界与发布追溯。所有 Agent 使用 Git 时都必须遵守本规则，
同时不得突破各自角色的文件和职责边界。

## 权限模型

### 无需额外批准

- 检查仓库状态与历史：`git status`、`git diff`、`git log`、`git show`、
  `git blame`。
- 在 Project Management Agent 已分类、用户已授权的任务范围内创建任务分支。
- 在任务分支上显式暂存本任务文件并创建本地提交。

每次暂存和提交前必须检查 `git status` 与 `git diff`。只暂存明确属于当前任务的
路径；不得使用宽泛暂存掩盖无关变化，不得覆盖、丢弃或提交用户已有的修改。

### 必须获得用户明确批准

- merge、push、pull、fetch、创建或推送 tag。
- 创建或修改远程 Pull Request、Issue、Release。
- rebase、commit amend、reset、stash、删除分支等可能改写或隐藏工作状态的操作。
- 任何发布到 PyPI、GitHub 或其他外部渠道的操作。

批准只适用于用户确认的具体操作和目标，不自动授权后续同类操作。

### 永远禁止

- 在既有仓库运行 `git init`，或擅自修改 remote 配置。
- 直接提交到 `main`、强制推送、改写 `main` 历史或绕过分支保护。
- 删除或覆盖不属于当前任务的修改。
- 提交秘密、凭据、`.env`、编辑器状态、缓存、构建产物或本地生成物，例如
  `docs/site/`、`site/`、`build/`、`dist/`、`__pycache__/`。
- 手工编辑工具管理的 Generated UML。结构变化时必须由规定工具重新生成，并将
  生成结果随代码提交；项目声明文件 `environment.yml` 不属于禁止提交的本地
  环境文件。

## 各 Agent 的 Git 边界

| Agent | 可在已授权任务分支提交 | 禁止 |
| --- | --- | --- |
| Project Management | 任务元数据、Phase 指针、工作流派单记录 | 源码、merge、release |
| Architecture | `architecture/`、ADR、Design UML、架构治理文件 | 功能实现、直接合入 `main` |
| Coding | 已批准设计对应的 `src/` 与配套测试 | 未批准的架构或依赖变更 |
| Testing | `tests/` 与测试配置 | 为通过测试而削弱断言、擅改生产实现 |
| Validation | 科学验证测试与验证记录 | 用主观判断代替量化验证、擅改实现 |
| Documentation | `docs/`、README、经协调后的 docstring | 改变实现行为、宣称不存在的功能 |
| Environment | 依赖与环境声明、相关 CI 配置 | 换环境、未经批准调整 PyTorch/CUDA |
| Reviewer | 只读检查 diff、历史与提交 | 审查时静默修改或提交代码 |
| Release | 经批准的版本、CHANGELOG、发布分支、tag 与产物准备 | 未经批准发布或跳过检查 |

## 分支策略

`main` 始终表示稳定状态，禁止直接提交。Project Management Agent 按任务类型从
当前本地 `main` 创建一个短生命周期分支；如需先 fetch/pull 同步远程，必须获得
用户明确批准：

- `feature/<name>`：功能开发。
- `bugfix/<name>`：缺陷和紧急修复。
- `docs/<name>`：纯文档变更。
- `arch/<name>`：架构、ADR、UML 或 Agent 治理变更。
- `chore/<name>`：环境、依赖、CI 与其他工程维护。
- `release/v<MAJOR>.<MINOR>.<PATCH>`：发布准备。

名称使用小写英文与连字符。一个任务分支只承载同一派单范围内的变化。

### Worktree 协议（多 Agent 并发强制）

多个 Agent 共享同一仓库时，必须用 `git worktree` 隔离各自工作区，防止并发
修改互相覆盖：

- **主工作区**（仓库本体）只停留在 `main`，仅执行 merge、push 等集成操作，
  **禁止在主工作区直接开发或提交任务变更**。
- 每个 Agent 拥有一个专属持久 worktree，位于主仓库同级目录，并常驻一个
  `<agent>/workspace` 占位分支：
  - opencode Agent：`../caegraph-opencode`（分支 `opencode/workspace`）
  - codex Agent：`../caegraph-codex`（分支 `codex/workspace`）
- 新增 Agent 时按同样约定扩展（`../caegraph-<agent>` +
  `<agent>/workspace`）；临时性 worktree 放 `/tmp` 并在任务结束后删除。
- 任务流程：在**本 Agent 的 worktree 内**从 `main` 创建任务分支
  （`git checkout -b <type>/<name> main`）→ 开发、验证、提交 → 经用户批准后
  在主工作区合入 `main` → worktree 收回占位分支并删除任务分支。
- 并发纪律：禁止触碰其他 Agent 的 worktree、占位分支及其未提交修改；任何
  Git 写操作前必须用 `git worktree list` + `git branch --show-current` 确认
  所在位置。

## 提交规范

提交格式为 `type(scope): description`，description 使用简短的英文祈使语气：

- `feat(core): add mesh abstraction`
- `fix(data): preserve node indices`
- `docs(api): document graph conversion`
- `test(core): cover object validation`
- `arch(core): define mesh relationships`
- `chore(env): add type checker`
- `ci(test): enforce formatting checks`
- `release: prepare v0.2.0`

每个提交只表达一个可审查的逻辑变化。禁止使用 `update`、`fix`、`modify`、
`changes` 等无法说明意图的孤立提交信息。提交前运行与变更相关的检查；合入前
必须完成全量验收。

## Pull Request 与合入

Pull Request 描述必须包括：变更目的、架构/UML 影响、测试结果、文档影响、API
兼容性与迁移要求。Reviewer Agent 检查完整 diff 和提交历史，并按 blocking /
non-blocking 输出结论。

合入 `main` 前必须满足：

- `black --check src tests`
- `ruff check src tests`
- `mypy src`
- `pytest`
- 在 `docs/` 下运行 `mkdocs build --strict`
- Reviewer Agent 结论为 `Approve`，且 CI 通过

Agent 只有在用户明确批准后才能创建远程 PR 或执行 merge/push。

## 发布流程

发布顺序为：Reviewer 预检 → `release/vX.Y.Z` → 更新版本与 CHANGELOG → 完整
验证 → 构建 sdist/wheel → 用户批准 → 创建 annotated tag `vX.Y.Z` → 推送 tag →
GitHub Release / PyPI 发布。Release Agent 不得将功能开发夹带进发布分支，也不得
将一次批准扩展到后续发布步骤。

## 紧急流程

紧急修复仍从 `main` 创建 `bugfix/<name>`，经过 Coding → Testing → Reviewer，
不得直接提交或强推 `main`。涉及公共 API、包结构或依赖时必须恢复完整的
Architecture / Environment 路由。发现凭据泄漏时立即停止提交和推送、报告影响，
由用户决定轮换凭据与历史清理；Agent 不得自行重写历史。

## Git 作为项目记忆

重大变更前检查相关 `git log`、`git blame` 与 `git diff`，结合 ADR 理解设计原因。
Git 历史记录已发生的演化，ADR 记录决策理由，二者不能相互替代。

## 输出要求

任何 Git 写操作都要报告：当前分支、执行的操作、涉及文件、验证结果，以及是否
存在尚需用户批准的 merge、push、tag 或发布步骤。
