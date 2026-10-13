"""Tests for the VerifierAgent: boundary check, stable ids and shell-free execution."""

import tempfile
from pathlib import Path

from mono2micro.agents.verifier import VerifierAgent
from mono2micro.models.discovery import DiscoveryReport, DatabaseCouplingInfo
from mono2micro.models.plan import (
    StranglerStep,
    RoutingStrategyType,
    DataOwnershipPlan,
    DataSeparationStrategy,
    RollbackProcedure,
)
from mono2micro.models.quality_gate import CriterionStatus


def _step(files, tables):
    return StranglerStep(
        step_number=1,
        title="Extract Billing",
        description="pilot",
        target_bounded_context="Billing",
        files_in_scope=files,
        routing_strategy=RoutingStrategyType.STRANGLER_FACADE,
        routing_details="gateway",
        data_ownership=DataOwnershipPlan(
            strategy=DataSeparationStrategy.LOGICAL_SCHEMA_SPLIT,
            source_tables=tables,
            data_rollback_strategy="mirror",
        ),
        rollback=RollbackProcedure(
            steps_fr=["a", "b"],
            git_revert_command="git revert HEAD",
            routing_fallback_action="route to monolith",
            data_revert_action="restore",
            estimated_time_to_recover_minutes=10,
        ),
    )


def _discovery(access_map):
    return DiscoveryReport(
        target_directory="/tmp/x",
        database_coupling=DatabaseCouplingInfo(
            detected_models_or_tables=list(access_map),
            cross_module_table_access=access_map,
        ),
    )


def test_boundary_fails_when_outsider_accesses_owned_table():
    with tempfile.TemporaryDirectory() as tmp:
        step = _step(["src/billing/invoice.py"], ["Invoice"])
        disc = _discovery({"Invoice": ["src/billing/invoice.py", "src/reports/export.py"]})
        crit = VerifierAgent(tmp).run_architectural_boundary_check(step, disc)
        assert crit.status == CriterionStatus.FAILED
        assert "src/reports/export.py" in crit.failure_details


def test_boundary_passes_when_only_scoped_files_access_table():
    with tempfile.TemporaryDirectory() as tmp:
        step = _step(["src/billing/invoice.py"], ["Invoice"])
        disc = _discovery({"Invoice": ["src/billing/invoice.py"]})
        crit = VerifierAgent(tmp).run_architectural_boundary_check(step, disc)
        assert crit.status == CriterionStatus.PASSED


def test_boundary_detects_residual_legacy_connection():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "svc.py"
        f.write_text('DB = "postgres://legacy/db"', encoding="utf-8")
        crit = VerifierAgent(tmp).run_architectural_boundary_check(_step(["svc.py"], []))
        assert crit.status == CriterionStatus.FAILED


def test_command_ids_are_stable_across_calls():
    with tempfile.TemporaryDirectory() as tmp:
        v = VerifierAgent(tmp)
        a = v.run_user_authorized_test_command("echo hi", "t")
        b = v.run_user_authorized_test_command("echo hi", "t")
        assert a.criterion_id == b.criterion_id


def test_commands_never_run_through_a_shell():
    with tempfile.TemporaryDirectory() as tmp:
        marker = Path(tmp) / "pwned"
        v = VerifierAgent(tmp)
        # With shell=True, '&&' would execute 'touch'. Without a shell it is a plain argument.
        v.run_user_authorized_test_command(f"echo ok && touch {marker}", "inject")
        assert not marker.exists()


def test_empty_command_fails_cleanly():
    with tempfile.TemporaryDirectory() as tmp:
        crit = VerifierAgent(tmp).run_user_authorized_test_command("   ", "empty")
        assert crit.status == CriterionStatus.FAILED
