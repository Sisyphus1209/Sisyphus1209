#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Doctor - Agent Skill 健康扫描器
借鉴 Routa Harness 思想，对 skill 目录执行声明式规则扫描。
"""

import os
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CheckResult:
    rule_id: str
    label: str
    passed: bool
    optional: bool
    message: str = ""
    details: List[str] = field(default_factory=list)


@dataclass
class SurfaceResult:
    surface_id: str
    label: str
    summary: str
    checks: List[CheckResult]


class SkillDoctor:
    def __init__(self, skill_path: Path, rules_path: Path):
        self.skill_path = skill_path.resolve()
        self.rules = self._load_rules(rules_path)
        self.skill_md = self.skill_path / "SKILL.md"
        self.skill_md_content = ""
        self.skill_md_lines: List[str] = []
        if self.skill_md.exists():
            self.skill_md_content = self.skill_md.read_text(encoding="utf-8")
            self.skill_md_lines = self.skill_md_content.splitlines()

    def _load_rules(self, path: Path) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def scan(self) -> List[SurfaceResult]:
        surfaces = self.rules.get("surfaces", [])
        results: List[SurfaceResult] = []
        for surface in surfaces:
            checks = []
            for rule in surface.get("overview", []):
                checks.append(self._evaluate_rule(rule))
            results.append(
                SurfaceResult(
                    surface_id=surface["id"],
                    label=surface["label"],
                    summary=surface.get("summary", ""),
                    checks=checks,
                )
            )
        return results

    def _evaluate_rule(self, rule: Dict) -> CheckResult:
        rid = rule["id"]
        label = rule["label"]
        optional = rule.get("optional", False)
        source = rule.get("source", "")

        if source == "file_exists":
            target = self.skill_path / rule["path"]
            passed = target.exists()
            return CheckResult(
                rid, label, passed, optional,
                f"{'存在' if passed else '缺失'}: {target.relative_to(self.skill_path)}"
            )

        if source == "dir_exists":
            target = self.skill_path / rule["path"]
            passed = target.is_dir()
            return CheckResult(
                rid, label, passed, optional,
                f"{'存在' if passed else '缺失'}: {target.relative_to(self.skill_path)}"
            )

        if source == "file_count":
            target = self.skill_path / rule["path"]
            min_count = rule.get("min", 0)
            if not target.exists():
                return CheckResult(
                    rid, label, False, optional,
                    f"目录不存在: {target.relative_to(self.skill_path)}"
                )
            files = list(target.rglob("*"))
            count = len([f for f in files if f.is_file()])
            passed = count >= min_count
            return CheckResult(
                rid, label, passed, optional,
                f"实际文件数 {count}，要求 ≥{min_count}"
            )

        if source == "regex_match":
            if not self.skill_md.exists():
                return CheckResult(rid, label, False, optional, "SKILL.md 不存在")
            patterns = rule.get("patterns", [])
            match_all = rule.get("match_all", False)
            match_any = rule.get("match_any", False)
            found = [bool(re.search(p, self.skill_md_content, re.MULTILINE)) for p in patterns]
            if match_all:
                passed = all(found)
            elif match_any:
                passed = any(found)
            else:
                passed = all(found)
            return CheckResult(
                rid, label, passed, optional,
                f"匹配 {sum(found)}/{len(patterns)} 个正则"
            )

        if source == "section_exists":
            if not self.skill_md.exists():
                return CheckResult(rid, label, False, optional, "SKILL.md 不存在")
            pattern = rule.get("heading_pattern", "")
            passed = bool(re.search(pattern, self.skill_md_content, re.MULTILINE))
            return CheckResult(
                rid, label, passed, optional,
                f"{'找到' if passed else '未找到'}章节: {pattern}"
            )

        if source == "section_count":
            if not self.skill_md.exists():
                return CheckResult(rid, label, False, optional, "SKILL.md 不存在")
            pattern = rule.get("section_pattern", "")
            matches = list(re.finditer(pattern, self.skill_md_content, re.MULTILINE))
            count = len(matches)
            min_c = rule.get("min", 0)
            max_c = rule.get("max", 999)
            passed = min_c <= count <= max_c
            return CheckResult(
                rid, label, passed, optional,
                f"实际 {count} 个，要求 [{min_c}, {max_c}]"
            )

        if source == "link_resolve":
            if not self.skill_md.exists():
                return CheckResult(rid, label, False, optional, "SKILL.md 不存在")
            broken = self._check_internal_links()
            passed = len(broken) == 0
            return CheckResult(
                rid, label, passed, optional,
                f"发现 {len(broken)} 个失效内部链接",
                details=broken[:5]
            )

        return CheckResult(rid, label, False, optional, f"未知 source 类型: {source}")

    def _check_internal_links(self) -> List[str]:
        # 移除代码块后再检查链接，避免示例代码误报
        broken = []
        # 简单移除 ```...``` 和 `...` 包裹的内容
        content_no_code = re.sub(r"```[\s\S]*?```", "", self.skill_md_content)
        content_no_code = re.sub(r"`[^`]*`", "", content_no_code)
        obsidian_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content_no_code)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content_no_code)
        for link in obsidian_links:
            link_path = self.skill_path / (link.strip() + ".md")
            if not link_path.exists():
                broken.append(f"[[{link}]]")
        for text, link in md_links:
            if link.startswith("http") or link.startswith("#"):
                continue
            link_path = self.skill_path / link
            if not link_path.exists():
                broken.append(f"[{text}]({link})")
        return broken

    def generate_report(self, results: List[SurfaceResult]) -> str:
        score, total = 0, 0
        details_lines = []
        for surface in results:
            details_lines.append(f"\n### {surface.label}")
            details_lines.append(f"*{surface.summary}*")
            details_lines.append("")
            for c in surface.checks:
                total += 1
                if c.passed:
                    score += 1
                icon = "✅" if c.passed else ("⚠️" if c.optional else "❌")
                details_lines.append(f"- {icon} **{c.label}** ({c.rule_id}): {c.message}")
                if c.details:
                    for d in c.details:
                        details_lines.append(f"  - {d}")
            details_lines.append("")

        score_pct = int((score / total * 100)) if total else 0
        score_section = f"""
