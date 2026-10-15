"""Migration plan models.

Enforces Principles 3, 4, 5, 6, 7 of Hammad et al. (2023):
- Incremental evolution
- Low coupling first
- Strangler Fig routing
- Explicit data ownership & separation
- Test criteria & explicit rollback procedure per step
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
from mono2micro.models.time_utils import utc_now


class RoutingStrategyType(str, Enum):
    API_GATEWAY_REVERSE_PROXY = "API_GATEWAY_REVERSE_PROXY"
    FEATURE_FLAG_IN_CODE = "FEATURE_FLAG_IN_CODE"
    STRANGLER_FACADE = "STRANGLER_FACADE"
    DNS_OR_INGRESS_SPLIT = "DNS_OR_INGRESS_SPLIT"
    IN_PROCESS_ADAPTER = "IN_PROCESS_ADAPTER"


class DataSeparationStrategy(str, Enum):
    SHARED_DATABASE_TEMPORARY = "SHARED_DATABASE_TEMPORARY"
    LOGICAL_SCHEMA_SPLIT = "LOGICAL_SCHEMA_SPLIT"
    DATABASE_PER_SERVICE = "DATABASE_PER_SERVICE"
    DUAL_WRITE_SYNCHRONIZATION = "DUAL_WRITE_SYNCHRONIZATION"
    EVENT_DRIVEN_CDC = "EVENT_DRIVEN_CDC"
    READ_REPLICA_OR_CACHE = "READ_REPLICA_OR_CACHE"


class DataOwnershipPlan(BaseModel):
    """Specification of data boundary and consistency."""
    strategy: DataSeparationStrategy
    source_tables: List[str] = Field(default_factory=list)
    target_tables: List[str] = Field(default_factory=list)
    foreign_keys_handled: List[str] = Field(default_factory=list)
    consistency_model: str = "Strong ACID inside service; Eventual consistency across services"
    dual_write_required: bool = False
    migration_script_path: Optional[str] = None
    data_rollback_strategy: str


class RollbackProcedure(BaseModel):
    """Explicit, testable rollback procedure."""
    steps: List[str] = Field(default_factory=list)
    steps_fr: Optional[List[str]] = None
    git_revert_command: str
    routing_fallback_action: str
    data_revert_action: str
    estimated_time_to_recover_minutes: int
    tested_in_sandbox: bool = False

    def __init__(self, **data):
        s = data.get("steps") or data.get("steps_fr") or []
        data["steps"] = s
        data["steps_fr"] = s
        super().__init__(**data)


class StranglerStep(BaseModel):
    """A single, verifiable, reversible migration step."""
    step_number: int
    title: str
    description: str
    target_bounded_context: str
    files_in_scope: List[str] = Field(default_factory=list)
    routing_strategy: RoutingStrategyType
    routing_details: str
    data_ownership: DataOwnershipPlan
    success_criteria: List[str] = Field(default_factory=list)
    rollback: RollbackProcedure
    
    # Safety and permissions
    is_destructive: bool = False
    is_data_migration: bool = False
    approved_by_human: bool = False
    approval_token: Optional[str] = None
    applied_at: Optional[datetime] = None
    applied_git_branch: Optional[str] = None


class StranglerPlan(BaseModel):
    """Overall phased migration roadmap."""
    plan_id: str
    created_at: datetime = Field(default_factory=utc_now)
    target_architecture_summary: str
    steps: List[StranglerStep]
    estimated_total_steps: int = 0
    prerequisites_met: bool = False
    prerequisite_blockers: List[str] = Field(default_factory=list)
    principles_applied: List[str] = Field(default_factory=list)
    plan_hash: Optional[str] = None

    def compute_canonical_hash(self) -> str:
        """Compute deterministic SHA-256 hash of immutable plan architecture contents."""
        import hashlib
        import json

        canonical_steps = []
        for step in sorted(self.steps, key=lambda s: s.step_number):
            canonical_steps.append({
                "step_number": step.step_number,
                "title": step.title,
                "target_bounded_context": step.target_bounded_context,
                "files_in_scope": sorted(step.files_in_scope),
                "routing_strategy": str(step.routing_strategy),
                "routing_details": step.routing_details,
                "data_strategy": str(step.data_ownership.strategy),
                "source_tables": sorted(step.data_ownership.source_tables),
                "target_tables": sorted(step.data_ownership.target_tables),
                "git_revert_command": step.rollback.git_revert_command,
            })

        payload = {
            "plan_id": self.plan_id,
            "target_architecture_summary": self.target_architecture_summary,
            "steps": canonical_steps,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        computed = hashlib.sha256(encoded).hexdigest()
        self.plan_hash = computed
        return computed
