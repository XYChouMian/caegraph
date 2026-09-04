#!/usr/bin/env python3
"""Aggregate all .agent/skills/*/SKILL.md into a single ALL_SKILLS.md.

Usage (from anywhere):
    python .agent/skills/aggregate_skills.py

Rules:
- Output is machine-generated: edit SKILL.md files, never the aggregate.
- Skills are ordered alphabetically by directory name (deterministic).
"""

from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SKILLS_DIR.parent / "ALL_SKILLS.md"


def demote_headings(text: str) -> str:
    """Demote every markdown heading by one level (# -> ##, ## -> ###)."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            lines.append("#" + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def main() -> None:
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        raise SystemExit(f"No SKILL.md found under {SKILLS_DIR}")

    parts: list[str] = [
        "# CAEGraph Agent Skills（汇总）",
        "",
        "> 本文件由 `.agent/skills/aggregate_skills.py` 自动生成，请勿手动编辑。",
        "> 修改对应 `SKILL.md` 后重新运行该脚本。",
        "",
        "## 目录",
        "",
    ]
    sections: list[tuple[str, str]] = []
    for skill_file in skill_files:
        name = skill_file.parent.name
        body = demote_headings(skill_file.read_text(encoding="utf-8").strip())
        sections.append((name, body))
        parts.append(f"- {name} (`{skill_file.relative_to(SKILLS_DIR.parent)}`)")

    for name, body in sections:
        parts.extend(["", "---", "", f"## {name}", "", body, ""])

    OUTPUT_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} ({len(sections)} skills)")


if __name__ == "__main__":
    main()
