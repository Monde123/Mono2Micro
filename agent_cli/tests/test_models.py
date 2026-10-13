"""Tests for Mono2Micro Pydantic models."""

import pytest
from datetime import datetime
from mono2micro.models.discovery import (
    VerifiedFact,
    FactEvidenceType,
    ModelAssumption,
    AssumptionCertainty,
    DetectedComponent,
    ComponentType,
    DiscoveryReport,
)
from mono2micro.models.objectives import (
    MigrationGoalType,
    MigrationObjectiveClarification,
    NonMicroserviceAlternative,
)
from mono2micro.models.domains import (
    BoundedContextHypothesis,
    DomainEvidence,
    DomainEvidenceSource,
    CouplingLevel,
)
from mono2micro.models.options import (
    ArchitectureOptionType,
    OptionEvaluation,
    OptionsComparisonMatrix,
)
from mono2micro.models.plan import (
    StranglerStep,
    StranglerPlan,
    RoutingStrategyType,
    DataSeparationStrategy,
    DataOwnershipPlan,
    RollbackProcedure,
)
from mono2micro.models.adversarial import (
    AdversarialReview,
    AdversarialObjection,
    ObjectionSeverity,
    IndependentTestCase,
)
from mono2micro.models.paper_reference import PAPER_PRINCIPLES, PaperPrincipleId
from mono2micro.models.report import FinalReport


def test_paper_principles_integrity():
    assert len(PAPER_PRINCIPLES) == 7
    citation = PAPER_PRINCIPLES[PaperPrincipleId.CLARIFY_OBJECTIVES]
    assert "Section I" in citation.paper_section
    assert "clarification" in citation.principle_name.lower()


def test_verified_fact_vs_model_assumption():
    fact = VerifiedFact(
        fact_id="fact-1",
        evidence_type=FactEvidenceType.FILE_EXISTS,
        file_path="src/routes/billing.ts",
        line_number=12,
        observation="Express router for /api/v1/billing detected"
    )
    assert fact.fact_id == "fact-1"
    assert fact.line_number == 12

    assumption = ModelAssumption(
        assumption_id="asm-1",
        statement="Billing appears to be an isolated bounded context",
        rationale="Only accessed via REST endpoints without direct DB imports elsewhere",
        certainty=AssumptionCertainty.MEDIUM,
        based_on_facts=["fact-1"],
        requires_user_confirmation=True,
    )
    assert assumption.requires_user_confirmation is True
    assert assumption.user_confirmed is None


def test_objectives_clarification():
    obj = MigrationObjectiveClarification(
        primary_goal=MigrationGoalType.DEPLOY_FREQUENCY,
        user_rationale="We want to deploy the catalog independently 5 times a day",
        current_team_size=4,
        can_be_solved_within_monolith=False,
        suggested_alternatives=[
            NonMicroserviceAlternative(
                title="Modular Monolith with Feature Flags",
                description="Trunk-based development with runtime feature flags",
                estimated_complexity="LOW",
                tradeoff_summary="Avoids distributed network failures"
            )
        ]
    )
    assert obj.primary_goal == MigrationGoalType.DEPLOY_FREQUENCY
    assert len(obj.suggested_alternatives) == 1


def test_strangler_step_validation():
    step = StranglerStep(
        step_number=1,
        title="Extract Notification Service",
        description="Extract email and SMS sender to a standalone service",
        target_bounded_context="Notifications",
        files_in_scope=["src/notifications/sender.py", "src/notifications/templates/"],
        routing_strategy=RoutingStrategyType.API_GATEWAY_REVERSE_PROXY,
        routing_details="Route /api/v1/notify to notification microservice",
        data_ownership=DataOwnershipPlan(
            strategy=DataSeparationStrategy.DATABASE_PER_SERVICE,
            source_tables=["notification_logs"],
            target_tables=["notifications"],
            consistency_model="Eventual consistency via queue",
            data_rollback_strategy="Keep old table active during transition"
        ),
        success_criteria=["Zero packet loss", "P95 latency < 50ms"],
        rollback=RollbackProcedure(
            steps_fr=["Switch API Gateway route back to monolith", "Drain queue"],
            git_revert_command="git revert HEAD",
            routing_fallback_action="Direct traffic back to monolith port 8080",
            data_revert_action="Re-enable monolith write path",
            estimated_time_to_recover_minutes=5
        )
    )
    assert step.step_number == 1
    assert step.approved_by_human is False
    assert step.rollback.estimated_time_to_recover_minutes == 5


def test_final_report_markdown_generation():
    discovery = DiscoveryReport(
        target_directory="/workspace/monolith",
        languages_detected=["TypeScript", "SQL"],
        frameworks_detected=["Express", "Prisma"],
        total_files_scanned=142,
        total_loc_scanned=25000,
        verified_facts=[
            VerifiedFact(
                fact_id="F1",
                evidence_type=FactEvidenceType.PACKAGE_DEPENDENCY,
                file_path="package.json",
                observation="Prisma ORM dependency detected"
            )
        ]
    )
    objectives = MigrationObjectiveClarification(
        primary_goal=MigrationGoalType.TARGETED_SCALABILITY,
        user_rationale="Search is taking 80% CPU",
        can_be_solved_within_monolith=True,
    )
    options_matrix = OptionsComparisonMatrix(
        evaluations=[
            OptionEvaluation(
                option_type=ArchitectureOptionType.MODULAR_MONOLITH,
                title="Monolithe Modulaire",
                summary="Isolation du moteur de recherche avec cache Redis dédié",
                complexity_rating="MOYENNE",
                operational_overhead="MINIME",
                suitability_score=0.9,
                is_recommended=True,
                expected_benefits=["Maintien de l'intégrité transactionnelle", "Pas de complexité réseau"],
            )
        ],
        recommended_option=ArchitectureOptionType.MODULAR_MONOLITH,
        synthesis_fr="Le monolithe modulaire résout le problème sans surcoût distribué."
    )
    report = FinalReport(
        report_id="rep-001",
        target_project_path="/workspace/monolith",
        discovery=discovery,
        objectives=objectives,
        options_matrix=options_matrix,
        selected_option=ArchitectureOptionType.MODULAR_MONOLITH,
        executive_summary_fr="Recommandation d'optimisation interne sans découpage microservices.",
        cited_paper_principles=[PAPER_PRINCIPLES[PaperPrincipleId.CLARIFY_OBJECTIVES]],
        next_recommended_actions_fr=["Mettre en cache les requêtes de recherche", "Isoler le module de recherche"],
    )
    md_fr = report.to_markdown(lang="fr")
    assert "# Rapport d'Évolution Architecturale" in md_fr
    assert "Convert Monolithic Application to Microservice Application" in md_fr
    assert "MODULAR_MONOLITH" in md_fr
    assert "Prisma ORM dependency detected" in md_fr

    md_en = report.to_markdown(lang="en")
    assert "# Architectural Evolution Report" in md_en
    assert "Convert Monolithic Application to Microservice Application" in md_en
    assert "Executive Summary" in md_en
    assert "Target Project" in md_en
    assert "MODULAR_MONOLITH" in md_en
    assert "Prisma ORM dependency detected" in md_en
