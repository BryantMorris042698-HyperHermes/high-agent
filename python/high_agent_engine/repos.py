"""Repository management for Python engine — mirrors rust/src/repos.rs."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import time


@dataclass
class Repo:
    """A tracked repository."""
    name: str
    url: str
    local_path: str
    branch: str = "main"
    last_sync: Optional[float] = None  # unix timestamp
    last_phi: float = 0.0
    n_nodes: int = 0
    n_edges: int = 0
    status: str = "unknown"  # unknown, cloned, synced, error

    def sync(self) -> bool:
        """Sync the repo (git fetch + optionally pull)."""
        try:
            if not Path(self.local_path).exists():
                subprocess.run(
                    ["git", "clone", "--depth", "1", self.url, self.local_path],
                    check=True, capture_output=True, timeout=120
                )
                self.status = "cloned"
            else:
                subprocess.run(
                    ["git", "-C", self.local_path, "fetch", "origin", self.branch],
                    check=True, capture_output=True, timeout=30
                )
                self.status = "synced"
            self.last_sync = time.time()
            return True
        except Exception:
            self.status = "error"
            return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "local_path": self.local_path,
            "branch": self.branch,
            "last_sync": self.last_sync,
            "last_phi": self.last_phi,
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Repo":
        return cls(**d)


class RepoManager:
    """
    Manages a collection of tracked repositories.
    Mirrors rust/src/repos.rs.
    """

    def __init__(self, state_file: Optional[str] = None):
        self.repos: Dict[str, Repo] = {}
        self.state_file = state_file or os.path.expanduser("~/.high-agent/repos/state.json")
        self._ensure_dir()
        self._load()

    def _ensure_dir(self) -> None:
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load repos from JSON state file."""
        if not Path(self.state_file).exists():
            return
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
            for name, d in data.get("repos", {}).items():
                self.repos[name] = Repo.from_dict(d)
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        """Persist repos to JSON state file."""
        data = {"repos": {name: r.to_dict() for name, r in self.repos.items()}}
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def add(self, name: str, url: str, local_path: Optional[str] = None,
            branch: str = "main") -> Repo:
        """Add and clone a new repository."""
        if local_path is None:
            # Default: clone into ~/.high-agent/repos/<name>
            local_path = os.path.join(
                os.path.expanduser("~/.high-agent/repos"), name
            )
        repo = Repo(name=name, url=url, local_path=local_path, branch=branch)
        repo.sync()
        self.repos[name] = repo
        self._save()
        return repo

    def remove(self, name: str) -> bool:
        """Remove a repository from tracking (does NOT delete local files)."""
        removed = self.repos.pop(name, None) is not None
        if removed:
            self._save()
        return removed

    def sync(self, name: Optional[str] = None) -> Dict[str, bool]:
        """Sync one or all repos. Returns dict of name -> success."""
        if name:
            result = {name: self.repos[name].sync() if name in self.repos else False}
        else:
            result = {n: r.sync() for n, r in self.repos.items()}
        self._save()
        return result

    def list(self) -> List[Repo]:
        """List all tracked repos."""
        return list(self.repos.values())

    def get(self, name: str) -> Optional[Repo]:
        """Get a repo by name."""
        return self.repos.get(name)

    def update_metrics(self, name: str, n_nodes: int, n_edges: int, phi: float) -> None:
        """Update graph metrics for a repo after analysis."""
        if name in self.repos:
            self.repos[name].n_nodes = n_nodes
            self.repos[name].n_edges = n_edges
            self.repos[name].last_phi = phi
            self._save()

    def __repr__(self) -> str:
        return f"RepoManager({len(self.repos)} repos)"