**综合得分**: {score}/{total} ({score_pct}%)

| 状态 | 含义 |
|------|------|
| ✅ | 通过 |
| ❌ | 必填项未通过（需要修复） |
| ⚠️ | 可选项未通过（建议完善） |
"""

        # 建议行动
        action_items = []
        for surface in results:
            for c in surface.checks:
                if not c.passed and not c.optional:
                    action_items.append(f"- 修复 **{c.label}** ({c.rule_id}): {c.message}")
                elif not c.passed and c.optional:
                    action_items.append(f"- 完善 **{c.label}** ({c.rule_id}): {c.message}")
        action_section = "\n".join(action_items) if action_items else "- 当前状态良好，继续保持。"
        if action_items:
            action_section += "\n\n- → 如需 redesign 指导，参考 `software-design-philosophy` skill。"

        # Mermaid 图
        mermaid_graph = self._generate_mermaid(results)

        template = self.rules.get("outputs", {}).get("report_template", "")
        return template.format(
            generated_at=datetime.now().isoformat(),
            skill_name=self.skill_path.name,
            skill_path=str(self.skill_path),
            score_section=score_section.strip(),
            details_section="\n".join(details_lines).strip(),
            mermaid_graph=mermaid_graph,
            action_section=action_section,
        )

    def _generate_mermaid(self, results: List[SurfaceResult]) -> str:
        lines = ["graph TD"]
        lines.append("    A[Skill Directory] --> B{Harness Scan}")
        prev = "B"
        for surface in results:
            node_id = f"S_{surface.surface_id}"
            failed = [c for c in surface.checks if not c.passed and not c.optional]
            opt_failed = [c for c in surface.checks if not c.passed and c.optional]
            if failed:
                style = f"[{surface.label}<br/>❌ {len(failed)} 项失败]"
                lines.append(f"    {node_id}{style}:::fail")
            elif opt_failed:
                style = f"[{surface.label}<br/>⚠️ {len(opt_failed)} 项建议]"
                lines.append(f"    {node_id}{style}:::warn")
            else:
                style = f"[{surface.label}<br/>✅ 通过]"
                lines.append(f"    {node_id}{style}:::pass")
            lines.append(f"    {prev} --> {node_id}")
            prev = node_id
        lines.append("    classDef pass fill:#d1fae5,stroke:#10b981,stroke-width:2px")
        lines.append("    classDef warn fill:#fef3c7,stroke:#f59e0b,stroke-width:2px")
        lines.append("    classDef fail fill:#fee2e2,stroke:#ef4444,stroke-width:2px")
        return "\n    ".join(lines)


def _run_single(skill_path: Path, rules_path: Path) -> tuple:
    doctor = SkillDoctor(skill_path, rules_path)
    results = doctor.scan()
    report = doctor.generate_report(results)
    out_path = skill_path / "skill-doctor-report.md"
    out_path.write_text(report, encoding="utf-8")

    failed = sum(1 for s in results for c in s.checks if not c.passed and not c.optional)
    optional = sum(1 for s in results for c in s.checks if not c.passed and c.optional)
    total = sum(len(s.checks) for s in results)
    passed = sum(1 for s in results for c in s.checks if c.passed)
    return passed, total, failed, optional, out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python doctor.py <path-to-skill-directory>")
        print("       python doctor.py --all")
        sys.exit(1)

    rules_path = Path(__file__).parent / "rules.yaml"
    arg = sys.argv[1]

    if arg in ("--all", "-a"):
        skills_dir = Path(__file__).parent.parent
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
        if not skill_dirs:
            print(f"No skill directories found under {skills_dir}")
            sys.exit(1)

        rows = []
        for skill_path in sorted(skill_dirs, key=lambda p: p.name):
            passed, total, failed, optional, out_path = _run_single(skill_path, rules_path)
            score = int(passed / total * 100) if total else 0
            status = "FAIL" if failed else "OK"
            rows.append((skill_path.name, passed, total, score, status, failed, optional))
            print(f"[{status}] {skill_path.name:30s} {passed}/{total} ({score}%) | required_fail={failed} optional={optional}")

        # Write overview report
        overview_path = skills_dir / "skill-doctor-overview.md"
        lines = [
            "# Skill Doctor 批量扫描总览",
            "",
            f"> 扫描时间: {datetime.now().isoformat()}",
            f"> 扫描目录: {skills_dir}",
            "",
            "| Skill | 得分 | 状态 | 必填失败 | 可选建议 |",
            "|-------|------|------|----------|----------|",
        ]
        for name, passed, total, score, status, failed, optional in rows:
            icon = "✅" if status == "OK" else "❌"
            lines.append(f"| {name} | {passed}/{total} ({score}%) | {icon} {status} | {failed} | {optional} |")
        lines += [
            "",
            "## 说明",
            "",
            "- **得分** = 通过检查数 / 总检查数",
            "- **必填失败** = 非可选规则未通过的数量（需要修复）",
            "- **可选建议** = 可选规则未通过的数量（建议完善）",
            "",
            "每个 skill 的详细报告位于其目录下的 `skill-doctor-report.md`。",
        ]
        overview_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nOverview saved to: {overview_path}")
        return

    skill_path = Path(arg).resolve()
    if not skill_path.exists():
        print(f"Error: skill path not found: {skill_path}")
        sys.exit(1)

    passed, total, failed, optional, out_path = _run_single(skill_path, rules_path)
    print(f"Report saved to: {out_path}")
    print(f"Summary: {passed}/{total} passed, {failed} required failures, {optional} optional gaps")


if __name__ == "__main__":
    main()
