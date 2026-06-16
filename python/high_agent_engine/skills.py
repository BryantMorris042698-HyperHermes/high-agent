"""Skill management for Python engine — mirrors rust/src/skills.rs."""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Skill storage locations (in priority order)
DEFAULT_SKILL_DIRS = [
    os.path.expanduser("~/.high-agent/skills"),
    os.path.expanduser("~/.hermes/skills"),
    "./skills",
]


@dataclass
class Skill:
    """A reusable agent skill."""
    name: str
    category: str
    trigger: str
    description: str
    steps: List[str]
    pitfalls: List[str]
    source: str = ""  # file path where loaded from
    version: int = 1

    @classmethod
    def from_file(cls, path: str) -> "Skill":
        """Parse a skill from a markdown file."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        name = os.path.splitext(os.path.basename(path))[0]

        # Parse frontmatter
        trigger = ""
        category = "general"
        description = ""
        steps = []
        pitfalls = []
        in_steps = False
        in_pitfalls = False
        body_lines = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("trigger:"):
                trigger = line.split("trigger:", 1)[1].strip().strip('"').strip("'")
            elif line.strip().startswith("category:"):
                category = line.split("category:", 1)[1].strip()
            elif line.strip().startswith("name:"):
                name = line.split("name:", 1)[1].strip().strip('"').strip("'")
            elif line.strip() == "## Steps" or line.strip() == "## Steps\n":
                in_steps = True
                in_pitfalls = False
                if description == "" and body_lines:
                    description = " ".join(l.strip() for l in body_lines if l.strip() and not l.strip().startswith("#"))[:200]
                body_lines = []
            elif line.strip() == "## Pitfalls" or line.strip() == "## Pitfalls\n":
                in_pitfalls = True
                in_steps = False
                body_lines = []
            elif line.strip().startswith("## "):
                in_steps = False
                in_pitfalls = False
                body_lines = []
            elif in_steps and (line.strip().startswith("1. ") or
                               line.strip().startswith("- ") or
                               re.match(r"^\d+\.\s+\*\*", line)):
                step = re.sub(r"^\d+\.\s+", "", line).strip()
                step = re.sub(r"^\*\*|\*\*$", "", step)
                if step:
                    steps.append(step)
            elif in_pitfalls and (line.strip().startswith("- ") or line.strip().startswith("* ")):
                pit = line.strip()[1:].strip()
                if pit:
                    pitfalls.append(pit)
            elif not line.strip().startswith("#") and not line.strip().startswith("---"):
                body_lines.append(line)

        return cls(
            name=name,
            category=category,
            trigger=trigger,
            description=description or "No description",
            steps=steps,
            pitfalls=pitfalls,
            source=path,
        )

    def to_markdown(self) -> str:
        """Serialize back to markdown format."""
        lines = [
            "---",
            f"name: {self.name}",
            f"category: {self.category}",
            f"trigger: \"{self.trigger}\"",
            "---",
            "",
            f"# {self.name}",
            "",
            self.description,
            "",
            "## Steps",
            "",
        ]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
        if self.pitfalls:
            lines.append("## Pitfalls")
            lines.append("")
            for pit in self.pitfalls:
                lines.append(f"- {pit}")
            lines.append("")
        return "\n".join(lines)


class SkillManager:
    """
    Manages skill discovery, loading, and storage.
    Mirrors rust/src/skills.rs.
    """

    def __init__(self, skill_dirs: Optional[List[str]] = None):
        self.skills: Dict[str, Skill] = {}
        self.loaded: Dict[str, Skill] = {}
        self.skill_dirs = skill_dirs or DEFAULT_SKILL_DIRS
        self._yaml_skills: List[Dict] = []
        self._load_all()
        self._load_yaml_skills()

    def _load_all(self) -> None:
        """Scan all skill directories and load every skill file."""
        for d in self.skill_dirs:
            path = Path(d)
            if not path.exists():
                continue
            for f in path.rglob("*.md"):
                if f.name.lower() in ("readme.md", "changelog.md", "contributing.md"):
                    continue
                try:
                    skill = Skill.from_file(str(f))
                    self.skills[skill.name] = skill
                except Exception:
                    pass  # Skip malformed skills

    def _load_yaml_skills(self) -> None:
        """Load metric-triggered skills from skills.yaml files."""
        search_paths = [
            Path("./skills/skills.yaml"),
            Path(__file__).parent.parent.parent / "skills" / "skills.yaml",
        ]
        for p in search_paths:
            if not p.exists():
                continue
            try:
                try:
                    import yaml
                    with open(p) as f:
                        data = yaml.safe_load(f)
                except ImportError:
                    # Minimal yaml fallback — parse the skills.yaml structure manually
                    data = self._parse_simple_yaml(str(p))
                for entry in (data or {}).get("skills", []):
                    self._yaml_skills.append(entry)
            except Exception:
                pass
            break

    @staticmethod
    def _parse_simple_yaml(path: str) -> Dict:
        """Minimal skills.yaml parser — handles the known format without pyyaml."""
        import re as _re
        skills = []
        current: Optional[Dict] = None
        trigger: Optional[Dict] = None
        with open(path) as f:
            for line in f:
                stripped = line.rstrip()
                indent = len(line) - len(line.lstrip())
                if stripped.strip().startswith("- id:"):
                    if current:
                        skills.append(current)
                    current = {"id": stripped.split(":", 1)[1].strip(), "trigger": {}, "action": ""}
                    trigger = None
                elif current is not None:
                    kv = stripped.strip()
                    if kv.startswith("name:"):
                        current["name"] = kv.split(":", 1)[1].strip()
                    elif kv.startswith("description:"):
                        current["description"] = kv.split(":", 1)[1].strip()
                    elif kv.startswith("tags:"):
                        current["tags"] = kv.split(":", 1)[1].strip()
                    elif kv.startswith("trigger:") and ":" not in kv[8:]:
                        trigger = {}
                        current["trigger"] = trigger
                    elif trigger is not None and kv.startswith("metric:"):
                        trigger["metric"] = kv.split(":", 1)[1].strip()
                    elif trigger is not None and kv.startswith("operator:"):
                        trigger["operator"] = kv.split(":", 1)[1].strip().strip('"')
                    elif trigger is not None and kv.startswith("threshold:"):
                        try:
                            trigger["threshold"] = float(kv.split(":", 1)[1].strip())
                        except ValueError:
                            pass
                    elif kv.startswith("action:") and "|" in kv:
                        current["action"] = ""
                    elif current.get("action") is not None and indent >= 6 and trigger is None:
                        current["action"] = (current.get("action", "") + " " + kv.strip()).strip()
        if current:
            skills.append(current)
        return {"skills": skills}

    @staticmethod
    def _snap_get(snap, key: str):
        """Get a metric from a snap that is either a dict or an object with attributes."""
        if isinstance(snap, dict):
            return snap.get(key)
        return getattr(snap, key, None)

    def match_metrics(self, snap) -> List[Dict]:
        """Return yaml skills whose metric triggers match the current snapshot."""
        _ALIASES = {"max_cyclomatic": "max_v"}
        matching = []
        for skill in self._yaml_skills:
            trigger = skill.get("trigger", {})
            if not isinstance(trigger, dict):
                continue
            raw_metric = trigger.get("metric", "")
            metric = _ALIASES.get(raw_metric, raw_metric)
            op = trigger.get("operator", ">")
            threshold = trigger.get("threshold", 0)
            val = self._snap_get(snap, metric)
            if val is None:
                continue
            hit = (
                (op == ">" and val > threshold) or
                (op == "<" and val < threshold) or
                (op == ">=" and val >= threshold) or
                (op == "<=" and val <= threshold)
            )
            if hit:
                matching.append(skill)
        return matching

    def all_skills_context(self, snap=None) -> str:
        """Format all skills with active markers for injection into prompts."""
        lines: List[str] = []
        if self._yaml_skills:
            applicable = {s["id"] for s in (self.match_metrics(snap) if snap else [])}
            for s in self._yaml_skills:
                active = s["id"] in applicable
                prefix = "★ ACTIVE  " if active else "  ·  "
                lines.append(f"{prefix}[{s.get('id', '?')}] {s.get('name', '')}")
                lines.append(f"           {s.get('description', '')}")
                if active and s.get("action"):
                    lines.append(f"           Action: {s['action'][:120].strip()}")
        for skill in self.skills.values():
            lines.append(f"  ·  [{skill.category}] {skill.name}: {skill.description[:80]}")
        return "\n".join(lines) if lines else "No skills loaded."

    def load_skill(self, name: str) -> Optional[Skill]:
        """Load a skill by name into the active set."""
        if name in self.skills:
            self.loaded[name] = self.skills[name]
            return self.skills[name]
        return None

    def unload_skill(self, name: str) -> None:
        """Remove a skill from the active set."""
        self.loaded.pop(name, None)

    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """List all available skills, optionally filtered by category."""
        if category:
            return [s for s in self.skills.values() if s.category == category]
        return list(self.skills.values())

    def list_loaded(self) -> List[Skill]:
        """List currently loaded skills."""
        return list(self.loaded.values())

    def create_skill(self, name: str, category: str, trigger: str,
                     description: str, steps: List[str],
                     pitfalls: Optional[List[str]] = None) -> Skill:
        """Create a new skill and save it."""
        skill = Skill(
            name=name,
            category=category,
            trigger=trigger,
            description=description,
            steps=steps,
            pitfalls=pitfalls or [],
        )
        self.skills[name] = skill
        self.loaded[name] = skill

        # Save to default skill dir
        save_dir = Path(os.path.expanduser("~/.high-agent/skills"))
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{name}.md"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(skill.to_markdown())

        return skill

    def delete_skill(self, name: str) -> bool:
        """Delete a skill from the store and filesystem."""
        skill = self.skills.pop(name, None)
        self.loaded.pop(name, None)
        if skill and skill.source:
            try:
                os.remove(skill.source)
            except OSError:
                pass
        return skill is not None

    def update_skill(self, name: str, **kwargs) -> Optional[Skill]:
        """Update fields of an existing skill."""
        if name not in self.skills:
            return None
        skill = self.skills[name]
        for key, val in kwargs.items():
            if hasattr(skill, key):
                setattr(skill, key, val)
        self.loaded[name] = skill

        # Re-save to source
        if skill.source:
            with open(skill.source, "w", encoding="utf-8") as f:
                f.write(skill.to_markdown())
        return skill

    def search(self, query: str) -> List[Skill]:
        """Search skills by name, description, or trigger."""
        q = query.lower()
        return [
            s for s in self.skills.values()
            if q in s.name.lower() or q in s.description.lower() or q in s.trigger.lower()
        ]

    def categories(self) -> List[str]:
        """List all unique categories."""
        return sorted(set(s.category for s in self.skills.values()))

    def __repr__(self) -> str:
        return f"SkillManager({len(self.skills)} skills, {len(self.loaded)} loaded)"
