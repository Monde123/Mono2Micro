"""Benchmark suite, corpus definition, and scoring contracts.

Corpus items with pinned commits (M3):
- JPetStore (Java MyBatis)
- DayTrader (Java EE/JPA)
- AcmeAir (Java / Node.js)
- Plants (Java / Spring)
- 2 Node.js & Python reference applications

Honesty rule:
If ground truth is not available, surrogate metrics (modularity, coupling ratio,
shared tables count) are explicitly declared as surrogates without pretending.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mono2micro.models.time_utils import utc_now


class BenchmarkBaselineMode(str, Enum):
    HEURISTIC_ONLY = "HEURISTIC_ONLY"
    LLM_ONLY_NO_TOOLS = "LLM_ONLY_NO_TOOLS"
    HYBRID_AGENT = "HYBRID_AGENT"


class BenchmarkCorpusItem(BaseModel):
    name: str
    target_language: str
    git_repo_url: Optional[str] = None
    pinned_commit: str
    has_ground_truth: bool = False
    ground_truth_description: Optional[str] = None
    surrogate_metrics_used: List[str] = Field(default_factory=list)
    reference_domains: List[str] = Field(default_factory=list)
    reference_tables: List[str] = Field(default_factory=list)


class BenchmarkRunResult(BaseModel):
    benchmark_name: str
    baseline_mode: BenchmarkBaselineMode
    timestamp: datetime = Field(default_factory=utc_now)
    duration_seconds: float
    files_analyzed: int
    tables_analyzed: int
    domains_proposed: int
    modularity_q: float
    inter_domain_coupling_ratio: float
    shared_tables_count: int
    precision: Optional[float] = None
    recall: Optional[float] = None
    devil_advocate_false_block_rate: float = 0.0
    end_to_end_tests_passed: bool = False
    attempts_needed: int = 1
    tokens_consumed: int = 0
    cost_usd: float = 0.0
    notes: str = ""


class BenchmarkEvaluationReport(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    corpus_runs: List[BenchmarkRunResult] = Field(default_factory=list)
    ablation_summary: Dict[str, Any] = Field(default_factory=dict)
