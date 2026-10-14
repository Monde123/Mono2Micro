"""Dependency graph and structural analysis models.

Supports AST extraction (Python, JS/TS, Java) and offline partitioning (M2):
- Module, class, and call dependency graph
- Coupling, cohesion, and modularity (Q) calculation
- Louvain / spectral modular graph clustering
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class DependencyNodeType(str, Enum):
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    DATABASE_TABLE = "DATABASE_TABLE"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"


class DependencyEdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    READS_TABLE = "READS_TABLE"
    WRITES_TABLE = "WRITES_TABLE"
    TRANSACTION_BOUNDARY = "TRANSACTION_BOUNDARY"


class DependencyNode(BaseModel):
    id: str
    name: str
    file_path: str
    node_type: DependencyNodeType
    language: str
    lines_of_code: int = 0
    package_or_namespace: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DependencyEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: DependencyEdgeType
    weight: float = 1.0
    call_count: int = 1
    evidence_line: Optional[int] = None
    untracked_dynamic: bool = False


class DependencyGraph(BaseModel):
    """Complete graph representation exported in JSON with schema."""
    nodes: Dict[str, DependencyNode] = Field(default_factory=dict)
    edges: List[DependencyEdge] = Field(default_factory=list)
    graph_version: str = "1.0"

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def untracked_dynamic_count(self) -> int:
        return sum(1 for e in self.edges if getattr(e, "untracked_dynamic", False))



class PartitionCandidate(BaseModel):
    """A candidate domain partition produced by clustering or heuristics."""
    domain_name: str
    node_ids: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    tables_owned: List[str] = Field(default_factory=list)
    tables_referenced: List[str] = Field(default_factory=list)
    internal_edge_weight: float = 0.0
    external_edge_weight: float = 0.0
    cohesion_score: float = 0.0


class PartitionEvaluation(BaseModel):
    """Evaluation metrics for a proposed set of partitions."""
    partitions: List[PartitionCandidate] = Field(default_factory=list)
    modularity_q: float = 0.0
    inter_domain_coupling_ratio: float = 0.0
    shared_tables_count: int = 0
    shared_tables_detail: Dict[str, List[str]] = Field(default_factory=dict)
    cross_domain_transactions_count: int = 0
    unassigned_nodes_count: int = 0
