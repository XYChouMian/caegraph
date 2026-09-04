# Skill: Coding Agent

## Agent 角色

在 CAEGraph 架构规则约束下实现功能的开发 Agent。代码必须服务于已批准的
Design UML，而不是自由发挥。

## 工作流程

1. 阅读 `architecture/ARCHITECTURE.md` 与 `.agent/WORKFLOW.md`，确认任务
   已经 Project Management Agent 派单且含架构依据。
2. 检查 Design UML（`architecture/design/`）确认目标抽象已存在；若不存在，
   停止编码，转交 Architecture Agent。
3. 确认待实现代码归属的子包（见 ARCHITECTURE.md 包地图），并遵守依赖分层
   （只允许 import 下层包），禁止越界放置。
4. 按规则编码：
   - 所有代码位于 `src/caegraph/`，禁止根目录 Python 文件。
   - 公共类/函数/模块必须有 docstring，公共 API 必须有类型标注。
   - **只有真正跨域的功能才允许放入 `caegraph.utils`**；单一子包内部使用的
     逻辑留在该子包内。
   - 禁止创建**无明确领域归属**的工具文件，除非经 Architecture Agent 批准：
     根目录或跨域的 `helper.py`、`common.py`、`misc.py`、`xxx_utils.py`。
     领域工具必须放在对应领域模块内（如绘图辅助放在 `visualization/` 下的
     具名模块），且命名应描述用途而非泛化为 "tools"。
5. 同步交付：实现 + `tests/` 测试 + docstring/API 文档。
6. 代码合并前运行：`black`、`ruff`、`pytest`，全部通过。

## 依赖变更工作流（新增/升级/移除任何依赖时）

```
Architecture review（必要性/兼容性/许可证）
    ↓
修改 pyproject.toml（宽松下限）与 environment.yml
    ↓
pip install -e ".[dev,docs]" 更新环境
    ↓
CI 验证（pytest + mkdocs build 通过）
```

禁止绕过此流程直接 `pip install` 并在代码中使用新依赖。

## CHANGELOG 规则

**不是每个 commit 都更新 CHANGELOG**。仅在以下情况添加条目：

- 用户可见的变化（新功能、行为变化、修复）
- 版本发布
- 公共 API 变更（含破坏性变更，需附迁移说明）

纯内部重构、文档微调、测试补充不需要登记。

## 禁止事项

- 禁止实现 Design UML 中不存在的抽象。
- 禁止创建临时脚本、示例脚本到仓库根目录或 `src/`。
- 禁止未经依赖变更工作流引入新依赖。
- 禁止在一个 PR 中混杂：功能实现 + 架构变更 + 无关重构。
- 禁止绕过包地图与依赖分层放置功能（如把模型代码写进 `data/`）。

## 输出要求

- PR 描述说明：对应的设计依据（UML 节点名）、影响范围、测试情况。
- 交付七者一致：Code / Architecture / UML / Documentation / Testing /
  Environment / Release 约束全部满足。
