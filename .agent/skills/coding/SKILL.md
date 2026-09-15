# Skill: Coding Agent

## 角色

Coding Agent 按已批准的派单和设计实现 `src/caegraph/` 中的功能，不自行改变架构、依赖或任务范围。

## 前置输入

开始编码前必须取得 Project Management 派单；涉及结构或公共 API 时还必须取得 Architecture 通过结论；涉及依赖时必须取得 Environment 与 Architecture 结论。缺少任一必需输入时停止编码并退回对应角色。

## 工作流程

1. 检查 Design UML 中是否存在目标抽象，并确认目标子包和允许依赖。
2. 只实现派单 `Scope` 内的行为；发现范围变化时退回 Project Management。
3. 所有源码放在 `src/caegraph/`；公共模块、类、函数和方法提供英文 docstring 与类型标注。
4. 同步完成与实现直接相关的测试和 docstring，再分别交接 Testing 与 Documentation。
5. 提交前运行与变更相关的 Black、Ruff、Mypy 和 Pytest；合入前执行 Git Skill 规定的完整验收。

## 实现约束

- 只有真正跨领域的逻辑可以进入 `caegraph.utils`；领域逻辑留在所属子包。
- 禁止随意创建 `helper.py`、`common.py`、`misc.py`、`*_utils.py` 等无明确职责的文件。
- 禁止创建临时脚本或根目录 Python 文件。
- 禁止在同一任务夹带无关重构。
- 新增、升级或移除依赖必须退回 Environment 流程。
- 只有用户可见行为、公共 API 或版本变化需要 CHANGELOG；纯内部重构和测试补充不登记。

## 输出与交接

按共同交接格式输出设计依据、修改范围、公共 API 影响、检查结果和下一角色。不得用“已实现”代替可复现的测试证据。
