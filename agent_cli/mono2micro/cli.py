"""Official Command Line Interface (CLI) for Mono2Micro Agent.

Commands:
- agent analyze   : Read-only static discovery, inventory, facts & assumptions.
- agent plan      : Clarify objectives, DDD domain analysis & 4 options comparison.
- agent test-plan : Devil's advocate critique, hidden couplings & independent tests.
- agent apply     : Controlled step application on isolated git branch with rollback.
- agent verify    : Architectural boundary check, authorized tests & strict Quality Gate.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from mono2micro.core.orchestrator import MigrationOrchestrator
from mono2micro.config import ProjectStateStore, UserSpecifications
from mono2micro.ui.rich_formatters import ConsoleFormatter
from mono2micro.models.objectives import MigrationGoalType
from mono2micro.models.options import ArchitectureOptionType
from mono2micro.core.security import SecretMasker

app = typer.Typer(
    name="agent",
    help="Agent IA local en ligne de commande pour la modernisation de monolithes logiciels (Hammad et al., 2023).",
    no_args_is_help=True
)

console = Console()


def get_orchestrator(target_path: Optional[str] = None) -> MigrationOrchestrator:
    """Resolve workspace directory and initialize orchestrator."""
    path = target_path or os.getcwd()
    return MigrationOrchestrator(path)


@app.command(name="analyze")
def cmd_analyze(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du répertoire du projet à analyser."),
    offline: bool = typer.Option(True, "--offline", help="Mode d'analyse statique locale sans appel externe."),
):
    """Analyse en lecture seule du dépôt : inventaire des composants, faits vérifiés et hypothèses."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    console.print(f"[bold cyan]🔍 Lancement de la découverte passive sur :[/] [white]{resolved_path}[/]\n")

    orchestrator = get_orchestrator(resolved_path)
    report = orchestrator.step_1_discover()

    # Rich formatting
    ConsoleFormatter.display_discovery_report(report)

    # Persist state
    store = ProjectStateStore(resolved_path)
    store.save_json("discovery.json", report.model_dump())
    console.print("[dim green]✓ Découverte sauvegardée dans .mono2micro/discovery.json[/]\n")
    console.print("[bold yellow]Prochaine commande recommandée :[/] [bold white]agent plan[/]")


