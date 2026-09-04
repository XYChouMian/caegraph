# ADR-001: 采用 src-layout 包结构

- 编号：ADR-001
- 标题：所有源码位于 `src/caegraph/`，采用 Python 官方推荐的 src-layout
- 日期：2026-09-03
- 状态：accepted
- 关联：Phase 0；`architecture/ARCHITECTURE.md` §4.2

## 背景

CAEGraph 定位为长期维护的 PyPI 科学计算库。flat-layout（包目录在仓库根）
存在测试误 import 本地未安装包的经典陷阱，且根目录容易被脚本污染。

## 决策

采用 src-layout：`src/caegraph/` 为唯一源码位置；仓库根目录禁止出现
Python 文件；`pyproject.toml` 中以 `[tool.setuptools.packages.find]
where = ["src"]` 发现包。

## 备选方案

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| flat-layout（根目录放 `caegraph/`） | 否决 | 测试可能 import 未安装的本地目录，掩盖打包错误 |
| src-layout（采纳） | 采纳 | 强制通过安装后的包进行测试；打包行为与用户一致；社区标准 |

## 影响

- 测试、文档构建、CI 都隐式依赖 `pip install -e .`（或等价的 PYTHONPATH 注入）。
- 贡献指南必须说明先安装再测试。
