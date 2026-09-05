# CAEGraph Agent Workflow（全局协作规范）

本文件定义所有 Agent 如何协作。任何 Agent（无论底层是 Claude Code、Cursor、
OpenCode 还是其他实现）接入 CAEGraph 开发时，**必须先读本文件与
`architecture/ARCHITECTURE.md`**，并在整个任务周期内遵守本流程。

---

## 1. 开发主链路

```
Requirement（用户请求）
    ↓
Project Management Agent   分类、拆解、定义验收标准、路由
    ↓
Task Branch                按 Git Skill 创建具名任务分支
    ↓
Architecture Agent         结构/依赖相关时必须先行（改 ARCHITECTURE.md + Design UML）
    ↓
Coding Agent               按已批准设计实现（src/caegraph/）
    ↓
Testing Agent              合成数据、确定性测试
    ↓
Documentation Agent        docstring/API/教程/双语页面
    ↓
Reviewer Agent             七者一致性 + API 兼容性审查
    ↓
Release Agent              仅发布任务执行（版本、构建、发布清单）
```

规则：

- 每个环节只做本角色的事（各 SKILL.md 的"禁止事项"为红线）。
- 下游发现上游缺陷时，**退回上游修复**，不得代劳（如 Reviewer 发现设计缺失
  → 退回 Architecture Agent，而不是默认一个设计继续写）。
- 不需要经过的环节可跳过（如纯文档更新不经过 Coding/Testing），但跳过决定
  由 Project Management Agent 做出并记录。
- Git 是所有 Agent 共享的基础工程能力；任何 Git 操作都必须遵守
  `.agent/skills/git/SKILL.md`，且不得突破当前角色的职责边界。

### 1b. 紧急修复链路

```
崩溃 / 错误结果 / CI 全红
    ↓
Project Management Agent   确认紧急级别与验收标准
    ↓
bugfix/<name>              从 main 创建，禁止直接提交 main
    ↓
Coding → Testing → Reviewer
    ↓
用户批准后 merge / push
```

涉及公共 API、包结构或依赖的紧急修复必须恢复完整的 Architecture / Environment
路由；紧急状态不授权强推、跳过测试或绕过用户批准。

## 2. 职责边界一览

| Agent | 唯一职责 | 绝对不做 |
| --- | --- | --- |
| Project Management | 任务分类与路由 | 直接实现任何东西 |
| Architecture | 规则、Design UML、差异审查 | 写功能代码 |
| Coding | 按设计实现 | 自创抽象、绕过流程引依赖 |
| Testing | 测试策略与质量 | 提交大文件、删断言凑通过 |
| Validation | 科学正确性（不变量/守恒/benchmark） | 以"看起来合理"替代量化断言 |
| Documentation | 文档站与双语页面 | 手写 API 内容 |
| Reviewer | 终审与兼容性 | 放行违规变更 |
| Environment | 环境与依赖声明 | 换环境、动 PyTorch/CUDA |
| Release | 版本与发布 | 跳过清单、擅自对外发布 |

## 3. 全局验收不变量

任何合入必须满足七者一致：

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing ⇔ Environment ⇔ Release 约束
```

- 结构变更：Design UML 先行，Generated UML 随代码由工具再生成（禁止手工编辑）。
- 依赖变更：走 Environment Agent 的工作流（声明文件 + CI 验证）。
- 破坏性 API 变更：版本计划 + CHANGELOG 迁移说明缺一不可。
- 当前 Phase 红线（见 ARCHITECTURE.md）优先于一切任务需求。

## 4. 接入新的 Agent 实现（换框架 checklist）

1. 读 `AGENTS.md`（全局约束）→ 本文件 → 对应 `SKILL.md`。
2. 确认 conda 环境 `caegraph-dev`（Python 3.10）——环境不符立即停止。
3. 读 `architecture/phases/CURRENT.md` 确认当前 Phase 与红线。
4. 按 Project Management Agent 的分类流程处理第一个请求。
5. 输出格式遵循各 SKILL.md 的"输出要求"。