@app.command(name="plan")
def cmd_plan(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    goal: str = typer.Option("CODEBASE_MODULARITY", "--goal", "-g", help="Objectif : TARGETED_SCALABILITY, TEAM_AUTONOMY, DEPLOY_FREQUENCY, FAULT_ISOLATION, CODEBASE_MODULARITY, TECH_DIVERSITY, INFRASTRUCTURE_COST."),
    team_size: int = typer.Option(2, "--team-size", "-t", help="Nombre de développeurs sur le projet."),
    rationale: str = typer.Option("Modernisation et clarification de l'architecture", "--rationale", "-r", help="Motivation détaillée."),
):
    """Clarification des objectifs, analyse de domaines (DDD) et comparaison des 4 options architecturales."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)

    # 1. Discover if not already cached
    orchestrator.step_1_discover()

    # 2. Clarify objectives
    try:
        goal_enum = MigrationGoalType(goal.upper())
    except ValueError:
        goal_enum = MigrationGoalType.CODEBASE_MODULARITY

    objectives = orchestrator.step_2_clarify_objectives(
        primary_goal=goal_enum,
        user_rationale=rationale,
        team_size=team_size
    )

    console.print(f"[bold green]Objectif métier analysé :[/] [white]{objectives.primary_goal.value}[/]")
    if objectives.can_be_solved_within_monolith:
        console.print("[bold yellow]ℹ️ Avertissement du Papier (Principe 1) :[/] [white]Cet objectif peut être résolu sans microservices (Monolithe Modulaire).[/]\n")

    # 3. Domains
    domains = orchestrator.step_3_analyze_domains()
    ConsoleFormatter.display_domains(domains)

    # 4. Compare 4 options
    matrix = orchestrator.step_4_compare_options()
    ConsoleFormatter.display_options_matrix(matrix)

    # 5. Build Strangler Plan
    plan = orchestrator.step_5_plan_migration()
    console.print(f"[bold cyan]Plan de Migration Élaboré ({plan.target_architecture_summary}) :[/]")
    for s in plan.steps:
        console.print(f"  • [bold white]Étape {s.step_number} : {s.title}[/] [dim]({s.target_bounded_context} — Stratégie: {s.routing_strategy.value})[/]")
        console.print(f"    [dim]Rollback : {s.rollback.git_revert_command}[/]")
    console.print()

    # Persist state
    store = ProjectStateStore(resolved_path)
    store.save_json("objectives.json", objectives.model_dump())
    store.save_json("domains.json", [d.model_dump() for d in domains])
    store.save_json("options_matrix.json", matrix.model_dump())
    store.save_json("strangler_plan.json", plan.model_dump())

    console.print("[dim green]✓ Trajectoire et plan enregistrés dans .mono2micro/strangler_plan.json[/]\n")
    console.print("[bold yellow]Prochaine commande recommandée :[/] [bold white]agent test-plan --step 1[/]")


@app.command(name="test-plan")
def cmd_test_plan(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    step: int = typer.Option(1, "--step", "-s", help="Numéro d'étape à challenger."),
):
    """Intervention de l'avocat du diable : recherche de couplages cachés et tests indépendants."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)

    # Reconstitute state
    orchestrator.step_1_discover()
    orchestrator.step_3_analyze_domains()
    orchestrator.step_4_compare_options()
    orchestrator.step_5_plan_migration()

    console.print(f"[bold red]⚖️ Intervention du Sous-Agent Contradicteur sur l'Étape {step}...[/]\n")
    review = orchestrator.step_6_adversarial_review(step_number=step)

    # Display Rich adversarial review
    ConsoleFormatter.display_adversarial_review(review)

    store = ProjectStateStore(resolved_path)
    store.save_json(f"adversarial_review_step_{step}.json", review.model_dump())

    if review.step_is_blocked:
        console.print("[bold red]⛔ BLOQUÉ : Vous devez résoudre ces objections avant de pouvoir exécuter 'agent apply'.[/]\n")
    else:
        console.print(f"[bold green]✓ Étape autorisée pour approbation.[/] [bold white]Lancez : agent apply --step {step}[/]\n")


