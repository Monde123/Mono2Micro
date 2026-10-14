"""Tests for LEAD contracts across M1-M6."""

import pytest
from datetime import datetime, timezone
from mono2micro.models.time_utils import utc_now
from mono2micro.models.plan import (
    StranglerPlan,
    StranglerStep,
    RoutingStrategyType,
    DataOwnershipPlan,
    DataSeparationStrategy,
    RollbackProcedure,
)
from mono2micro.models.audit import AuditActionType, AuditLogRecord, PlanApproval
from mono2micro.models.graph import (
    DependencyNode,
    DependencyNodeType,
    DependencyEdge,
    DependencyEdgeType,
    DependencyGraph,
    PartitionCandidate,
    PartitionEvaluation,
)
from mono2micro.models.data_analysis import (
    TableAccessRecord,
    TableAccessOperation,
    ForeignKeyRelation,
    TransactionScope,
    DataLayerAnalysis,
)
from mono2micro.models.benchmarks import (
    BenchmarkCorpusItem,
    BenchmarkBaselineMode,
    BenchmarkRunResult,
)
from mono2micro.models.migration import (
    CodemodKind,
    CodemodResult,
    FixLoopAttempt,
    FixLoopSession,
)
from mono2micro.models.memory import (
    AdversarialDiffRule,
    AdversarialDiffViolation,
    GroundedMemoryProof,
    TaskMemoryItem,
)
from mono2micro.models.budget import LLMBudgetTracker
from mono2micro.models.doctor import CommandCapability, DoctorReport


def _sample_plan(title: str = "Step 1: Extract Billing") -> StranglerPlan:
    step = StranglerStep(
        step_number=1,
        title=title,
        description="Extract billing domain",
        target_bounded_context="Billing",
        files_in_scope=["services/billing.py"],
        routing_strategy=RoutingStrategyType.API_GATEWAY_REVERSE_PROXY,
        routing_details="/api/v1/billing/* -> billing:8081",
        data_ownership=DataOwnershipPlan(
            strategy=DataSeparationStrategy.DATABASE_PER_SERVICE,
            source_tables=["invoices"],
            target_tables=["billing_invoices"],
            data_rollback_strategy="restore snapshot",
        ),
        rollback=RollbackProcedure(
            steps_fr=["git checkout main"],
            git_revert_command="git revert HEAD",
            routing_fallback_action="route traffic back to monolith",
            data_revert_action="replay event logs",
            estimated_time_to_recover_minutes=5,
        ),
    )
    return StranglerPlan(
        plan_id="PLAN-001",
        target_architecture_summary="Strangler Fig Migration",
        steps=[step],
        estimated_total_steps=1,
    )


def test_plan_canonical_hash_is_deterministic_and_sensitive_to_changes():
    plan1 = _sample_plan()
    hash1 = plan1.compute_canonical_hash()

    plan2 = _sample_plan()
    hash2 = plan2.compute_canonical_hash()

    assert hash1 == hash2
    assert len(hash1) == 64

    # Modifying title or scope must change the hash immediately
    plan_tampered = _sample_plan(title="Step 1: Tampered Unauthorized Step")
    hash_tampered = plan_tampered.compute_canonical_hash()
    assert hash_tampered != hash1


def test_audit_log_record_serialization():
    rec = AuditLogRecord(
        record_id="AUD-001",
        action=AuditActionType.PLAN_APPROVED,
        plan_id="PLAN-001",
        plan_hash="abc123456789",
        step_number=1,
        target_path="/repo",
        details={"approved_by": "lead_architect"},
    )
    line = rec.to_jsonl_line()
    assert "PLAN_APPROVED" in line
    assert "abc123456789" in line
    assert "AUD-001" in line


def test_dependency_graph_and_partition_models():
    node1 = DependencyNode(
        id="mod_billing",
        name="billing.py",
        file_path="src/billing.py",
        node_type=DependencyNodeType.MODULE,
        language="python",
        lines_of_code=120,
    )
    node2 = DependencyNode(
        id="mod_orders",
        name="orders.py",
        file_path="src/orders.py",
        node_type=DependencyNodeType.MODULE,
        language="python",
        lines_of_code=200,
    )
    edge = DependencyEdge(
        source_id="mod_orders",
        target_id="mod_billing",
        edge_type=DependencyEdgeType.CALLS,
        weight=2.0,
    )
    graph = DependencyGraph(
        nodes={"mod_billing": node1, "mod_orders": node2},
        edges=[edge],
    )
    assert graph.node_count == 2
    assert graph.edge_count == 1

    part = PartitionCandidate(
        domain_name="Billing",
        node_ids=["mod_billing"],
        files=["src/billing.py"],
        tables_owned=["invoices"],
    )
    eval_report = PartitionEvaluation(
        partitions=[part],
        modularity_q=0.45,
        inter_domain_coupling_ratio=0.15,
        shared_tables_count=0,
    )
    assert eval_report.modularity_q == 0.45


def test_data_analysis_models():
    access = TableAccessRecord(
        table_name="accounts",
        operation=TableAccessOperation.WRITE,
        file_path="src/auth.py",
        line_number=42,
        in_transaction=True,
    )
    fk = ForeignKeyRelation(
        source_table="orders",
        source_column="customer_id",
        target_table="customers",
        target_column="id",
    )
    scope = TransactionScope(
        scope_id="tx_1",
        file_path="src/checkout.py",
        function_or_method="process_order",
        tables_accessed=["orders", "inventory", "payments"],
        spans_multiple_domains=True,
        domains_involved=["Orders", "Inventory", "Payments"],
    )
    analysis = DataLayerAnalysis(
        tables_detected=["accounts", "orders", "customers", "inventory", "payments"],
        table_accesses=[access],
        foreign_keys=[fk],
        transactions=[scope],
        raw_sql_queries_count=1,
    )
    assert len(analysis.tables_detected) == 5
    assert len(analysis.transactions) == 1


def test_llm_budget_tracker_hard_stop():
    tracker = LLMBudgetTracker(max_tokens=1000, max_cost_usd=0.01)
    # First small usage
    assert tracker.record_usage(prompt_tokens=200, completion_tokens=100) is True
    assert tracker.hard_stop_reached is False

    # Second usage crossing 1000 token limit
    assert tracker.record_usage(prompt_tokens=500, completion_tokens=300) is False
    assert tracker.hard_stop_reached is True
    assert "Token budget ceiling reached" in str(tracker.stop_reason)


def test_grounded_memory_proof_model():
    proof = GroundedMemoryProof(
        file_path="src/models.py",
        line_number=28,
        content_sha256="deadbeef1234",
    )
    mem = TaskMemoryItem(
        memory_id="MEM-1",
        key="table_ownership:users",
        observation="Table users owned by auth domain",
        proof=proof,
    )
    assert mem.proof.line_number == 28
    assert mem.is_expired is False
