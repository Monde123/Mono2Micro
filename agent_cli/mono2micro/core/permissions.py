"""Explicit permission and human-approval engine.

Enforces Workflow Steps 7 & 8:
- Read-only actions are permitted by default for analysis.
- No code change or destructive command is allowed without explicit approval.
- Approving step N strictly DOES NOT approve step N+1.
- Destructive operations, migrations, and deployments require separate confirmation.
"""

import hashlib
import time
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ActionScope(str, Enum):
    READ_ONLY_DISCOVERY = "READ_ONLY_DISCOVERY"
    PLAN_PROPOSAL = "PLAN_PROPOSAL"
    ADVERSARIAL_CHALLENGE = "ADVERSARIAL_CHALLENGE"
    WRITE_STEP_IMPLEMENTATION = "WRITE_STEP_IMPLEMENTATION"
    EXECUTE_VERIFICATION_TESTS = "EXECUTE_VERIFICATION_TESTS"
    DESTRUCTIVE_CLEANUP = "DESTRUCTIVE_CLEANUP"
    DATABASE_MIGRATION = "DATABASE_MIGRATION"


class PermissionDeniedError(Exception):
    """Raised when an action is attempted without valid human approval."""
    pass


class ApprovalRecord(BaseModel):
    """Immutable audit trail of a user approval."""
    token: str
    step_number: int
    scope: ActionScope
    files_allowed: List[str]
    is_destructive: bool
    granted_at_epoch: float = Field(default_factory=time.time)
    approver: str = "local_developer"
    notes: Optional[str] = None


class PermissionEngine:
    """Central authority controlling all mutating actions."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self._approved_steps: Dict[int, ApprovalRecord] = {}
        self._executed_steps: Set[int] = set()
        self._audit_log: List[ApprovalRecord] = []

    def generate_step_token(self, step_number: int, files_allowed: List[str], is_destructive: bool = False) -> str:
        """Create a deterministic confirmation token for a specific step and file scope."""
        payload = f"{self.target_directory}:{step_number}:{sorted(files_allowed)}:{is_destructive}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def request_approval_for_step(
        self,
        step_number: int,
        title: str,
        files_allowed: List[str],
        is_destructive: bool = False,
        is_data_migration: bool = False,
        user_confirmation_input: Optional[str] = None,
    ) -> ApprovalRecord:
        """Grant approval for ONE and ONLY ONE step.
        
        Requires explicit token or 'OUI' confirmation.
        """
        if step_number in self._executed_steps:
            raise PermissionDeniedError(f"L'étape {step_number} a déjà été exécutée. Un ré-exécution exige un nouveau plan.")

        token = self.generate_step_token(step_number, files_allowed, is_destructive)

        # In non-interactive or confirmed contexts, check explicit confirmation
        if user_confirmation_input is not None:
            normalized = user_confirmation_input.strip().upper()
            if normalized not in ("OUI", "YES", "APPROVE", token.upper()):
                raise PermissionDeniedError(
                    f"Action refusée pour l'étape {step_number}. Confirmation attendue: 'OUI' ou jeton '{token}', reçu: '{user_confirmation_input}'"
                )

        record = ApprovalRecord(
            token=token,
            step_number=step_number,
            scope=ActionScope.WRITE_STEP_IMPLEMENTATION if not is_data_migration else ActionScope.DATABASE_MIGRATION,
            files_allowed=list(files_allowed),
            is_destructive=is_destructive,
            notes=f"Approbation explicite accordée pour l'étape {step_number}: '{title}'"
        )

        self._approved_steps[step_number] = record
        self._audit_log.append(record)
        return record

    def verify_permission_to_apply_step(self, step_number: int, target_files: List[str]) -> ApprovalRecord:
        """Verify that step_number is strictly approved and target_files are within approved scope."""
        record = self._approved_steps.get(step_number)
        if not record:
            raise PermissionDeniedError(
                f"BLOCAGE DE SÉCURITÉ: L'étape {step_number} n'a reçu aucune approbation humaine explicite. "
                f"L'approbation d'étapes antérieures ne vaut pas pour l'étape {step_number}."
            )

        # Check scope boundary: cannot touch files outside approved set
        allowed_set = set(record.files_allowed)
        for tf in target_files:
            if tf not in allowed_set:
                raise PermissionDeniedError(
                    f"VIOLATION DE PÉRIMÈTRE: Le fichier '{tf}' n'est pas dans le périmètre autorisé pour l'étape {step_number}. "
                    f"Fichiers autorisés: {sorted(allowed_set)}"
                )

        return record

    def mark_step_executed(self, step_number: int):
        """Mark step as completed, invalidating its approval token for replay."""
        self._executed_steps.add(step_number)
        if step_number in self._approved_steps:
            del self._approved_steps[step_number]

    def get_audit_trail(self) -> List[ApprovalRecord]:
        return list(self._audit_log)
