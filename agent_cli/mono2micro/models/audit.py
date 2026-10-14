"""Persistent audit log and plan approval contracts.

Enforces:
- SHA-256 signed plan verification (M1)
- Persistent JSONL audit logging (who, what, plan_hash, timestamp, target)
- Tamper detection preventing execution if the plan was modified after approval.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from mono2micro.models.time_utils import utc_now


class AuditActionType(str, Enum):
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_APPROVED = "PLAN_APPROVED"
    PLAN_REJECTED = "PLAN_REJECTED"
    PLAN_TAMPER_DETECTED = "PLAN_TAMPER_DETECTED"
    STEP_APPLY_ATTEMPT = "STEP_APPLY_ATTEMPT"
    STEP_APPLY_SUCCESS = "STEP_APPLY_SUCCESS"
    STEP_APPLY_FAILED = "STEP_APPLY_FAILED"
    QUALITY_GATE_EVALUATED = "QUALITY_GATE_EVALUATED"
    ROLLBACK_TRIGGERED = "ROLLBACK_TRIGGERED"
    DEVIL_ADVOCATE_BLOCKED = "DEVIL_ADVOCATE_BLOCKED"


class AuditLogRecord(BaseModel):
    """An immutable audit trail record stored in JSONL format."""
    record_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str = "local_developer"
    action: AuditActionType
    plan_id: str
    plan_hash: str
    step_number: Optional[int] = None
    target_path: str
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_jsonl_line(self) -> str:
        """Convert record to a single JSON line."""
        data = self.model_dump(mode="json")
        return json.dumps(data, sort_keys=True)


class PlanApproval(BaseModel):
    """Approval token and signature certifying human sign-off on a specific plan hash."""
    plan_id: str
    plan_hash: str
    step_number: int
    approver: str = "human_operator"
    approval_token: str
    approved_at: datetime = Field(default_factory=utc_now)
    persisted_path: Optional[str] = None
