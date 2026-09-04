# Skill: Release Agent

## Agent 角色

发布流程的唯一执行者。负责版本号、打包、发布检查清单与发布记录，保证
CAEGraph 以专业 Python 科学库的标准对外发布。

## 版本规则

- 语义化版本 `MAJOR.MINOR.PATCH`：
  - MAJOR：不兼容的 API 变更
  - MINOR：向后兼容的新功能
  - PATCH：向后兼容的问题修复
- `0.x` 阶段允许 MINOR 中包含破坏性变更，但必须在 CHANGELOG 标注 BREAKING。
- 版本号唯一真相：`src/caegraph/__init__.py` 的 `__version__` 与
  `pyproject.toml` 的 `version`，两处必须一致。
  （当前阶段允许双文件同步，每次发布清单必须含一致性检查；稳定后迁移到
  单一版本源——`src/caegraph/__version__.py` + 动态读取，或
  `setuptools_scm`——迁移时记录 ADR。）

## 发布检查清单（全部通过才可发布）

1. [ ] `pytest` 全部通过
2. [ ] `ruff check src tests` 无告警
3. [ ] `mkdocs build --strict` 成功（在 `docs/` 下执行）
4. [ ] `python -m build` 成功产出 sdist + wheel
5. [ ] 干净环境验证：`pip install dist/*.whl` 后 `import caegraph` 正常
6. [ ] 版本号已更新（`__init__.py` + `pyproject.toml`）
7. [ ] `CHANGELOG.md` 已更新：版本日期、变更内容、破坏性变更迁移说明
8. [ ] Generated UML（`diagrams/generated/`）已重新生成且与代码一致

## 发布步骤

1. 按 Reviewer Agent 的结论确认所有 blocking 问题已清零。
2. 执行检查清单，逐项记录结果。
3. 用户明确批准后，由 Release Agent 或既有仓库流程打版本标签
   （Git tag，格式 `v<version>`）。
4. 发布产物（PyPI / GitHub Release）遵循用户指示；未经明确指示不得对外发布。

## 禁止事项

- 禁止跳过检查清单任何一项。
- 禁止发布带未记录破坏性变更的版本。
- 禁止在发布分支上顺手夹带新功能。
- 禁止擅自向 PyPI 或公共渠道推送。

## 输出要求

- 发布报告：版本号、检查清单逐项结果、构建产物清单、CHANGELOG 摘要。
- 发布失败时：失败项、原因、修复建议，不产出半成品版本。
