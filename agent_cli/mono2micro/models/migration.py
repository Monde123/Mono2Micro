"""Migration, deterministic codemod, and fix-loop models.

Enforces M4 requirements:
- Deterministic AST/pattern codemods
- Generate -> Test -> Fix loop (max 3 attempts with automatic rollback on failure)
- Gateway routing & feature flag scaffolding
- Token, cost, and duration accounting
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from mono2micro.models.time_utils import utc_now


class CodemodKind(str, Enum):
    EXTRACT_MODULE = "EXTRACT_MODULE"
    INJECT_FACADE = "INJECT_FACADE"
    GENERATE_GATEWAY_ROUTE = "GENERATE_GATEWAY_ROUTE"
    GENERATE_FEATURE_FLAG = "GENERATE_FEATURE_FLAG"
    SPLIT_DATABASE_SCHEMA = "SPLIT_DATABASE_SCHEMA"


class CodemodResult(BaseModel):
    kind: CodemodKind
    success: bool
    files_modified: List[str] = Field(default_factory=list)
    files_created: List[str] = Field(default_factory=list)
    diff_patch: str = ""
    error_message: Optional[str] = None


class FixLoopAttempt(BaseModel):
    attempt_number: int
    proposed_diff: str
    test_passed: bool
    test_output: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0


class FixLoopSession(BaseModel):
    step_number: int
    target_context: str
    max_attempts: int = 3
    attempts: List[FixLoopAttempt] = Field(default_factory=list)
    final_success: bool = False
    restored_automatically: bool = False
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    total_duration_seconds: float = 0.0


class GatewayRouteConfig(BaseModel):
    service_name: str
    route_prefix: str
    upstream_url: str
    timeout_ms: int = 5000
    strip_prefix: bool = False
    feature_flag_key: Optional[str] = None


class FeatureFlagConfig(BaseModel):
    flag_key: str
    enabled: bool = False
    description: str = ""
    percentage_rollout: int = 0
    service_name: str = ""
