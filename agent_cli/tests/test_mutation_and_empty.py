import tempfile
from pathlib import Path
from mono2micro.analysis.graph_engine import GraphEngine

def test_empty_repo_control():
    with tempfile.TemporaryDirectory() as tmp:
        engine = GraphEngine(tmp)
        graph = engine.build_graph()
        partitions = engine.cluster_louvain(graph)
        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert len(partitions.partitions) == 0

def test_mutation_sensitivity():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("import b\n", encoding="utf-8")
        (root / "b.py").write_text("x = 1\n", encoding="utf-8")
        engine1 = GraphEngine(tmp)
        g1 = engine1.build_graph()
        q1 = engine1.cluster_louvain(g1).modularity_q

        (root / "b.py").unlink()
        engine2 = GraphEngine(tmp)
        g2 = engine2.build_graph()
        assert g2.node_count < g1.node_count
