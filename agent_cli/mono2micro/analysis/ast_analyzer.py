"""AST and structural code parser for Python, JavaScript/TypeScript, and Java."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from mono2micro.models.graph import (
    DependencyEdge,
    DependencyEdgeType,
    DependencyNode,
    DependencyNodeType,
)


class ASTAnalyzer:
    """Extracts nodes and dependency edges across Python, JS/TS, and Java source files."""

    def __init__(self, root_dir: str):
        self.root_dir = str(Path(root_dir).resolve())

    def analyze_file(self, file_path: str) -> Tuple[List[DependencyNode], List[DependencyEdge]]:
        """Analyze a single file and return its defined nodes and outgoing edges."""
        abs_path = os.path.join(self.root_dir, file_path) if not os.path.isabs(file_path) else file_path
        rel_path = os.path.relpath(abs_path, self.root_dir).replace("\\", "/")

        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return [], []

        ext = os.path.splitext(abs_path)[1].lower()
        if ext == ".py":
            return self._analyze_python(abs_path, rel_path)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            return self._analyze_javascript(abs_path, rel_path)
        elif ext == ".java":
            return self._analyze_java(abs_path, rel_path)

        return [], []

    def _analyze_python(self, abs_path: str, rel_path: str) -> Tuple[List[DependencyNode], List[DependencyEdge]]:
        nodes: List[DependencyNode] = []
        edges: List[DependencyEdge] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            # Fallback to single file module node on parse failure
            mod_node = DependencyNode(
                id=f"mod:{rel_path}",
                name=os.path.basename(rel_path),
                file_path=rel_path,
                node_type=DependencyNodeType.MODULE,
                language="python",
                lines_of_code=1,
            )
            return [mod_node], []

        loc = len(content.splitlines())
        mod_id = f"mod:{rel_path}"
        mod_node = DependencyNode(
            id=mod_id,
            name=os.path.basename(rel_path),
            file_path=rel_path,
            node_type=DependencyNodeType.MODULE,
            language="python",
            lines_of_code=loc,
        )
        nodes.append(mod_node)

        # Walk AST for classes, functions, imports, and calls
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_id = f"cls:{rel_path}:{node.name}"
                cls_node = DependencyNode(
                    id=cls_id,
                    name=node.name,
                    file_path=rel_path,
                    node_type=DependencyNodeType.CLASS,
                    language="python",
                    lines_of_code=getattr(node, "end_lineno", node.lineno) - node.lineno + 1 if hasattr(node, "lineno") else 1,
                    package_or_namespace=os.path.dirname(rel_path),
                )
                nodes.append(cls_node)
                # Class belongs to module
                edges.append(DependencyEdge(
                    source_id=cls_id,
                    target_id=mod_id,
                    edge_type=DependencyEdgeType.IMPORTS,
                    weight=0.5,
                ))
                # Inheritance edges
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        edges.append(DependencyEdge(
                            source_id=cls_id,
                            target_id=f"type:{base.id}",
                            edge_type=DependencyEdgeType.INHERITS,
                            weight=2.0,
                            evidence_line=node.lineno,
                        ))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    edges.append(DependencyEdge(
                        source_id=mod_id,
                        target_id=f"import:{alias.name}",
                        edge_type=DependencyEdgeType.IMPORTS,
                        weight=1.0,
                        evidence_line=node.lineno,
                    ))

            elif isinstance(node, ast.ImportFrom):
                target_module = node.module or ""
                edges.append(DependencyEdge(
                    source_id=mod_id,
                    target_id=f"import:{target_module}",
                    edge_type=DependencyEdgeType.IMPORTS,
                    weight=1.0,
                    evidence_line=node.lineno,
                ))

            elif isinstance(node, ast.Call):
                func_name = ""
                is_import_module = False
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if node.func.attr == "import_module":
                        is_import_module = True

                # Dynamic dependency detection (Python)
                if func_name == "getattr" and len(node.args) >= 2:
                    attr_arg = node.args[1]
                    is_literal_str = isinstance(attr_arg, ast.Constant) and isinstance(attr_arg.value, str)
                    if not is_literal_str:
                        edges.append(DependencyEdge(
                            source_id=mod_id,
                            target_id="dynamic:getattr",
                            edge_type=DependencyEdgeType.CALLS,
                            weight=1.0,
                            evidence_line=getattr(node, "lineno", None),
                            untracked_dynamic=True,
                        ))
                elif is_import_module or func_name == "import_module":
                    edges.append(DependencyEdge(
                        source_id=mod_id,
                        target_id="dynamic:importlib.import_module",
                        edge_type=DependencyEdgeType.IMPORTS,
                        weight=1.0,
                        evidence_line=getattr(node, "lineno", None),
                        untracked_dynamic=True,
                    ))
                elif func_name == "__import__":
                    edges.append(DependencyEdge(
                        source_id=mod_id,
                        target_id="dynamic:__import__",
                        edge_type=DependencyEdgeType.IMPORTS,
                        weight=1.0,
                        evidence_line=getattr(node, "lineno", None),
                        untracked_dynamic=True,
                    ))

                if func_name and func_name not in ("len", "str", "int", "print", "range"):
                    edges.append(DependencyEdge(
                        source_id=mod_id,
                        target_id=f"call:{func_name}",
                        edge_type=DependencyEdgeType.CALLS,
                        weight=0.5,
                        evidence_line=getattr(node, "lineno", None),
                    ))

        return nodes, edges

    def _analyze_javascript(self, abs_path: str, rel_path: str) -> Tuple[List[DependencyNode], List[DependencyEdge]]:
        nodes: List[DependencyNode] = []
        edges: List[DependencyEdge] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return [], []

        loc = len(content.splitlines())
        mod_id = f"mod:{rel_path}"
        mod_node = DependencyNode(
            id=mod_id,
            name=os.path.basename(rel_path),
            file_path=rel_path,
            node_type=DependencyNodeType.MODULE,
            language="javascript",
            lines_of_code=loc,
            package_or_namespace=os.path.dirname(rel_path),
        )
        nodes.append(mod_node)

        # Regex parsing for imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        ]
        for pat in import_patterns:
            for match in re.finditer(pat, content):
                imp = match.group(1)
                edges.append(DependencyEdge(
                    source_id=mod_id,
                    target_id=f"import:{imp}",
                    edge_type=DependencyEdgeType.IMPORTS,
                    weight=1.0,
                ))

        # Classes
        for match in re.finditer(r'class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?', content):
            cls_name = match.group(1)
            parent = match.group(2)
            cls_id = f"cls:{rel_path}:{cls_name}"
            nodes.append(DependencyNode(
                id=cls_id,
                name=cls_name,
                file_path=rel_path,
                node_type=DependencyNodeType.CLASS,
                language="javascript",
                package_or_namespace=os.path.dirname(rel_path),
            ))
            if parent:
                edges.append(DependencyEdge(
                    source_id=cls_id,
                    target_id=f"type:{parent}",
                    edge_type=DependencyEdgeType.INHERITS,
                    weight=2.0,
                ))

        return nodes, edges

    def _analyze_java(self, abs_path: str, rel_path: str) -> Tuple[List[DependencyNode], List[DependencyEdge]]:
        nodes: List[DependencyNode] = []
        edges: List[DependencyEdge] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return [], []

        loc = len(content.splitlines())
        mod_id = f"mod:{rel_path}"
        mod_node = DependencyNode(
            id=mod_id,
            name=os.path.basename(rel_path),
            file_path=rel_path,
            node_type=DependencyNodeType.MODULE,
            language="java",
            lines_of_code=loc,
            package_or_namespace=os.path.dirname(rel_path),
        )
        nodes.append(mod_node)

        # Package statement
        pkg_match = re.search(r'package\s+([a-zA-Z0-9_.]+);', content)
        if pkg_match:
            mod_node.package_or_namespace = pkg_match.group(1)

        # Import statements
        for match in re.finditer(r'import\s+([a-zA-Z0-9_.*]+);', content):
            edges.append(DependencyEdge(
                source_id=mod_id,
                target_id=f"import:{match.group(1)}",
                edge_type=DependencyEdgeType.IMPORTS,
                weight=1.0,
            ))

        # Classes and interfaces
        for match in re.finditer(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(class|interface)\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?(?:\s+implements\s+([A-Za-z0-9_,\s]+))?', content):
            kind = match.group(1)
            name = match.group(2)
            parent = match.group(3)
            cls_id = f"cls:{rel_path}:{name}"
            nodes.append(DependencyNode(
                id=cls_id,
                name=name,
                file_path=rel_path,
                node_type=DependencyNodeType.CLASS,
                language="java",
                package_or_namespace=mod_node.package_or_namespace,
            ))
            if parent:
                edges.append(DependencyEdge(
                    source_id=cls_id,
                    target_id=f"type:{parent}",
                    edge_type=DependencyEdgeType.INHERITS,
                    weight=2.0,
                ))

        return nodes, edges
