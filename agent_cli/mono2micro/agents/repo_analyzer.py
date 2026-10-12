"""Repo Analyzer Agent (Role 1).

Gathers empirical, verifiable observations on the repository without executing code.
Formulates model assumptions explicitly flagged as requiring human validation.
"""

from typing import List, Optional
from mono2micro.tools.repo_scanner import SafeRepoScanner
from mono2micro.models.discovery import (
    DiscoveryReport,
    ModelAssumption,
    AssumptionCertainty,
    ComponentType,
)


class RepoAnalyzerAgent:
    """Agent in charge of passive codebase discovery and facts verification."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self.scanner = SafeRepoScanner(target_directory)

    def analyze(self) -> DiscoveryReport:
        """Scan repository and enrich with conservative model assumptions."""
        report = self.scanner.scan()

        # Generate initial conservative assumptions based on verified facts
        assumptions: List[ModelAssumption] = []
        fact_ids = [f.fact_id for f in report.verified_facts]

        # 1. Monolith architecture assumption
        router_components = [c for c in report.components if c.component_type == ComponentType.API_ROUTER]
        if len(router_components) >= 2 or report.total_files_scanned > 20:
            assumptions.append(ModelAssumption(
                assumption_id="ASM-ARCH-MONOLITH",
                statement="Le projet présente la structure d'une application monolithique centralisée.",
                rationale=f"Présence de {len(router_components)} routeurs et {len(report.database_coupling.detected_models_or_tables)} modèles de données partageant un même dépôt.",
                certainty=AssumptionCertainty.HIGH,
                based_on_facts=fact_ids[:3],
                requires_user_confirmation=True
            ))

        # 2. Database coupling assumption
        if report.database_coupling.detected_models_or_tables:
            assumptions.append(ModelAssumption(
                assumption_id="ASM-DATA-COUPLED",
                statement="Une base de données relationnelle partagée forme le socle de persistance.",
                rationale=f"{len(report.database_coupling.detected_models_or_tables)} tables/modèles identifiés ({', '.join(report.database_coupling.detected_models_or_tables[:4])}).",
                certainty=AssumptionCertainty.HIGH,
                based_on_facts=[f for f in fact_ids if "DB" in f or "SQL" in f][:3],
                requires_user_confirmation=True
            ))

        # 3. Test suite coverage assumption
        if not report.test_frameworks_detected:
            assumptions.append(ModelAssumption(
                assumption_id="ASM-TEST-GAP",
                statement="Couverture de tests automatisés potentiellement faible ou non standardisée.",
                rationale="Aucun framework de test majeur (Jest, Pytest, Mocha) détecté dans les manifestes racine.",
                certainty=AssumptionCertainty.MEDIUM,
                based_on_facts=[],
                requires_user_confirmation=True
            ))

        report.model_assumptions = assumptions
        return report
