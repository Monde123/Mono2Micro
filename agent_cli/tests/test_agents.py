"""Tests for specialized agent roles."""

import tempfile
from pathlib import Path
from mono2micro.agents.repo_analyzer import RepoAnalyzerAgent
from mono2micro.agents.domain_analyst import DomainAnalystAgent
from mono2micro.agents.migration_architect import MigrationArchitectAgent
from mono2micro.agents.test_adversary import TestAdversaryAgent
from mono2micro.models.discovery import DiscoveryReport, DetectedComponent, ComponentType, DatabaseCouplingInfo
from mono2micro.models.objectives import MigrationObjectiveClarification, MigrationGoalType
from mono2micro.models.options import ArchitectureOptionType
from mono2micro.models.plan import StranglerStep, RoutingStrategyType, DataOwnershipPlan, DataSeparationStrategy, RollbackProcedure
from mono2micro.models.adversarial import ObjectionSeverity


def test_domain_analyst_orders_low_coupling_first():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src" / "notifications").mkdir(parents=True)
        (root / "src" / "payments").mkdir(parents=True)

        discovery = DiscoveryReport(
            target_directory=tmp,
            database_coupling=DatabaseCouplingInfo(
                detected_models_or_tables=["PaymentTransaction", "Invoice", "PaymentMethod", "PaymentAudit", "NotificationLog"],
                cross_module_table_access={"PaymentTransaction": ["payments.py", "orders.py"]}
            )
        )

        analyst = DomainAnalystAgent(tmp)
        hypotheses = analyst.analyze_domains(discovery)

        assert len(hypotheses) >= 2
        # First domain should have higher feasibility (low coupling)
        assert hypotheses[0].extraction_feasibility_score >= hypotheses[-1].extraction_feasibility_score


def test_migration_architect_recommends_modular_monolith_on_small_team():
    architect = MigrationArchitectAgent()
    discovery = DiscoveryReport(
        target_directory="/tmp/fake",
        test_frameworks_detected=["jest"]
    )
    objectives = MigrationObjectiveClarification(
        primary_goal=MigrationGoalType.CODEBASE_MODULARITY,
        user_rationale="Spaghetti code in our team of 2 developers",
        current_team_size=2
    )

    domains = DomainAnalystAgent("/tmp/fake").analyze_domains(discovery)
    matrix = architect.compare_options(discovery, objectives, domains)

    assert matrix.recommended_option == ArchitectureOptionType.MODULAR_MONOLITH
    assert "Monolithe Modulaire" in matrix.synthesis_fr


def test_migration_architect_honors_user_specification_preference():
    architect = MigrationArchitectAgent()
    discovery = DiscoveryReport(
        target_directory="/tmp/fake",
        test_frameworks_detected=["jest"]
    )
    objectives = MigrationObjectiveClarification(
        primary_goal=MigrationGoalType.CODEBASE_MODULARITY,
        user_rationale="Small team",
        current_team_size=2
    )

    domains = DomainAnalystAgent("/tmp/fake").analyze_domains(discovery)
    
    # User explicitly requests KEEP_MONOLITH via specifications
    from mono2micro.config import UserSpecifications
    specs = UserSpecifications(preferred_architecture="KEEP_MONOLITH", team_size=2)
    matrix = architect.compare_options(discovery, objectives, domains, user_specs=specs)

    assert matrix.recommended_option == ArchitectureOptionType.KEEP_MONOLITH
    assert "KEEP_MONOLITH" in matrix.synthesis_fr


def test_test_adversary_blocks_when_table_accessed_outside_scope():
    adversary = TestAdversaryAgent()
    discovery = DiscoveryReport(
        target_directory="/tmp/fake",
        test_frameworks_detected=[],  # No tests = blocking
        database_coupling=DatabaseCouplingInfo(
            cross_module_table_access={"users": ["src/auth.py", "src/billing.py", "src/orders.py"]}
        )
    )

    step = StranglerStep(
        step_number=1,
        title="Extract Auth",
        description="Extract Auth service",
        target_bounded_context="Auth",
        files_in_scope=["src/auth.py"],  # billing.py and orders.py are outside scope!
        routing_strategy=RoutingStrategyType.API_GATEWAY_REVERSE_PROXY,
        routing_details="Proxy route",
        data_ownership=DataOwnershipPlan(
            strategy=DataSeparationStrategy.DATABASE_PER_SERVICE,
            source_tables=["users"],
            data_rollback_strategy="Dual write"
        ),
        rollback=RollbackProcedure(
            steps_fr=["Rollback route", "Switch DB back"],
            git_revert_command="git revert HEAD",
            routing_fallback_action="Fallback",
            data_revert_action="Restore",
            estimated_time_to_recover_minutes=5
        )
    )

    review = adversary.review_step_before_implementation(step, discovery)

    assert review.step_is_blocked is True
    assert len(review.blocking_reasons) > 0
    # Objections should contain blocking severity
    severities = [o.severity for o in review.objections]
    assert ObjectionSeverity.BLOCKING in severities
    # Independent tests must be prepared
    assert len(review.independent_test_cases) >= 2
