"""Rich terminal formatters for trees, tables, panels, and paper citations.

Provides clear visual hierarchy and strictly separates verifiable facts from model hypotheses.
"""

from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich import box

from mono2micro.models.discovery import DiscoveryReport
from mono2micro.models.domains import BoundedContextHypothesis
from mono2micro.models.options import OptionsComparisonMatrix
from mono2micro.models.adversarial import AdversarialReview, ObjectionSeverity
from mono2micro.models.quality_gate import QualityGateResult, CriterionStatus
from mono2micro.models.plan import StranglerPlan
from mono2micro.core.security import SecretMasker

console = Console()


class ConsoleFormatter:
    """Renders structured domain data as rich CLI widgets."""

    @staticmethod
    def print_banner():
        """Display tool header grounded in Hammad et al. (2023)."""
        banner_text = Text()
        banner_text.append("MONO2MICRO AGENT — Modernisation Raisonnée de Monolithes\n", style="bold cyan")
        banner_text.append("Basé sur les principes de recherche de : ", style="dim")
        banner_text.append("Hatem Hammad, Thaer Sahmoud & Abed Al Rahman Abu Ghazala (2023)\n", style="bold white")
        banner_text.append("Réf. alphaXiv : ", style="dim")
        banner_text.append("https://www.alphaxiv.org/abs/2306.08851", style="underline blue")

        console.print(Panel(
            banner_text,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

    @staticmethod
    def display_discovery_report(report: DiscoveryReport):
        """Render discovery statistics, components tree, and verified facts."""
        # 1. Overview summary table
        summary_table = Table(title="[bold green]1. Inventaire Factuel du Dépôt (Lecture Seule)[/]", box=box.ROUNDED)
        summary_table.add_column("Indicateur", style="bold white")
        summary_table.add_column("Valeur Observée", style="cyan")

        summary_table.add_row("Répertoire Scanné", report.target_directory)
        summary_table.add_row("Fichiers Totaux Analysés", str(report.total_files_scanned))
        summary_table.add_row("Volume de Code Estimé", f"{report.total_loc_scanned:,} lignes")
        summary_table.add_row("Langages Détectés", ", ".join(report.languages_detected) or "Aucun")
        summary_table.add_row("Frameworks Identifiés", ", ".join(report.frameworks_detected) or "Aucun")
        summary_table.add_row("Socle de Persistance (BD)", report.database_coupling.db_type)
        summary_table.add_row("Tables/Modèles Détectés", str(len(report.database_coupling.detected_models_or_tables)))
        summary_table.add_row("Frameworks de Tests", ", ".join(report.test_frameworks_detected) or "[red]Aucun détecté[/]")

        console.print(summary_table)
        console.print()

        # 2. Components Tree
        tree = Tree(f"[bold cyan]📁 Structure & Composants Découverts ({Path(report.target_directory).name})[/]")
        
        routers_branch = tree.add("[bold yellow]🌐 Points d'Entrée & Routeurs HTTP[/]")
        db_branch = tree.add("[bold magenta]🗄️ Persistance & Modèles de Données[/]")
        test_branch = tree.add("[bold blue]🧪 Suites de Tests & CI/CD[/]")

        for comp in report.components:
            if comp.component_type.value == "API_ROUTER":
                routers_branch.add(f"[white]{comp.name}[/] [dim]({comp.relative_path} — {comp.language})[/]")
            elif comp.component_type.value == "DATABASE_ORM":
                db_branch.add(f"[white]{comp.name}[/] [dim]({comp.relative_path})[/]")
            elif comp.component_type.value == "TEST_SUITE":
                test_branch.add(f"[white]{comp.name}[/] [dim]({comp.relative_path})[/]")

        if not routers_branch.children:
            routers_branch.add("[dim italic]Aucun routeur explicite identifié[/]")
        if not db_branch.children:
            db_branch.add("[dim italic]Aucun ORM détecté[/]")
        if not test_branch.children:
            test_branch.add("[red italic]Aucune suite de test identifiée[/]")

        console.print(tree)
        console.print()

        # 3. Verified Facts Table
        facts_table = Table(title="[bold green]2. Faits Empiriques Vérifiés (100% Vérifiables)[/]", box=box.ROUNDED)
        facts_table.add_column("ID", style="dim", width=14)
        facts_table.add_column("Type de Preuve", style="bold yellow")
        facts_table.add_column("Fichier Source", style="cyan")
        facts_table.add_column("Observation Empirique", style="white")

        for fact in report.verified_facts[:8]:
            facts_table.add_row(
                fact.fact_id,
                fact.evidence_type.value,
                fact.file_path,
                SecretMasker.mask_text(fact.observation)
            )

        if len(report.verified_facts) > 8:
            facts_table.add_row("...", "...", "...", f"[dim]+ {len(report.verified_facts) - 8} autres faits vérifiés[/]")

        console.print(facts_table)
        console.print()

        # 4. Model Assumptions Table
        if report.model_assumptions:
            assumptions_table = Table(
                title="[bold yellow]3. Hypothèses Formées par le Modèle (À Confirmer par le Développeur)[/]",
                box=box.ROUNDED
            )
            assumptions_table.add_column("ID", style="dim", width=18)
            assumptions_table.add_column("Hypothèse Déduite", style="bold white")
            assumptions_table.add_column("Niveau de Certitude", style="magenta")
            assumptions_table.add_column("Statut Validation", style="yellow")

            for asm in report.model_assumptions:
                status_str = "[yellow]⚠️ À valider[/]" if asm.user_confirmed is None else ("[green]✓ Validé[/]" if asm.user_confirmed else "[red]✗ Rejeté[/]")
                assumptions_table.add_row(
                    asm.assumption_id,
                    asm.statement,
                    asm.certainty.value,
                    status_str
                )
            console.print(assumptions_table)
            console.print()

    @staticmethod
    def display_domains(domains: list[BoundedContextHypothesis]):
        """Render detected domains, coupling metrics and low-coupling priority."""
        table = Table(
            title="[bold green]Analyse des Domaines Métier & Contextes Délimités (Principe 2 & 4)[/]",
            box=box.ROUNDED
        )
        table.add_column("Priorité", style="bold cyan", width=10)
        table.add_column("Contexte Délimité (Candidat)", style="bold white")
        table.add_column("Couplage Estimé", style="magenta")
        table.add_column("Score d'Extraction", style="green")
        table.add_column("Entités / Tables Associées", style="dim")
        table.add_column("Recommandation d'Étape", style="white")

        for idx, d in enumerate(domains, 1):
            prio_badge = f"#{idx} {'[bold green](1er pas)[/]' if idx == 1 else ''}"
            coupling_color = "green" if d.coupling_level.value == "LOOSE" else ("yellow" if d.coupling_level.value == "MODERATE" else "red")
            tables_str = ", ".join(d.shared_database_tables[:3]) if d.shared_database_tables else "Isolé"
            recom = "Candidat prioritaire pilote" if idx == 1 else ("Extraction ultérieure" if d.coupling_level.value != "TIGHT" else "Fort couplage, isoler d'abord")

            table.add_row(
                prio_badge,
                d.name,
                f"[{coupling_color}]{d.coupling_level.value}[/]",
                f"{d.extraction_feasibility_score:.2f}",
                tables_str,
                recom
            )

        console.print(table)
        console.print()

    @staticmethod
    def display_options_matrix(matrix: OptionsComparisonMatrix):
        """Render comparison of the 4 architectural options."""
        table = Table(
            title="[bold green]Comparatif des 4 Trajectoires Architecturales[/]",
            box=box.ROUNDED
        )
        table.add_column("Option", style="bold white", width=26)
        table.add_column("Complexité", style="yellow", width=12)
        table.add_column("Surcoût Opér.", style="magenta", width=14)
        table.add_column("Principaux Bénéfices", style="cyan")
        table.add_column("Risques Majeurs", style="red")
        table.add_column("Recommandée ?", style="bold green", width=15)

        for opt in matrix.evaluations:
            rec_str = "[bold green]✓ OUI[/]" if opt.is_recommended else "[dim]Non[/]"
            table.add_row(
                opt.title,
                opt.complexity_rating,
                opt.operational_overhead,
                "\n".join(f"• {b}" for b in opt.expected_benefits[:2]),
                "\n".join(f"• {r}" for r in opt.operational_risks[:2]),
                rec_str
            )

        console.print(table)
        console.print()

        console.print(Panel(
            f"[bold cyan]Synthèse de l'Architecte :[/]\n{matrix.synthesis_fr}",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print()

    @staticmethod
    def display_adversarial_review(review: AdversarialReview):
        """Render devil's advocate review, objections, and test scenarios."""
        title_style = "bold red" if review.step_is_blocked else "bold green"
        status_label = "[bold red]⛔ ÉTAPE BLOQUÉE PAR L'AVOCAT DU DIABLE[/]" if review.step_is_blocked else "[bold green]✓ ÉTAPE VALIDÉE AVEC RÉSERVES[/]"

        console.print(Panel(
            f"{status_label}\n[dim]{review.recommendation_summary_fr}[/]",
            border_style="red" if review.step_is_blocked else "green",
            box=box.ROUNDED
        ))
        console.print()

        # Objections table
        if review.objections:
            obj_table = Table(title="[bold red]Objections & Risques Méthodologiques Soulevés[/]", box=box.ROUNDED)
            obj_table.add_column("Sévérité", width=12)
            obj_table.add_column("Sujet", style="bold white")
            obj_table.add_column("Contre-Argumentation / Preuve", style="yellow")
            obj_table.add_column("Action Corrective Requise", style="cyan")

            for obj in review.objections:
                sev_color = "red" if obj.severity == ObjectionSeverity.BLOCKING else "yellow"
                obj_table.add_row(
                    f"[{sev_color} bold]{obj.severity.value}[/]",
                    obj.topic,
                    f"{obj.argument_fr}\n[dim]Preuve: {obj.evidence_or_counterexample}[/]",
                    obj.suggested_remedy
                )
            console.print(obj_table)
            console.print()

        # Independent tests table
        if review.independent_test_cases:
            tests_table = Table(title="[bold blue]Scénarios de Tests Indépendants Conçus Avant Implémentation[/]", box=box.ROUNDED)
            tests_table.add_column("ID Test", style="dim", width=22)
            tests_table.add_column("Intention du Test", style="bold white")
            tests_table.add_column("Comportement Attendu", style="green")
            tests_table.add_column("Symptôme d'Échec", style="red")

            for tc in review.independent_test_cases:
                tests_table.add_row(
                    tc.case_id,
                    tc.title,
                    tc.expected_outcome,
                    tc.failure_symptom
                )
            console.print(tests_table)
            console.print()

    @staticmethod
    def display_quality_gate(qg: QualityGateResult):
        """Render Quality Gate results with zero-averaging enforcement."""
        status_color = "green" if qg.overall_passed else "red"
        status_text = "[bold green]✓ QUALITY GATE VALIDÉ — PRÊT POUR LIVRAISON[/]" if qg.overall_passed else "[bold red]⛔ QUALITY GATE EN ÉCHEC — LIVRAISON BLOQUÉE[/]"

        console.print(Panel(
            f"{status_text}\n"
            f"[dim]Critères vérifiés: {qg.passed_mandatory_count}/{qg.total_criteria_count} | "
            f"Échecs critiques: {qg.critical_failures_count} | "
            f"Non vérifiés: {qg.skipped_mandatory_count}[/]\n"
            f"[italic]Règle stricte: Aucun échec critique ne peut être moyenné ou compensé.[/]",
            border_style=status_color,
            box=box.ROUNDED
        ))
        console.print()

        table = Table(title="[bold cyan]Détail des Critères de Contrôle[/]", box=box.ROUNDED)
        table.add_column("Statut", width=12)
        table.add_column("Obligatoire", width=12)
        table.add_column("Catégorie", style="dim")
        table.add_column("Contrôle Réalisé", style="bold white")
        table.add_column("Preuve / Motif d'Échec", style="white")

        for c in qg.criteria:
            if c.status == CriterionStatus.PASSED:
                st = "[green]✓ PASSED[/]"
            elif c.status == CriterionStatus.FAILED:
                st = "[red]✗ FAILED[/]"
            else:
                st = "[yellow]⚠️ SKIPPED[/]"

            mand = "[bold red]OUI[/]" if c.is_mandatory else "[dim]Non[/]"
            detail = c.evidence or c.failure_details or "Pas de détails"

            table.add_row(st, mand, c.category.value, c.title, detail)

        console.print(table)
        console.print()


from pathlib import Path
