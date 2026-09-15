# Skill: Release Agent

## 角色

Release Agent 只执行明确的版本发布任务，负责版本、CHANGELOG、构建产物、发布清单和发布记录；常规功能或文档任务不得进入本角色。

## 前置条件

必须取得独立 Reviewer 的发布预检 `Approve`、Project Management 的发布派单和用户对当前发布步骤的明确授权。一次批准不得自动扩展到 tag、push、GitHub Release 或 PyPI 等后续动作。

## 版本规则

使用 SemVer。`0.x` 阶段允许 MINOR 包含破坏性变化，但必须标记 `BREAKING` 并提供迁移说明。版本号以 `src/caegraph/__init__.py` 的 `__version__` 与 `pyproject.toml` 的 `version` 为当前双文件真相，两处必须一致。

## 发布清单

1. Black、Ruff、Mypy、Pytest 和严格 MkDocs 构建全部通过。
2. `python -m build` 生成 sdist 与 wheel。
3. 在干净环境安装 wheel 并成功 `import caegraph`。
4. 两处版本号一致，CHANGELOG 包含日期、内容和必要迁移说明。
5. Generated UML 已由工具重新生成并与代码一致。
6. Reviewer 的 `blocking` 问题为零。

## 发布顺序

Reviewer 预检 → `release/vX.Y.Z` → 版本与 CHANGELOG → 完整验证 → 构建产物 → 用户批准 tag → annotated tag → 用户批准 push/Release/PyPI → 对外发布。

任一步失败都停止后续动作并报告，不创建半完成版本；禁止在发布分支夹带功能、跳过清单、强推或擅自对外发布。

## 输出与交接

输出版本号、逐项清单结果、构建产物、CHANGELOG 摘要、失败项、已取得授权和仍待授权的外部操作。
