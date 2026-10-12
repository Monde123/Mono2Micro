"""Master Orchestrator using LangChain architecture.

Orchestrates the 10-step migration lifecycle:
1. Read-only discovery
2. Objectives clarification
3. Domain & dependency analysis
4. Architecture options comparison
5. Phased Strangler Fig planning
6. Adversarial challenge & independent tests
7. Human approval gate
8. Controlled implementation
9. Verification & Quality Gate
10. Comprehensive reporting

Supports both online LLM providers and local heuristic fallback.
"""

import os
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from mono2micro.models.discovery import DiscoveryReport
from mono2micro.models.objectives import MigrationObjectiveClarification, MigrationGoalType
from mono2micro.models.domains import BoundedContextHypothesis
from mono2micro.models.options import OptionsComparisonMatrix, ArchitectureOptionType
from mono2micro.models.plan import StranglerPlan, StranglerStep
from mono2micro.models.adversarial import AdversarialReview
from mono2micro.models.quality_gate import QualityGateResult, QualityGateCriterion
from mono2micro.models.report import FinalReport
from mono2micro.models.paper_reference import PAPER_PRINCIPLES

from mono2micro.agents.repo_analyzer import RepoAnalyzerAgent
from mono2micro.agents.domain_analyst import DomainAnalystAgent
from mono2micro.agents.migration_architect import MigrationArchitectAgent
from mono2micro.agents.test_adversary import TestAdversaryAgent
from mono2micro.agents.implementer import ImplementerAgent
from mono2micro.agents.verifier import VerifierAgent
from mono2micro.core.permissions import PermissionEngine


