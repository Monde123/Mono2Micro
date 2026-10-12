"""Tests for Quality Gate and strict zero-averaging policy."""

import pytest
from mono2micro.models.quality_gate import (
    QualityGateCriterion,
    QualityGateResult,
    QualityGateCategory,
    CriterionStatus,
)


def test_quality_gate_passes_when_all_mandatory_pass():
    result = QualityGateResult(
        step_number=1,
        criteria=[
            QualityGateCriterion(
                criterion_id="QG-1",
                category=QualityGateCategory.REGRESSION_TESTS,
                title="All existing unit tests pass",
                is_mandatory=True,
                status=CriterionStatus.PASSED,
                evidence="54 passed in 2.1s"
            ),
            QualityGateCriterion(
                criterion_id="QG-2",
                category=QualityGateCategory.ARCHITECTURAL_BOUNDARY,
                title="No direct external database queries",
                is_mandatory=True,
                status=CriterionStatus.PASSED,
                evidence="AST scan found 0 cross-boundary database calls"
            )
        ]
    )
    assert result.overall_passed is True
    assert result.critical_failures_count == 0
    assert result.blocker_summary_fr is None


def test_quality_gate_strictly_fails_on_single_mandatory_failure_no_averaging():
    """Even if 9 out of 10 tests pass (90%), ONE critical failure MUST block."""
    criteria = [
        QualityGateCriterion(
            criterion_id=f"QG-{i}",
            category=QualityGateCategory.REGRESSION_TESTS,
            title=f"Test Suite Part {i}",
            is_mandatory=True,
            status=CriterionStatus.PASSED
        ) for i in range(1, 10)
    ]
    # Add 1 failing mandatory criterion
    criteria.append(
        QualityGateCriterion(
            criterion_id="QG-10",
            category=QualityGateCategory.DATA_CONSISTENCY,
            title="Database foreign key integrity check",
            is_mandatory=True,
            status=CriterionStatus.FAILED,
            failure_details="Orphaned records detected during dry-run"
        )
    )

    result = QualityGateResult(
        step_number=1,
        criteria=criteria
    )

    # STRICT ASSERTIONS: NO AVERAGING ALLOWED
    assert result.overall_passed is False
    assert result.critical_failures_count == 1
    assert result.passed_mandatory_count == 9
    assert result.blocker_summary_fr is not None
    assert "Database foreign key integrity check" in result.blocker_summary_fr


def test_quality_gate_fails_when_mandatory_criterion_is_skipped_or_unverified():
    """An unexecuted or skipped test CANNOT be assumed to pass."""
    result = QualityGateResult(
        step_number=1,
        criteria=[
            QualityGateCriterion(
                criterion_id="QG-1",
                category=QualityGateCategory.REGRESSION_TESTS,
                title="Regression suite",
                is_mandatory=True,
                status=CriterionStatus.PASSED
            ),
            QualityGateCriterion(
                criterion_id="QG-2",
                category=QualityGateCategory.API_CONTRACT,
                title="Consumer-driven contract test",
                is_mandatory=True,
                status=CriterionStatus.UNVERIFIED,
                failure_details="Test environment was unreachable"
            )
        ]
    )

    assert result.overall_passed is False
    assert result.skipped_mandatory_count == 1
    assert "NON VÉRIFIÉ(S)" in result.blocker_summary_fr