@app.command(name="apply")
def cmd_apply(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    step: int = typer.Option(1, "--step", "-s", help="Numéro de l'étape à appliquer."),
    confirm: Optional[str] = typer.Option(None, "--confirm", "-c", help="Jeton ou chaîne de confirmation explicite ('OUI')."),
):
    """Application contrôlée d'une étape validée sur branche Git isolée après approbation."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)

    # Build plan & check adversarial status
    orchestrator.step_1_discover()
    orchestrator.step_3_analyze_domains()
    orchestrator.step_4_compare_options()
    plan = orchestrator.step_5_plan_migration()
    review = orchestrator.step_6_adversarial_review(step_number=step)

    if review.step_is_blocked:
        console.print(f"[bold red]Action Interdite : L'étape {step} est bloquée par l'avocat du diable.[/]")
        for r in review.blocking_reasons:
            console.print(f"  • [red]{r}[/]")
        raise typer.Exit(code=1)

    target_step = next((s for s in plan.steps if s.step_number == step), None)
    if not target_step:
        console.print(f"[red]Étape {step} introuvable.[/]")
        raise typer.Exit(code=1)

    # Request human approval
    console.print(f"[bold yellow]⚠️ DEMANDE D'APPROBATION HUMAINE FORMELLE POUR L'ÉTAPE {step} :[/]")
    console.print(f"[white]Titre :[/] {target_step.title}")
    console.print(f"[white]Périmètre des fichiers :[/] {', '.join(target_step.files_in_scope) or 'Fichiers déclarés du module'}")
    console.print(f"[white]Procédure de Rollback :[/] {target_step.rollback.git_revert_command}\n")

    confirmation = confirm
    if not confirmation:
        confirmation = Prompt.ask("[bold red]Confirmez-vous l'application de cette étape sur branche isolée ? (Tapez 'OUI' pour approuver)[/]")

    try:
        token = orchestrator.step_7_request_human_approval(step, confirmation)
        console.print(f"[bold green]✓ Approbation accordée avec succès (Jeton: {token}).[/]\n")
    except Exception as e:
        console.print(f"[bold red]❌ Échec de permission :[/] {str(e)}")
        raise typer.Exit(code=1)

    # Prepare branch and simulate/apply changes
    success, msg = orchestrator.implementer.prepare_isolation_branch(target_step)
    if success:
        console.print(f"[green]✓ {msg}[/]")
    else:
        console.print(f"[yellow]⚠️ {msg}[/]")

    console.print(f"[bold green]✓ Étape {step} initialisée sur branche dédiée. Fichiers protégés par les frontières du plan.[/]\n")
    console.print("[bold yellow]Prochaine commande requise :[/] [bold white]agent verify --step 1[/]")


@app.command(name="verify")
def cmd_verify(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    step: int = typer.Option(1, "--step", "-s", help="Numéro d'étape à vérifier."),
    test_cmd: Optional[str] = typer.Option(None, "--test-cmd", help="Commande de test autorisée (ex: 'npm test' ou 'pytest')."),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Langue du rapport ('fr' ou 'en'). Par défaut selon configuration."),
):
    """Exécution des contrôles autorisés, étanchéité architecturale et Quality Gate sans moyenne."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)

    orchestrator.step_1_discover()
    orchestrator.step_3_analyze_domains()
    orchestrator.step_4_compare_options()
    orchestrator.step_5_plan_migration()

    # Commands come from the explicit --test-cmd flag (typed by the user) and from
    # the user's configured allow-list (`config --add-test-cmd`). Nothing else runs.
    specs = orchestrator.user_specs
    ordered = ([test_cmd] if test_cmd else []) + list(specs.authorized_test_commands)
    commands = []
    for cmd in dict.fromkeys(ordered):  # de-duplicate, keep order
        commands.append((cmd, f"Suite de test utilisateur autorisée : {cmd}"))
    if not commands:
        # Default internal syntax/check command
        commands.append(("git status", "Contrôle de propreté de l'arbre Git"))

    console.print(f"[bold cyan]🔍 Exécution des contrôles Quality Gate pour l'étape {step}...[/]\n")
    qg_result = orchestrator.step_9_verify_quality_gate(step_number=step, authorized_commands=commands)

    # Display Rich Quality Gate
    ConsoleFormatter.display_quality_gate(qg_result)

    # Generate full report
    report = orchestrator.step_10_generate_report()
    store = ProjectStateStore(resolved_path)
    specs = store.get_user_specifications()
    chosen_lang = (lang or specs.language or "fr").lower()

    # Save primary report in requested language, plus both explicit language files
    store.save_json("report.json", report.model_dump())
    store.save_text("report.md", report.to_markdown(lang=chosen_lang))
    store.save_text("report_fr.md", report.to_markdown(lang="fr"))
    store.save_text("report_en.md", report.to_markdown(lang="en"))

    lang_label = "Français" if chosen_lang == "fr" else "English"
    console.print(f"[dim green]✓ Rapports complets exportés (Langue active: [bold white]{lang_label}[/]) :[/]")
    console.print(f"  • [white].mono2micro/report.md[/] [dim](Actif: {lang_label})[/]")
    console.print("  • [white].mono2micro/report_fr.md[/] [dim](Version française)[/]")
    console.print("  • [white].mono2micro/report_en.md[/] [dim](English version)[/]")
    console.print("  • [white].mono2micro/report.json[/] [dim](Données brutes bilingues structurées)[/]\n")

    if qg_result.overall_passed:
        console.print("[bold green]🎉 Succès : Le Quality Gate est validé. L'étape peut être fusionnée après relecture de PR.[/]")
    else:
        console.print("[bold red]⛔ Livraison bloquée : Un ou plusieurs critères obligatoires sont en échec ou non vérifiés.[/]")


