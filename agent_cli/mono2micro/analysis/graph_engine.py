"""Graph engine, modularity calculation, Louvain clustering, and schema export."""

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from mono2micro.models.graph import (
    DependencyEdge,
    DependencyEdgeType,
    DependencyGraph,
    DependencyNode,
    DependencyNodeType,
    PartitionCandidate,
    PartitionEvaluation,
)
from mono2micro.analysis.ast_analyzer import ASTAnalyzer
from mono2micro.analysis.data_analyzer import DataAnalyzer


class GraphEngine:
    """Constructs comprehensive codebase graph and applies modularity clustering."""

    def __init__(self, root_dir: str):
        self.root_dir = str(Path(root_dir).resolve())
        self.ast_analyzer = ASTAnalyzer(self.root_dir)
        self.data_analyzer = DataAnalyzer(self.root_dir)

    def build_graph(self) -> DependencyGraph:
        """Scan all repository files and build complete DependencyGraph."""
        nodes: Dict[str, DependencyNode] = {}
        edges: List[DependencyEdge] = []

        # 1. Code AST scanning
        for root, _, files in os.walk(self.root_dir):
            if any(p in root.split(os.sep) for p in (".git", "node_modules", "dist", "build", "venv", ".mono2micro")):
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.root_dir).replace("\\", "/")
                file_nodes, file_edges = self.ast_analyzer.analyze_file(rel_path)
                for n in file_nodes:
                    nodes[n.id] = n
                edges.extend(file_edges)

        # 2. Data layer scanning
        data_analysis = self.data_analyzer.analyze()
        for tbl in data_analysis.tables_detected:
            tbl_id = f"table:{tbl}"
            nodes[tbl_id] = DependencyNode(
                id=tbl_id,
                name=tbl,
                file_path="",
                node_type=DependencyNodeType.DATABASE_TABLE,
                language="sql",
            )

        for acc in data_analysis.table_accesses:
            mod_id = f"mod:{acc.file_path}"
            tbl_id = f"table:{acc.table_name}"
            edge_type = DependencyEdgeType.WRITES_TABLE if acc.operation.value == "WRITE" else DependencyEdgeType.READS_TABLE
            edges.append(DependencyEdge(
                source_id=mod_id,
                target_id=tbl_id,
                edge_type=edge_type,
                weight=2.0,
                evidence_line=acc.line_number,
            ))

        return DependencyGraph(nodes=nodes, edges=edges)

    def export_graph_json(self, graph: DependencyGraph, output_path: str):
        """Export graph into human-readable JSON with schema header."""
        payload = {
            "$schema": "https://mono2micro.dev/schemas/dependency-graph.v1.json",
            "meta": {
                "root_dir": self.root_dir,
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
            },
            "nodes": [n.model_dump() for n in graph.nodes.values()],
            "edges": [e.model_dump() for e in graph.edges],
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def compute_modularity(self, graph: DependencyGraph, partition: Dict[str, str]) -> float:
        """Compute Newman-Girvan modularity Q for a given node->community mapping."""
        # Build adjacency with weights
        adj: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        total_weight = 0.0

        for edge in graph.edges:
            w = edge.weight
            adj[edge.source_id][edge.target_id] += w
            adj[edge.target_id][edge.source_id] += w
            total_weight += w

        if total_weight == 0.0:
            return 0.0

        # Degree (weighted)
        k: Dict[str, float] = {}
        for u in graph.nodes:
            k[u] = sum(adj[u].values())

        m2 = 2.0 * total_weight
        q = 0.0

        # Sum over communities
        communities: Dict[str, List[str]] = defaultdict(list)
        for node_id, comm in partition.items():
            communities[comm].append(node_id)

        for comm, members in communities.items():
            for u in members:
                for v in members:
                    a_uv = adj[u].get(v, 0.0)
                    e_uv = (k.get(u, 0.0) * k.get(v, 0.0)) / m2
                    q += (a_uv - e_uv)

        return q / m2

    def cluster_louvain(self, graph: DependencyGraph) -> PartitionEvaluation:
        """Partition graph using greedy Louvain modularity optimization."""
        # Focus on module nodes
        module_nodes = [n for n in graph.nodes.values() if n.node_type == DependencyNodeType.MODULE]
        if not module_nodes:
            return PartitionEvaluation()

        # Build undirected graph between modules
        adj: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        node_degrees: Dict[str, float] = defaultdict(float)
        total_m = 0.0

        # Link modules directly or through shared targets (imports / tables / classes)
        # 1. Direct and indirect edges
        target_to_sources: Dict[str, Set[str]] = defaultdict(set)
        for e in graph.edges:
            target_to_sources[e.target_id].add(e.source_id)

        for target, sources in target_to_sources.items():
            source_list = list(sources)
            for i in range(len(source_list)):
                for j in range(i + 1, len(source_list)):
                    u = source_list[i]
                    v = source_list[j]
                    weight = 1.0 if not target.startswith("table:") else 3.0
                    adj[u][v] += weight
                    adj[v][u] += weight
                    total_m += weight

        for u in adj:
            node_degrees[u] = sum(adj[u].values())

        # Initial partition: each node in its own cluster or grouped by directory if small
        partition: Dict[str, str] = {}
        for n in module_nodes:
            dir_name = os.path.dirname(n.file_path).split(os.sep)[0] or "core"
            partition[n.id] = dir_name

        # One pass of greedy modularity transfer
        node_ids = [n.id for n in module_nodes]
        for node in node_ids:
            best_comm = partition.get(node, "core")
            current_comm = best_comm
            neighbor_comms = set()
            for neighbor in adj[node]:
                if neighbor in partition:
                    neighbor_comms.add(partition[neighbor])

            # Test transferring to neighbor community
            best_gain = 0.0
            for cand_comm in neighbor_comms:
                if cand_comm == current_comm:
                    continue
                # evaluate internal vs external edge weight gain
                weight_to_cand = sum(adj[node][nbr] for nbr in adj[node] if partition.get(nbr) == cand_comm)
                weight_to_curr = sum(adj[node][nbr] for nbr in adj[node] if partition.get(nbr) == current_comm)
                gain = weight_to_cand - weight_to_curr
                if gain > best_gain:
                    best_gain = gain
                    best_comm = cand_comm

            if best_gain > 0:
                partition[node] = best_comm

        # Build PartitionCandidates
        comm_members: Dict[str, List[DependencyNode]] = defaultdict(list)
        for n in module_nodes:
            comm = partition.get(n.id, "default")
            comm_members[comm].append(n)

        # Detect tables owned vs shared
        table_to_comms: Dict[str, Set[str]] = defaultdict(set)
        for e in graph.edges:
            if e.target_id.startswith("table:"):
                tbl_name = e.target_id.replace("table:", "")
                comm = partition.get(e.source_id, "default")
                table_to_comms[tbl_name].add(comm)

        candidates: List[PartitionCandidate] = []
        total_internal_weight = 0.0
        total_external_weight = 0.0

        for comm_name, members in comm_members.items():
            member_ids = {m.id for m in members}
            member_files = [m.file_path for m in members]

            internal_w = 0.0
            external_w = 0.0
            for u in member_ids:
                for v, w in adj[u].items():
                    if v in member_ids:
                        internal_w += w / 2.0
                    else:
                        external_w += w

            total_internal_weight += internal_w
            total_external_weight += external_w

            tables_owned = [tbl for tbl, comms in table_to_comms.items() if comms == {comm_name}]
            tables_ref = [tbl for tbl, comms in table_to_comms.items() if comm_name in comms and len(comms) > 1]

            cohesion = internal_w / (internal_w + external_w + 1e-6)

            candidates.append(PartitionCandidate(
                domain_name=comm_name.capitalize(),
                node_ids=list(member_ids),
                files=member_files,
                tables_owned=tables_owned,
                tables_referenced=tables_ref,
                internal_edge_weight=internal_w,
                external_edge_weight=external_w,
                cohesion_score=round(cohesion, 4),
            ))

        # Shared tables count and detail
        shared_tables: Dict[str, List[str]] = {}
        for tbl, comms in table_to_comms.items():
            if len(comms) > 1:
                shared_tables[tbl] = sorted(comms)

        total_weight = total_internal_weight + total_external_weight
        coupling_ratio = round(total_external_weight / (total_weight + 1e-6), 4)
        q = self.compute_modularity(graph, partition)

        return PartitionEvaluation(
            partitions=candidates,
            modularity_q=round(q, 4),
            inter_domain_coupling_ratio=coupling_ratio,
            shared_tables_count=len(shared_tables),
            shared_tables_detail=shared_tables,
        )
