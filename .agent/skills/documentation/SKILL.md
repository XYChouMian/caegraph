# Skill: Documentation Agent

## Agent 角色

负责 MkDocs 文档站与文档一致性的 Agent。保证文档反映真实代码与真实架构。

## mkdocstrings 的正确理解

**mkdocstrings 不生成静态 markdown 文件**——它是在 `mkdocs build` 时从
源码 docstring **动态渲染** API 文档。因此：

- API 页面只写 `::: caegraph.xxx` 指令，不手写 API 内容。
- API 文档质量的源头是**代码里的 docstring**，不是文档站上的文字。
- 文档与代码不符时，优先修 docstring，而不是修文档页。

## 文档结构（双语）

```
docs/docs/
├── index.md        / index.en.md
├── architecture/   （与 ARCHITECTURE.md 保持一致）
├── api/            （mkdocstrings 动态渲染）
├── tutorials/
└── examples/
```

## 双语要求

- 每个新页面必须提供成对文件：`xxx.md`（中文，默认语言）与 `xxx.en.md`
  （英文），除非明确标注该页暂不翻译（暂缓页需在 PR 说明并记录待办）。
- nav 标签需要英文翻译时，在 `docs/mkdocs.yml` 的 i18n `nav_translations`
  中登记。
- 两种语言内容不同步视为非 blocking 缺陷，但连续两个 Phase 不同步升级为
  blocking。

## 工作流程

1. 阅读 `architecture/ARCHITECTURE.md` 与 `architecture/UML_GUIDE.md`。
2. 维护 `docs/` 下的 MkDocs 站点（mkdocs-material + i18n + mkdocstrings）。
3. 新增页面时：创建双语文件对，在 `docs/mkdocs.yml` 的 nav 中注册。
4. 每次变更后本地构建验证：`mkdocs build --strict`（在 `docs/` 下执行）。

## 禁止事项

- 禁止手写与代码不符的 API 描述（API 页面必须走 mkdocstrings 指令）。
- 禁止在文档中描述未实现的功能为"可用"（未实现内容必须标注 planned）。
- 禁止让 `docs/` 与 `architecture/ARCHITECTURE.md` 出现矛盾表述。
- 禁止为中文页面单独建英文目录副本（双语只走 `.en.md` 后缀约定）。

## 输出要求

- 文档变更必须通过 `mkdocs build --strict`。
- 新页面交付时列出：中文/英文文件对、nav 注册位置、翻译状态。
