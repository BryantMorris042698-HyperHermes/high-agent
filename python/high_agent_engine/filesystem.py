"""File system integration — connect agents to the local file tree.

Agents can read, write, and browse files. Every operation is logged as a
FileEvent and surfaced in the TUI's CODE tab.
"""

from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.idea', '.vs', 'build', 'dist', '.cache', 'target',
}

_CODE_EXTS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go',
    '.c', '.cpp', '.h', '.java', '.sh', '.bash',
    '.md', '.txt', '.toml', '.yaml', '.yml', '.json',
    '.html', '.css', '.sql', '.env', '.cfg', '.ini',
    '.rb', '.php', '.swift', '.kt', '.dart',
}

# Line-level syntax coloring: (pattern_fn, color_pair_name)
# Applied in order — first match wins
_PYTHON_RULES = [
    (lambda s: s.startswith('#'),                            'dim'),
    (lambda s: s.startswith(('"""', "'''", 'r"""', "r'''")), 'phi_good'),
    (lambda s: s.startswith(('import ', 'from ')),           'regime_lbl_s'),
    (lambda s: s.startswith(('def ', 'async def ')),         'agent_lbl'),
    (lambda s: s.startswith('class '),                       'sidebar_h'),
    (lambda s: s.startswith('@'),                             'peach_lbl'),
    (lambda s: s.startswith(('return', 'yield')),            'teal_lbl'),
    (lambda s: s.startswith(('if ', 'elif ', 'else', 'for ',
                              'while ', 'with ', 'try', 'except', 'raise')), 'lavender'),
    (lambda s: 'TODO' in s or 'FIXME' in s or 'HACK' in s,  'phi_warn'),
    (lambda s: any(c in s for c in ('"', "'")),              'phi_good'),
]

_GENERIC_RULES = [
    (lambda s: s.startswith('#') or s.startswith('//'),     'dim'),
    (lambda s: s.startswith(('fn ', 'func ', 'def ', 'function ', 'pub fn')), 'agent_lbl'),
    (lambda s: s.startswith(('import', 'use ', 'require', 'include')),        'regime_lbl_s'),
]


def color_line(line: str, ext: str = '.py') -> str:
    """Return a color pair name for a source line based on its content."""
    stripped = line.strip()
    rules = _PYTHON_RULES if ext == '.py' else _GENERIC_RULES
    for pred, color in rules:
        try:
            if pred(stripped):
                return color
        except Exception:
            pass
    return 'text'


@dataclass
class FileEvent:
    """One agent file operation."""
    ts: float
    agent: str
    action: str    # "read" | "write" | "create" | "browse"
    path: str      # relative path within tree root
    content: str   # content (for write/create)
    line_count: int


class FileTree:
    """
    Connected directory — agents browse, read, and write files here.

    Usage:
        ft = FileTree("/path/to/project")
        content = ft.read("src/main.py")
        ft.write("src/output.py", new_code, agent="Refactor")
        for name, is_dir in ft.list_dir("src"):
            print(f"{'/' if is_dir else ' '} {name}")
    """

    def __init__(self, root: str):
        self.root = str(Path(root).expanduser().resolve())
        self.files: List[str] = []          # relative paths, sorted
        self.open_path: Optional[str] = None
        self._cache: Dict[str, str] = {}
        self.events: List[FileEvent] = []
        self.scan()

    def scan(self) -> int:
        """Scan root for code files. Returns count."""
        self.files = []
        try:
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = sorted(
                    d for d in dirnames
                    if not d.startswith('.') and d not in _IGNORE_DIRS
                )
                for fn in sorted(filenames):
                    if fn.startswith('.'):
                        continue
                    ext = Path(fn).suffix.lower()
                    if ext in _CODE_EXTS or not ext:
                        rel = os.path.relpath(os.path.join(dirpath, fn), self.root)
                        self.files.append(rel)
        except PermissionError:
            pass
        return len(self.files)

    def read(self, relpath: str, agent: str = "FileSystem") -> str:
        fullpath = os.path.join(self.root, relpath)
        try:
            with open(fullpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            content = f"# Cannot read: {e}"
        self._cache[relpath] = content
        self.open_path = relpath
        self.events.append(FileEvent(
            ts=time.time(), agent=agent, action="read",
            path=relpath, content=content,
            line_count=content.count('\n') + 1,
        ))
        if len(self.events) > 500:
            self.events = self.events[-500:]
        return content

    def write(self, relpath: str, content: str, agent: str = "FileSystem") -> bool:
        fullpath = os.path.join(self.root, relpath)
        existed = os.path.exists(fullpath)
        try:
            Path(fullpath).parent.mkdir(parents=True, exist_ok=True)
            with open(fullpath, 'w', encoding='utf-8') as f:
                f.write(content)
            self._cache[relpath] = content
            self.open_path = relpath
            if relpath not in self.files:
                self.files.append(relpath)
                self.files.sort()
            self.events.append(FileEvent(
                ts=time.time(), agent=agent,
                action="create" if not existed else "write",
                path=relpath, content=content,
                line_count=content.count('\n') + 1,
            ))
            if len(self.events) > 500:
                self.events = self.events[-500:]
            return True
        except Exception:
            return False

    def content(self, relpath: str) -> Optional[str]:
        """Return cached content for a file."""
        if relpath in self._cache:
            return self._cache[relpath]
        if relpath in self.files:
            return self.read(relpath)
        return None

    def list_dir(self, subpath: str = '') -> List[Tuple[str, bool]]:
        """Return (name, is_dir) pairs in a subdirectory."""
        prefix = subpath.rstrip('/') + '/' if subpath else ''
        result: List[Tuple[str, bool]] = []
        seen_dirs: set = set()
        for f in self.files:
            if not f.startswith(prefix):
                continue
            rest = f[len(prefix):]
            if '/' in rest:
                d = rest.split('/')[0]
                if d not in seen_dirs:
                    seen_dirs.add(d)
                    result.append((d, True))
            else:
                result.append((rest, False))
        return result

    def summary(self) -> str:
        """Short summary for display."""
        exts: Dict[str, int] = {}
        for f in self.files:
            ext = Path(f).suffix.lower() or 'other'
            exts[ext] = exts.get(ext, 0) + 1
        top = sorted(exts.items(), key=lambda x: -x[1])[:4]
        ext_str = '  '.join(f"{e}×{n}" for e, n in top)
        return f"{len(self.files)} files  {ext_str}"
