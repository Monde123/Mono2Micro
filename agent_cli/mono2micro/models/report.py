"""Comprehensive migration and audit report models.

Enforces Workflow Step 10:
Generate readable and verifiable reports combining factual findings,
model hypotheses, recommended paths, devil's advocate reviews, and citations from Hammad et al. (2023).
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from mono2micro.models.discovery import DiscoveryReport
from mono2micro.models.objectives import MigrationObjectiveClarification
from mono2micro.models.domains import BoundedContextHypothesis
from mono2micro.models.options import OptionsComparisonMatrix, ArchitectureOptionType
from mono2micro.models.plan import StranglerPlan
from mono2micro.models.adversarial import AdversarialReview
from mono2micro.models.quality_gate import QualityGateResult
from mono2micro.models.paper_reference import PaperPrincipleCitation


class FinalReport(BaseModel):
    """Full end-to-end report document."""
    report_id: str
    target_project_path: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Paper reference metadata
    paper_title: str = "Convert Monolithic Application to Microservice Application"
    paper_authors: str = "Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala (2023)"
    paper_url: str = "https://www.alphaxiv.org/abs/2306.08851"
    
    # Analysis components
    discovery: DiscoveryReport
    objectives: MigrationObjectiveClarification
    candidate_domains: List[BoundedContextHypothesis] = Field(default_factory=list)
    options_matrix: OptionsComparisonMatrix
    selected_option: ArchitectureOptionType
    strangler_plan: Optional[StranglerPlan] = None
    adversarial_review: Optional[AdversarialReview] = None
    quality_gate_result: Optional[QualityGateResult] = None
    
    # Principles applied
    cited_paper_principles: List[PaperPrincipleCitation] = Field(default_factory=list)
    
    # Human validation summary
    human_approved: bool = False
    executive_summary_fr: str
    next_recommended_actions_fr: List[str] = Field(default_factory=list)
    open_risks_fr: List[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Render report as human-readable Markdown."""
        lines = [
            f"# Rapport d'Évolution Architecturale — Mono2Micro",
            f"**Projet cible** : `{self.target_project_path}`  ",
            f"**Généré le** : {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Référence théorique** : [{self.paper_title}]({self.paper_url}) ({self.paper_authors})  ",
            "",
            "## 1. Synthèse Exécutive",
            self.executive_summary_fr,
            "",
            f"**Recommandation retenue** : `{self.selected_option.value}`",
            "",
            "## 2. Clarification des Objectifs Métier",
            f"- **Objectif principal** : {self.objectives.primary_goal.value}",
            f"- **Motivation utilisateur** : {self.objectives.user_rationale}",
            f"- **Résoluble au sein du monolithe ?** : {'OUI' if self.objectives.can_be_solved_within_monolith else 'NON'}",
            "",
            "## 3. Découverte Empirique du Dépôt",
            f"- **Fichiers scannés** : {self.discovery.total_files_scanned}",
            f"- **Langages détectés** : {', '.join(self.discovery.languages_detected) or 'Aucun'}",
            f"- **Frameworks détectés** : {', '.join(self.discovery.frameworks_detected) or 'Aucun'}",
            f"- **Faits vérifiés** : {len(self.discovery.verified_facts)}",
            f"- **Hypothèses déduites (à confirmer)** : {len(self.discovery.model_assumptions)}",
            "",
            "### Faits vérifiés notables :",
        ]
        for fact in self.discovery.verified_facts[:5]:
            lines.append(f"- `[{fact.evidence_type.value}]` {fact.observation} (`{fact.file_path}`)")
        
        lines.extend([
            "",
            "## 4. Analyse des Domaines Métier & Couplages",
        ])
        for domain in self.candidate_domains:
            confirmed_str = "Confirmé" if domain.user_confirmed else "Hypothèse non confirmée"
            lines.append(f"### Domaine : {domain.name} ({confirmed_str})")
            lines.append(f"- **Rôle** : {domain.suggested_responsibility}")
            lines.append(f"- **Couplage estimé** : `{domain.coupling_level.value}` (Score faisabilité: {domain.extraction_feasibility_score:.2f})")
            if domain.shared_database_tables:
                lines.append(f"- **Tables BD partagées** : {', '.join(domain.shared_database_tables)}")

        lines.extend([
            "",
            "## 5. Comparaison des 4 Options Architecturales",
        ])
        for opt in self.options_matrix.evaluations:
            rec_tag = " [RECOMMANDÉE]" if opt.is_recommended else ""
            lines.append(f"### {opt.title}{rec_tag}")
            lines.append(f"{opt.summary}")
            lines.append(f"- **Complexité** : {opt.complexity_rating} | **Surcoût opérationnel** : {opt.operational_overhead}")
            lines.append(f"- **Bénéfices** : {', '.join(opt.expected_benefits)}")
            lines.append(f"- **Risques** : {', '.join(opt.operational_risks)}")

        if self.adversarial_review:
            lines.extend([
                "",
                "## 6. Revue Contradictoire de l'Avocat du Diable",
                f"**Statut étape** : {'BLOQUÉE' if self.adversarial_review.step_is_blocked else 'AUTORISÉE SOUS CONDITIONS'}",
                f"**Avis** : {self.adversarial_review.recommendation_summary_fr}",
                "",
                "### Objections et Risques Cachés :",
            ])
            for obj in self.adversarial_review.objections:
                lines.append(f"- `[{obj.severity.value}]` **{obj.topic}** : {obj.argument_fr}")
                lines.append(f"  *Contre-exemple / preuve* : {obj.evidence_or_counterexample}")

        if self.quality_gate_result:
            lines.extend([
                "",
                "## 7. Quality Gate et Vérifications",
                f"**Résultat global** : {'SUCCÈS' if self.quality_gate_result.overall_passed else 'ÉCHEC / BLOQUÉ'}",
                f"- Critères totaux : {self.quality_gate_result.total_criteria_count}",
                f"- Échecs critiques : {self.quality_gate_result.critical_failures_count}",
                f"- Non vérifiés : {self.quality_gate_result.skipped_mandatory_count}",
            ])
            if self.quality_gate_result.blocker_summary_fr:
                lines.append(f"**Blocages** : {self.quality_gate_result.blocker_summary_fr}")

        lines.extend([
            "",
            "## 8. Principes du Papier Appliqués (Hammad et al., 2023)",
        ])
        for citation in self.cited_paper_principles:
            lines.append(f"- **{citation.principle_name}** ({citation.paper_section}) : {citation.summary_fr}")

        lines.extend([
            "",
            "## 9. Risques Ouverts et Prochaines Actions",
        ])
        for action in self.next_recommended_actions_fr:
            lines.append(f"1. {action}")

        return "\n".join(lines)
