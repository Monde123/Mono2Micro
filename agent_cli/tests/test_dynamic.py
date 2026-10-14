import tempfile
import os
from mono2micro.analysis.ast_analyzer import ASTAnalyzer

def test_dynamic_dependency_detection():
    with tempfile.TemporaryDirectory() as tmp:
        # File containing all dynamic patterns
        fpath = os.path.join(tmp, "dynamic_code.py")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(
                "import importlib\n"
                "mod = importlib.import_module('plugin_module')\n"
                "obj = getattr(target_obj, dynamic_attr_name)\n"
                "mod2 = __import__('another_module')\n"
            )
        analyzer = ASTAnalyzer(tmp)
        nodes, edges = analyzer.analyze_file("dynamic_code.py")
        dynamic_edges = [e for e in edges if e.untracked_dynamic]
        assert len(dynamic_edges) == 3

        # Clean file without dynamic patterns
        clean_path = os.path.join(tmp, "clean_code.py")
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(
                "import math\n"
                "from datetime import datetime\n"
                "class Service:\n"
                "    def process(self):\n"
                "        val = getattr(self, 'literal_attr')\n"
                "        return math.sqrt(16)\n"
            )
        clean_nodes, clean_edges = analyzer.analyze_file("clean_code.py")
        clean_dynamic = [e for e in clean_edges if e.untracked_dynamic]
        assert len(clean_dynamic) == 0

