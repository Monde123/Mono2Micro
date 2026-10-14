"""Milestone 1 (M1) Tests: Signed Plan & Persistent Audit Log.

Acceptance criteria:
- Plan signed by canonical SHA-256 hash
- 'apply' refuses if current plan differs from approved plan (tamper detection)
- Persistent JSONL audit log (who, what, hash, timestamp)
- Approvals persisted across sessions
"""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from mono2micro.cli import app
from mono2micro.core.orchestrator import MigrationOrchestrator
from mono2micro.core.audit_logger import AuditLogger
from mono2micro.models.audit import AuditActionType


runner = CliRunner()


def _init_dummy_repo(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text(
        "# dummy monolith\n"
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/api/users')\n"
        "def users(): return 'users'\n"
    )
    (tmp_path / "requirements.txt").write_text("flask==2.3.0\npytest==7.0.0\n")
    tests = tmp_path / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_app.py").write_text("def test_users(): assert True\n")


def test_m1_plan_signed_by_canonical_hash(tmp_path):
    _init_dummy_repo(tmp_path)
    orch = MigrationOrchestrator(str(tmp_path))
    orch.step_1_discover()
    orch.step_3_analyze_domains()
    orch.step_4_compare_options()
    plan = orch.step_5_plan_migration()

    assert plan.plan_hash is not None
    assert len(plan.plan_hash) == 64
    assert plan.plan_hash == plan.compute_canonical_hash()

    # Verify audit record for PLAN_CREATED
    records = orch.audit_logger.read_all_audit_records()
    assert any(r.action == AuditActionType.PLAN_CREATED and r.plan_hash == plan.plan_hash for r in records)


def test_m1_persistent_approval_and_jsonl_audit_trail(tmp_path):
    _init_dummy_repo(tmp_path)
    orch = MigrationOrchestrator(str(tmp_path))
    orch.step_1_discover()
    orch.step_3_analyze_domains()
    orch.step_4_compare_options()
    plan = orch.step_5_plan_migration()

    # Request human approval
    token = orch.step_7_request_human_approval(step_number=1, user_input_confirmation="YES")
    assert token is not None

    # Check approvals.jsonl
    approvals_path = tmp_path / ".mono2micro" / "approvals.jsonl"
    assert approvals_path.exists()
    lines = approvals_path.read_text().strip().splitlines()
    assert len(lines) == 1
    appr_data = json.loads(lines[0])
    assert appr_data["step_number"] == 1
    assert appr_data["approval_token"] == token
    assert appr_data["plan_hash"] == plan.plan_hash

    # Check audit.jsonl contains PLAN_APPROVED
    audit_records = orch.audit_logger.read_all_audit_records()
    approved_records = [r for r in audit_records if r.action == AuditActionType.PLAN_APPROVED]
    assert len(approved_records) == 1
    assert approved_records[0].step_number == 1
    assert approved_records[0].plan_hash == plan.plan_hash


def test_m1_tamper_detection_refuses_execution_if_plan_modified(tmp_path):
    _init_dummy_repo(tmp_path)
    orch = MigrationOrchestrator(str(tmp_path))
    orch.step_1_discover()
    orch.step_3_analyze_domains()
    orch.step_4_compare_options()
    plan = orch.step_5_plan_migration()

    # Step 1 is approved
    orch.step_7_request_human_approval(step_number=1, user_input_confirmation="YES")

    # Integrity before tampering: valid
    is_valid, msg = orch.verify_plan_before_apply(step_number=1)
    assert is_valid is True

    # Tamper with the plan (e.g., sneaky scope expansion)
    plan.steps[0].files_in_scope.append("secrets/credentials.env")
    plan.compute_canonical_hash()

    # Integrity after tampering: MUST fail and record PLAN_TAMPER_DETECTED
    is_valid, msg = orch.verify_plan_before_apply(step_number=1)
    assert is_valid is False
    assert "SECURITY BLOCK" in msg

    records = orch.audit_logger.read_all_audit_records()
    tamper_records = [r for r in records if r.action == AuditActionType.PLAN_TAMPER_DETECTED]
    assert len(tamper_records) == 1
    assert tamper_records[0].step_number == 1


def test_m1_cli_approve_and_audit_commands(tmp_path):
    _init_dummy_repo(tmp_path)
    # Plan first
    res_plan = runner.invoke(app, ["plan", "--path", str(tmp_path)])
    assert res_plan.exit_code == 0

    # Approve via CLI
    res_approve = runner.invoke(app, ["approve", "--path", str(tmp_path), "--step", "1", "--confirm", "YES"])
    assert res_approve.exit_code == 0
    assert "approved and signed" in res_approve.stdout

    # Audit via CLI
    res_audit = runner.invoke(app, ["audit", "--path", str(tmp_path)])
    assert res_audit.exit_code == 0
    assert "PLAN_CREATED" in res_audit.stdout
    assert "PLAN_APPROVED" in res_audit.stdout