@app.command(name="config")
def cmd_config(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    set_domain: Optional[str] = typer.Option(None, "--set-domain", help="Définir un domaine personnalisé : 'Nom=chemin1,chemin2'"),
    forbid: Optional[str] = typer.Option(None, "--forbid", help="Interdire l'extraction d'un module ou d'une table."),
    team_size: Optional[int] = typer.Option(None, "--team-size", help="Définir la taille persistante de l'équipe."),
    prefer: Optional[str] = typer.Option(None, "--prefer", help="Option préférée : MODULAR_MONOLITH, STRANGLER_MICROSERVICES, KEEP_MONOLITH."),
    add_test_cmd: Optional[str] = typer.Option(None, "--add-test-cmd", help="Ajouter une commande de test autorisée pour le Quality Gate."),
    privacy: Optional[str] = typer.Option(None, "--privacy", help="Niveau de confidentialité : FULL_CODE_REDACTED, METADATA_ONLY, ANONYMIZED_SYMBOLS."),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Définir la langue par défaut des rapports et du projet ('fr' ou 'en')."),
    init: bool = typer.Option(False, "--init", help="Initialiser le fichier de spécifications .mono2micro/user_specifications.json."),
):
    """Gérer la persistance des spécificités utilisateur, domaines métiers et règles d'équipe."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    store = ProjectStateStore(resolved_path)
    specs = store.get_user_specifications()

    updated = False

    if set_domain:
        if "=" in set_domain:
            d_name, d_paths = set_domain.split("=", 1)
            patterns = [p.strip() for p in d_paths.split(",") if p.strip()]
            specs.custom_domains[d_name.strip()] = patterns
            console.print(f"[bold green]✓ Domaine personnalisé enregistré :[/] [white]{d_name.strip()}[/] -> {patterns}")
            updated = True
        else:
            console.print("[red]Format attendu pour --set-domain : 'Nom=chemin1,chemin2'[/]")

    if forbid:
        if forbid not in specs.forbidden_extractions:
            specs.forbidden_extractions.append(forbid)
            console.print(f"[bold green]✓ Module/Table marqué interdit d'extraction :[/] [white]{forbid}[/]")
            updated = True

    if team_size is not None:
        specs.team_size = team_size
        console.print(f"[bold green]✓ Taille d'équipe persistée :[/] [white]{team_size} développeur(s)[/]")
        updated = True

    if prefer:
        specs.preferred_architecture = prefer.upper()
        console.print(f"[bold green]✓ Architecture préférée enregistrée :[/] [white]{prefer.upper()}[/]")
        updated = True

    if add_test_cmd:
        if add_test_cmd not in specs.authorized_test_commands:
            specs.authorized_test_commands.append(add_test_cmd)
            console.print(f"[bold green]✓ Commande de test autorisée :[/] [white]{add_test_cmd}[/]")
            updated = True

    if privacy:
        specs.privacy_level = privacy.upper()
        console.print(f"[bold green]✓ Niveau de confidentialité persisté :[/] [white]{privacy.upper()}[/]")
        updated = True

    if lang:
        normalized_lang = lang.strip().lower()
        if normalized_lang in ["fr", "en"]:
            specs.language = normalized_lang
            lang_name = "Français" if normalized_lang == "fr" else "English"
            console.print(f"[bold green]✓ Langue par défaut configurée :[/] [white]{lang_name} ({normalized_lang})[/]")
            updated = True
        else:
            console.print("[red]Format attendu pour --lang : 'fr' ou 'en'[/]")

    if updated or init:
        store.save_user_specifications(specs)
        console.print("[dim green]✓ Spécifications enregistrées dans .mono2micro/user_specifications.json[/]\n")

    # Display current configuration
    from rich.table import Table
    table = Table(title="[bold cyan]Spécificités & Contraintes Utilisateur Persistées[/]", box=None)
    table.add_column("Paramètre", style="bold white")
    table.add_column("Valeur Actuelle", style="cyan")

    table.add_row("Taille de l'équipe", f"{specs.team_size} développeur(s)")
    table.add_row("Architecture préférée", specs.preferred_architecture or "Auto-évaluation par l'architecte")
    table.add_row("Langue des rapports", f"{'Français (fr)' if specs.language == 'fr' else 'English (en)'}")
    table.add_row("Politique confidentialité", specs.privacy_level)
    table.add_row("Domaines personnalisés", ", ".join(f"{k} ({len(v)} chemins)" for k, v in specs.custom_domains.items()) or "Aucun (inférence automatique)")
    table.add_row("Extractions interdites", ", ".join(specs.forbidden_extractions) or "Aucune")
    table.add_row("Commandes de tests autorisées", ", ".join(specs.authorized_test_commands))

    console.print(table)
    console.print()
    console.print("[dim]Fichier éditable directement : .mono2micro/user_specifications.json[/]\n")


def main():
    """CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
