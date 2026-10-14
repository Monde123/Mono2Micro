"""Persistent audit logger and plan integrity verifier.

Enforces M1:
- Deterministic plan signing (canonical SHA-256 hash).
- Persistent JSONL append-only audit log at .mono2micro/audit.jsonl.
- Persistent approval records at .mono2micro/approvals.jsonl.
- Refuses step apply if the plan has drifted from the approved plan hash (tamper detection).
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from mono2micro.models.audit import AuditActionType, AuditLogRecord, PlanApproval
from mono2micro.models.plan import StranglerPlan
from mono2micro.models.time_utils import utc_now


class PlanTamperedError(Exception):
    """Raised when the current migration plan differs from the approved plan."""
    pass


class AuditLogger:
    """Manages persistent JSONL audit trail and plan signatures."""

    def __init__(self, target_directory: str):
        self.target_directory = str(Path(target_directory).resolve())
        self.mono2micro_dir = Path(self.target_directory) / ".mono2micro"
        self.audit_log_path = self.mono2micro_dir / "audit.jsonl"
        self.approvals_path = self.mono2micro_dir / "approvals.jsonl"
        self.approved_plan_path = self.mono2micro_dir / "approved_plan.json"

    def _ensure_dir(self):
        self.mono2micro_dir.mkdir(parents=True, exist_ok=True)

    def log_action(
        self,
        action: AuditActionType,
        plan_id: str,
        plan_hash: str,
        step_number: Optional[int] = None,
        actor: str = "local_developer",
        details: Optional[dict] = None,
    ) -> AuditLogRecord:
        """Append an immutable audit entry to audit.jsonl."""
        self._ensure_dir()
        record = AuditLogRecord(
            record_id=f"AUD-{uuid4().hex[:12]}",
            timestamp=utc_now(),
            actor=actor,
            action=action,
            plan_id=plan_id,
            plan_hash=plan_hash,
            step_number=step_number,
            target_path=self.target_directory,
            details=details or {},
        )
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(record.to_jsonl_line() + "\n")
        return record

    def record_approval(
        self,
        plan: StranglerPlan,
        step_number: int,
        approval_token: str,
        approver: str = "human_operator",
    ) -> PlanApproval:
        """Persist human approval for a specific plan hash and step."""
        self._ensure_dir()
        plan_hash = plan.plan_hash or plan.compute_canonical_hash()

        approval = PlanApproval(
            plan_id=plan.plan_id,
            plan_hash=plan_hash,
            step_number=step_number,
            approver=approver,
            approval_token=approval_token,
            approved_at=utc_now(),
            persisted_path=str(self.approvals_path),
        )

        # Append to approvals.jsonl
        with open(self.approvals_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(approval.model_dump(mode="json"), sort_keys=True) + "\n")

        # Save snapshot of approved plan for tamper diffing
        with open(self.approved_plan_path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(mode="json"), f, indent=2, sort_keys=True)

        # Also write to general audit log
        self.log_action(
            action=AuditActionType.PLAN_APPROVED,
            plan_id=plan.plan_id,
            plan_hash=plan_hash,
            step_number=step_number,
            actor=approver,
            details={"approval_token": approval_token},
        )
        return approval

    def get_latest_approval(self, step_number: int) -> Optional[PlanApproval]:
        """Read latest approval for a given step from approvals.jsonl."""
        if not self.approvals_path.exists():
            return None
        latest: Optional[PlanApproval] = None
        with open(self.approvals_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                app = PlanApproval(**data)
                if app.step_number == step_number:
                    latest = app
        return latest

    def verify_plan_integrity(self, current_plan: StranglerPlan, step_number: int) -> Tuple[bool, str]:
        """Verify that the current plan exactly matches the approved plan hash.

        Returns (is_valid, message). If modified, returns False and logs PLAN_TAMPER_DETECTED.
        """
        current_hash = current_plan.compute_canonical_hash()
        approval = self.get_latest_approval(step_number)

        if not approval:
            return False, f"Step {step_number} has no recorded approval in {self.approvals_path}."

        if approval.plan_hash != current_hash:
            msg = (
                f"SECURITY BLOCK: Current plan hash '{current_hash}' does not match "
                f"the approved plan hash '{approval.plan_hash}'. "
                f"The plan was modified after approval. Execution is refused."
            )
            self.log_action(
                action=AuditActionType.PLAN_TAMPER_DETECTED,
                plan_id=current_plan.plan_id,
                plan_hash=current_hash,
                step_number=step_number,
                details={
                    "approved_hash": approval.plan_hash,
                    "current_hash": current_hash,
                    "reason": "Plan content was modified after human approval",
                },
            )
            return False, msg

        return True, "Plan integrity verified: current plan matches approved signature."

    def read_all_audit_records(self) -> List[AuditLogRecord]:
        """Read all historical audit records in chronological order."""
        if not self.audit_log_path.exists():
            return []
        records = []
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(AuditLogRecord(**json.loads(line)))
        return records
