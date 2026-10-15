"""Quality Gate and verification models.

Enforces Workflow Step 9:
- Only runs user-authorized commands.
- Mandatory criteria must ALL pass.
- STRICTLY PROHIBITS score averaging or compensating critical failures.
- Non-executed or skipped mandatory tests immediately fail the gate.
"""

from pydantic import BaseModel, Field, root_validator
from typing import List, Optional
from enum import Enum
from datetime import datetime
from mono2micro.models.time_utils import utc_now


class CriterionStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNVERIFIED = "UNVERIFIED"


class QualityGateCategory(str, Enum):
    REGRESSION_TESTS = "REGRESSION_TESTS"
    API_CONTRACT = "API_CONTRACT"
    DATA_CONSISTENCY = "DATA_CONSISTENCY"
    ARCHITECTURAL_BOUNDARY = "ARCHITECTURAL_BOUNDARY"
    FAILURE_BEHAVIOR = "FAILURE_BEHAVIOR"
    BUILD_AND_LINT = "BUILD_AND_LINT"


class QualityGateCriterion(BaseModel):
    """A specific verification checkpoint."""
    criterion_id: str
    category: QualityGateCategory
    title: str
    is_mandatory: bool = True
    status: CriterionStatus = CriterionStatus.UNVERIFIED
    command_executed: Optional[str] = None
    output_summary: Optional[str] = None
    evidence: Optional[str] = None
    failure_details: Optional[str] = None


class QualityGateResult(BaseModel):
    """Outcome of Quality Gate evaluation."""
    evaluated_at: datetime = Field(default_factory=utc_now)
    step_number: Optional[int] = None
    criteria: List[QualityGateCriterion] = Field(default_factory=list)
    overall_passed: bool = False
    critical_failures_count: int = 0
    skipped_mandatory_count: int = 0
    passed_mandatory_count: int = 0
    total_criteria_count: int = 0
    blocker_summary: Optional[str] = None
    blocker_summary_fr: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def enforce_strict_no_averaging_policy(cls, values) -> dict:
        """Strict non-negotiable rule: Any failing or unverified mandatory criterion blocks the gate completely."""
        criteria = values.get("criteria", [])
        mandatory_criteria = [c for c in criteria if c.is_mandatory]
        failures = [c for c in mandatory_criteria if c.status == CriterionStatus.FAILED]
        skipped = [c for c in mandatory_criteria if c.status in (CriterionStatus.SKIPPED, CriterionStatus.UNVERIFIED)]
        passed = [c for c in mandatory_criteria if c.status == CriterionStatus.PASSED]

        values["critical_failures_count"] = len(failures)
        values["skipped_mandatory_count"] = len(skipped)
        values["passed_mandatory_count"] = len(passed)
        values["total_criteria_count"] = len(criteria)

        if failures or skipped:
            values["overall_passed"] = False
            reasons = []
            if failures:
                reasons.append(f"{len(failures)} mandatory criterion/criteria FAILED: " + ", ".join(f.title for f in failures))
            if skipped:
                reasons.append(f"{len(skipped)} mandatory criterion/criteria UNVERIFIED: " + ", ".join(s.title for s in skipped))
            msg = " | ".join(reasons)
            values["blocker_summary"] = msg
            values["blocker_summary_fr"] = msg
        else:
            values["overall_passed"] = len(mandatory_criteria) > 0 and len(passed) == len(mandatory_criteria)
            if values["overall_passed"]:
                values["blocker_summary"] = None
                values["blocker_summary_fr"] = None

        return values
