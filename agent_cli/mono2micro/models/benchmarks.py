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
    status: str = "MEASURED"
    n: Optional[int] = 1
    raw_output_path: Optional[str] = None
    tool_commit: Optional[str] = None
    not_run_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
    duration_seconds: Optional[float] = None
    files_analyzed: Optional[int] = None
    tables_analyzed: Optional[int] = None
    domains_proposed: Optional[int] = None
    modularity_q: Optional[float] = None
    inter_domain_coupling_ratio: Optional[float] = None
    shared_tables_count: Optional[int] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    devil_advocate_false_block_rate: Optional[float] = None
    end_to_end_tests_passed: Optional[bool] = None
    attempts_needed: Optional[int] = None
    tokens_consumed: Optional[int] = None
    cost_usd: Optional[float] = None
    notes: str = ""


class BenchmarkEvaluationReport(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    results: List[BenchmarkRunResult] = Field(default_factory=list)
    corpus_runs: List[BenchmarkRunResult] = Field(default_factory=list)
    ablation_summary: Dict[str, Any] = Field(default_factory=dict)