class MigrationOrchestrator:
    """Master workflow coordinator enforcing state transitions and permissions."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self.permissions = PermissionEngine(target_directory)
        
        # Instantiate agents
        self.repo_analyzer = RepoAnalyzerAgent(target_directory)
        self.domain_analyst = DomainAnalystAgent(target_directory)
        self.migration_architect = MigrationArchitectAgent()
        self.test_adversary = TestAdversaryAgent()
        self.implementer = ImplementerAgent(target_directory, self.permissions)
        self.verifier = VerifierAgent(target_directory)

        # Cached state
        self.discovery_report: Optional[DiscoveryReport] = None
        self.objectives: Optional[MigrationObjectiveClarification] = None
        self.candidate_domains: List[BoundedContextHypothesis] = []
        self.options_matrix: Optional[OptionsComparisonMatrix] = None
        self.strangler_plan: Optional[StranglerPlan] = None
        self.adversarial_reviews: Dict[int, AdversarialReview] = {}
        self.quality_gate_results: Dict[int, QualityGateResult] = {}

    def step_1_discover(self) -> DiscoveryReport:
        """Step 1: Read-only static discovery without code execution."""
        self.discovery_report = self.repo_analyzer.analyze()
        return self.discovery_report

    def step_2_clarify_objectives(
        self,
        primary_goal: MigrationGoalType,
        user_rationale: str,
        team_size: int = 2,
        pain_points: Optional[List[str]] = None
    ) -> MigrationObjectiveClarification:
        """Step 2: Clarify motivation and verify if microservices are genuinely required."""
        pain_points = pain_points or []
        
        # Check if objective could be resolved within monolith
        can_be_solved_internally = primary_goal in (
            MigrationGoalType.CODEBASE_MODULARITY,
            MigrationGoalType.INFRASTRUCTURE_COST
        ) or (team_size <= 2 and primary_goal != MigrationGoalType.TECH_DIVERSITY)

        self.objectives = MigrationObjectiveClarification(
            primary_goal=primary_goal,
            user_rationale=user_rationale,
            current_team_size=team_size,
            pain_points=pain_points,
            can_be_solved_within_monolith=can_be_solved_internally,
            monolith_solution_notes=(
                "Une architecture de type Monolithe Modulaire (Modular Monolith) permet d'isoler les contextes "
                "sans introduire de complexité réseau distribuée ni de cohérence éventuelle."
                if can_be_solved_internally else None
            )
        )
        return self.objectives

    def step_3_analyze_domains(self) -> List[BoundedContextHypothesis]:
        """Step 3: Infer bounded contexts as hypotheses grounded in code evidence."""
        if not self.discovery_report:
            self.step_1_discover()

        self.candidate_domains = self.domain_analyst.analyze_domains(self.discovery_report)
        return self.candidate_domains

    def step_4_compare_options(self) -> OptionsComparisonMatrix:
        """Step 4: Formulate and compare the 4 architectural alternatives."""
        if not self.discovery_report:
            self.step_1_discover()
        if not self.objectives:
            self.step_2_clarify_objectives(
                primary_goal=MigrationGoalType.CODEBASE_MODULARITY,
                user_rationale="Amélioration de la maintenabilité et de l'architecture"
            )
        if not self.candidate_domains:
            self.step_3_analyze_domains()

        self.options_matrix = self.migration_architect.compare_options(
            self.discovery_report,
            self.objectives,
            self.candidate_domains
        )
        return self.options_matrix

    def step_5_plan_migration(self, selected_option: Optional[ArchitectureOptionType] = None) -> StranglerPlan:
        """Step 5: Generate progressive, low-coupling-first Strangler roadmap."""
        if not self.options_matrix:
            self.step_4_compare_options()

        option = selected_option or self.options_matrix.recommended_option
        self.strangler_plan = self.migration_architect.build_strangler_plan(
            self.candidate_domains,
            option
        )
        return self.strangler_plan

    def step_6_adversarial_review(self, step_number: int) -> AdversarialReview:
        """Step 6: Devil's advocate evaluation and preparation of independent test cases."""
        if not self.strangler_plan:
            self.step_5_plan_migration()

        target_step = next((s for s in self.strangler_plan.steps if s.step_number == step_number), None)
        if not target_step:
            raise ValueError(f"Étape {step_number} introuvable dans le plan de migration.")

        review = self.test_adversary.review_step_before_implementation(target_step, self.discovery_report)
        self.adversarial_reviews[step_number] = review
        return review

    def step_7_request_human_approval(
        self,
        step_number: int,
        user_input_confirmation: str
    ) -> str:
        """Step 7: Enforce explicit approval gate with token."""
        if not self.strangler_plan:
            raise ValueError("Aucun plan n'a été préparé.")

        step = next((s for s in self.strangler_plan.steps if s.step_number == step_number), None)
        if not step:
            raise ValueError(f"Étape {step_number} non trouvée.")

        # Check if blocked by adversary
        adv_review = self.adversarial_reviews.get(step_number)
        if adv_review and adv_review.step_is_blocked:
            raise PermissionError(
                f"BLOCAGE CONTRADICTEUR: L'étape {step_number} est bloquée par l'avocat du diable. "
                f"Raisons: {', '.join(adv_review.blocking_reasons)}"
            )

        record = self.permissions.request_approval_for_step(
            step_number=step_number,
            title=step.title,
            files_allowed=step.files_in_scope,
            is_destructive=step.is_destructive,
            is_data_migration=step.is_data_migration,
            user_confirmation_input=user_input_confirmation
        )
        step.approval_token = record.token
        return record.token

    def step_8_apply_step(
        self,
        step_number: int,
        modifications: Dict[str, str]
    ) -> Tuple[bool, str, List[str]]:
        """Step 8: Apply single approved step on isolated git branch."""
        if not self.strangler_plan:
            raise ValueError("Aucun plan disponible.")
        step = next((s for s in self.strangler_plan.steps if s.step_number == step_number), None)
        if not step:
            raise ValueError(f"Étape {step_number} inexistante.")

        # Prepare isolated branch
        self.implementer.prepare_isolation_branch(step)
        
        # Apply changes
        return self.implementer.apply_file_changes(step, modifications)

    def step_9_verify_quality_gate(
        self,
        step_number: int,
        authorized_commands: Optional[List[Tuple[str, str]]] = None
    ) -> QualityGateResult:
        """Step 9: Run authorized tests and enforce non-negotiable Quality Gate."""
        if not self.strangler_plan:
            raise ValueError("Aucun plan disponible.")
        step = next((s for s in self.strangler_plan.steps if s.step_number == step_number), None)
        if not step:
            raise ValueError(f"Étape {step_number} inexistante.")

        criteria: List[QualityGateCriterion] = []

        # 1. Architectural boundary check
        boundary_crit = self.verifier.run_architectural_boundary_check(step)
        criteria.append(boundary_crit)

        # 2. Run authorized user commands
        authorized_commands = authorized_commands or []
        for cmd, title in authorized_commands:
            crit = self.verifier.run_user_authorized_test_command(cmd, title)
            criteria.append(crit)

        qg_result = self.verifier.evaluate_quality_gate(criteria, step_number)
        self.quality_gate_results[step_number] = qg_result
        return qg_result

    def step_10_generate_report(self) -> FinalReport:
        """Step 10: Compile end-to-end report with paper citations and verifiable results."""
        if not self.discovery_report:
            self.step_1_discover()
        if not self.objectives:
            self.step_2_clarify_objectives(
                primary_goal=MigrationGoalType.CODEBASE_MODULARITY,
                user_rationale="Audit initial"
            )
        if not self.options_matrix:
            self.step_4_compare_options()

        return FinalReport(
            report_id=f"REP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            target_project_path=self.target_directory,
            discovery=self.discovery_report,
            objectives=self.objectives,
            candidate_domains=self.candidate_domains,
            options_matrix=self.options_matrix,
            selected_option=self.options_matrix.recommended_option,
            strangler_plan=self.strangler_plan,
            adversarial_review=list(self.adversarial_reviews.values())[0] if self.adversarial_reviews else None,
            quality_gate_result=list(self.quality_gate_results.values())[0] if self.quality_gate_results else None,
            cited_paper_principles=list(PAPER_PRINCIPLES.values()),
            executive_summary_fr=(
                f"Audit architectural basé sur le papier de Hatem Hammad et al. (2023). "
                f"Option recommandée : {self.options_matrix.recommended_option.value}. "
                f"{self.options_matrix.synthesis_fr}"
            ),
            next_recommended_actions_fr=[
                "Confirmer ou ajuster avec les développeurs les frontières des domaines candidats (hypotheses).",
                "Mettre en place ou consolider la suite de tests de non-régression avant toute séparation de données.",
                "Examiner les objections soulevées par le rôle contradicteur.",
                "Valider explicitement la première étape pilote de refactoring si la migration est confirmée."
            ],
            open_risks_fr=[
                "Risque d'échec si la séparation de base de données est réalisée sans synchronisation miroir (dual writes).",
                "Risque de surcoût d'exploitation si les microservices sont adoptés avec une équipe réduite."
            ]
        )
