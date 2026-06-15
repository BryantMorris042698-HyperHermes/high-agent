"""Static codebase analyzer — produces JSON graph from real source files."""

from __future__ import annotations
import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from .graph import DirectedGraph, Node, Edge

class CodebaseCrawler:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.graph = DirectedGraph()
        self.import_map: Dict[str, List[str]] = {}
        self.call_graph: Dict[str, List[str]] = {}

    def scan(self, extensions: List[str] = None) -> DirectedGraph:
        if extensions is None:
            extensions = [".py", ".rs", ".go", ".js", ".ts", ".java", ".c", ".cpp"]
        self._scan_python() if any(e == ".py" for e in extensions) else None
        self._scan_rust() if any(e == ".rs" for e in extensions) else None
        self._build_graph()
        return self.graph

    def _scan_python(self) -> None:
        for path in self.root.rglob("*.py"):
            if "venv" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts:
                continue
            self._analyze_python_file(path)

    def _analyze_python_file(self, path: Path) -> None:
        try:
            content = path.read_text()
            tree = ast.parse(content, filename=str(path))
            module = path.parent.name
            rel_path = str(path.relative_to(self.root))
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
            self.import_map[str(path)] = imports

            for func in funcs:
                node = Node(func, module, rel_path)
                # Cyclomatic complexity approximation: 1 + num conditionals
                cond_count = len([n for n in ast.walk(ast.parse(""))])
                node.cyclomatic = 1.0 + sum(1 for _ in re.finditer(r'\b(if|elif|while|for|except|and|or)\b', content))
                node.lines = len(content.split('\n'))
                self.graph.add_node(node)
                self.call_graph[func] = []
        except: pass

    def _scan_rust(self) -> None:
        for path in self.root.rglob("*.rs"):
            if "target" in path.parts: continue
            self._analyze_rust_file(path)

    def _analyze_rust_file(self, path: Path) -> None:
        try:
            content = path.read_text()
            module = path.parent.name
            rel_path = str(path.relative_to(self.root))
            func_pattern = re.compile(r'fn\s+(\w+)\s*[\(<]')
            funcs = func_pattern.findall(content)
            impl_pattern = re.compile(r'impl\s+(?:\w+\s+)?(\w+)')
            impls = set(impl_pattern.findall(content))

            for func in funcs:
                node = Node(func, module, rel_path)
                node.cyclomatic = 1.0 + len(re.findall(r'\b(if|else|while|for|match|loop)\b', content))
                node.lines = len(content.split('\n'))
                self.graph.add_node(node)
        except: pass

    def _build_graph(self) -> None:
        for src_path, imports in self.import_map.items():
            src_node = None
            for node in self.graph.nodes.values():
                if str(self.root / node.file) == src_path:
                    src_node = node
                    break
            if not src_node: continue
            for imp in imports:
                for tgt in self.graph.nodes.values():
                    if tgt.id == imp or imp in tgt.id:
                        e = Edge(src_node.id, tgt.id)
                        e.edge_type = "import"
                        self.graph.add_edge(e)

    def to_json(self) -> str:
        return self.graph.to_json()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <path_to_codebase>")
    else:
        crawler = CodebaseCrawler(sys.argv[1])
        graph = crawler.scan()
        print(f"Graph: {graph.n_nodes()} nodes, {graph.n_edges()} edges")
        print(crawler.to_json())