"""Official Command Line Interface (CLI) for Mono2Micro Agent.

Commands:
- agent analyze   : Read-only static discovery, inventory, facts & assumptions.
- agent plan      : Clarify objectives, DDD domain analysis & 4 options comparison.
- agent test-plan : Devil's advocate critique, hidden couplings & independent tests.
- agent apply     : Controlled step application on isolated git branch with rollback.
- agent verify    : Architectural boundary check, authorized tests & strict Quality Gate.
"""

import difflib
import sys
import os
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.markup import escape
from rich.syntax import Syntax

from mono2micro.core.orchestrator import MigrationOrchestrator
from mono2micro.config import ProjectStateStore, UserSpecifications
from mono2micro.ui.rich_formatters import ConsoleFormatter
from mono2micro.models.objectives import MigrationGoalType
from mono2micro.models.options import ArchitectureOptionType
from mono2micro.core.security import SecretMasker
from mono2micro.models.audit import AuditActionType
from mono2micro.llm import LLMError, SUPPORTED_PROVIDERS, build_client_from_specs
from mono2micro.agents.implementer import ProposalError, StepProposal

app = typer.Typer(
    name="agent",
    help="Local CLI agent for empirical monolith modernization and modularization (Hammad et al., 2023).",
    no_args_is_help=True
)

console = Console()


def get_orchestrator(target_path: Optional[str] = None, llm=None) -> MigrationOrchestrator:
    """Resolve workspace directory and initialize orchestrator."""
    path = target_path or os.getcwd()
    return MigrationOrchestrator(path, llm=llm)


def resolve_llm(target_path: str, ask_key: bool = False, required: bool = False):
    """Build the LLM client from persisted settings and the user's own API key.

    The key comes from the environment (OPENAI_API_KEY / ANTHROPIC_API_KEY /
    GEMINI_API_KEY) or, with --ask-api-key, from a hidden prompt. It is never saved.
    Returns None when no provider is configured. If a provider is configured but
    unusable: abort when `required`, otherwise warn and fall back to local heuristics.
    """
    specs = ProjectStateStore(target_path).get_user_specifications()
    try:
        client = build_client_from_specs(specs, ask_key=ask_key)
    except LLMError as exc:
        if required:
            console.print(f"[bold red]❌ LLM unavailable:[/] {escape(str(exc))}")
            raise typer.Exit(code=1)
        console.print(f"[yellow]⚠️ LLM skipped ({escape(str(exc))}). Using local heuristics only.[/]\n")
        return None
    if client is not None:
        cfg = getattr(client, "config", None)
        label = f"{cfg.provider}/{cfg.model}" if cfg else specs.llm_provider
        console.print(f"[bold cyan]🤖 Active LLM:[/] [white]{label}[/] [dim](key read from environment, never persisted)[/]")
        console.print("[dim]Metadata sent: file paths, model names, frameworks. No source file content for 'plan'.[/]\n")
    return client


def render_proposal_diff(proposal: StepProposal) -> str:
    """Unified diff of everything the model proposes (new files diff against /dev/null)."""
    chunks = []
    for path, new_text in sorted(proposal.files.items()):
        old_text = proposal.originals.get(path, "")
        chunks.append("".join(difflib.unified_diff(
            old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
            fromfile=f"a/{path}" if old_text else "/dev/null", tofile=f"b/{path}",
        )))
    return "\n".join(chunks)


@app.command(name="analyze")
def cmd_analyze(
    path: str = typer.Option(".", "--path", "-p", help="Target project directory path to analyze."),
    offline: bool = typer.Option(True, "--offline", help="Static local analysis mode without external calls."),
):
    """Read-only repository discovery: components, verified facts, and model hypotheses."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    console.print(f"[bold cyan]🔍 Launching passive discovery on:[/] [white]{resolved_path}[/]\n")

    orchestrator = get_orchestrator(resolved_path)
    report = orchestrator.step_1_discover()

    # Rich formatting
    ConsoleFormatter.display_discovery_report(report)

    # Persist state
    store = ProjectStateStore(resolved_path)
    store.save_json("discovery.json", report.model_dump())
    console.print("[dim green]✓ Discovery saved in .mono2micro/discovery.json[/]\n")
    console.print("[bold yellow]Recommended next command:[/] [bold white]agent plan[/]")


@app.command(name="graph")
def cmd_graph(
    path: str = typer.Option(".", "--path", "-p", help="Project directory path."),
    export: Optional[str] = typer.Option(None, "--export", "-o", help="Custom path to export graph JSON."),
):
    """Build dependency graph (AST & data layer) and calculate Louvain modularity partitions offline."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    console.print(f"[bold cyan]🔍 Extracting dependency graph & clustering on:[/] [white]{resolved_path}[/]\n")
    orchestrator = get_orchestrator(resolved_path)
    graph, eval_result = orchestrator.build_dependency_graph()

    from rich.table import Table
    table = Table(title="[bold cyan]Offline Structural Partitions & Modularity (Louvain)[/]", box=None)
    table.add_column("Proposed Domain", style="bold white")
    table.add_column("Files Count", style="cyan")
    table.add_column("Tables Owned", style="green")
    table.add_column("Tables Ref", style="yellow")
    table.add_column("Cohesion", style="magenta")

    for part in eval_result.partitions:
        table.add_row(
            part.domain_name,
            str(len(part.files)),
            ", ".join(part.tables_owned) or "-",
            ", ".join(part.tables_referenced) or "-",
            f"{part.cohesion_score:.2f}",
        )

    console.print(table)
    console.print(f"\n[bold white]Graph Summary:[/] {graph.node_count} nodes, {graph.edge_count} edges")
    console.print(f"[bold green]Modularity Q:[/] [white]{eval_result.modularity_q:.4f}[/]")
    console.print(f"[bold yellow]Inter-domain Coupling Ratio:[/] [white]{eval_result.inter_domain_coupling_ratio:.4f}[/]")
    console.print(f"[bold red]Shared Tables Count:[/] [white]{eval_result.shared_tables_count}[/]")
    if eval_result.shared_tables_detail:
        for tbl, doms in eval_result.shared_tables_detail.items():
            console.print(f"  • [red]{tbl}[/] shared between: {', '.join(doms)}")

    if export:
        from mono2micro.analysis.graph_engine import GraphEngine
        engine = GraphEngine(resolved_path)
        engine.export_graph_json(graph, export)
        console.print(f"\n[dim green]✓ Custom graph export written to {export}[/]\n")
    else:
        console.print("\n[dim green]✓ Graph exported to .mono2micro/dependency_graph.json[/]")
        console.print("[dim green]✓ Partitions exported to .mono2micro/partitions.json[/]\n")


@app.command(name="plan")
def cmd_plan(
    path: str = typer.Option(".", "--path", "-p", help="Chemin du projet."),
    goal: str = typer.Option("CODEBASE_MODULARITY", "--goal", "-g", help="Objectif : TARGETED_SCALABILITY, TEAM_AUTONOMY, DEPLOY_FREQUENCY, FAULT_ISOLATION, CODEBASE_MODULARITY, TECH_DIVERSITY, INFRASTRUCTURE_COST."),
    team_size: int = typer.Option(2, "--team-size", "-t", help="Nombre de développeurs sur le projet."),
    rationale: str = typer.Option("Modernisation et clarification de l'architecture", "--rationale", "-r", help="Motivation détaillée."),
    ask_api_key: bool = typer.Option(False, "--ask-api-key", help="Saisir la clé API LLM (masquée, non enregistrée) si absente de l'environnement."),
):
    """Clarification des objectifs, analyse de domaines (DDD) et comparaison des 4 options architecturales."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    llm = resolve_llm(resolved_path, ask_key=ask_api_key, required=False)
    orchestrator = get_orchestrator(resolved_path, llm=llm)

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
    ask_api_key: bool = typer.Option(False, "--ask-api-key", help="Saisir la clé API LLM (masquée, non enregistrée) si absente de l'environnement."),
):
    """Application contrôlée d'une étape validée sur branche Git isolée après approbation.

    Avec un LLM configuré, le modèle propose le code de l'étape ; le diff complet est
    affiché pour relecture AVANT toute écriture, et l'approbation ne couvre que ces fichiers.
    """
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    llm = resolve_llm(resolved_path, ask_key=ask_api_key, required=True)
    orchestrator = get_orchestrator(resolved_path, llm=llm)

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

    # M1 Integrity check: if approval was previously recorded, ensure current plan is identical
    existing_approval = orchestrator.audit_logger.get_latest_approval(step)
    if existing_approval:
        is_valid, tamper_msg = orchestrator.verify_plan_before_apply(step)
        if not is_valid:
            console.print(f"[bold red]❌ {tamper_msg}[/]")
            raise typer.Exit(code=1)

    # --- Optional: model-proposed code, reviewed before anything is written
    proposal: Optional[StepProposal] = None
    if llm is not None:
        console.print("[bold yellow]⚠️ Le code des fichiers du périmètre (secrets masqués) sera envoyé au fournisseur LLM.[/]")
        if not confirm and not Confirm.ask("Autoriser cet envoi ?", default=False):
            console.print("[red]Envoi refusé : aucune génération.[/]")
            raise typer.Exit(code=1)
        try:
            proposal = orchestrator.propose_step_changes(step)
        except (ProposalError, LLMError, ValueError) as exc:
            console.print(f"[bold red]❌ Génération impossible :[/] {escape(str(exc))}")
            raise typer.Exit(code=1)

        diff_text = render_proposal_diff(proposal)
        ProjectStateStore(resolved_path).save_text(f"step-{step}.diff", diff_text)
        console.print(f"\n[bold cyan]Proposition du modèle : {len(proposal.files)} fichier(s)[/] [dim](diff complet : .mono2micro/step-{step}.diff)[/]")
        lines = diff_text.splitlines()
        console.print(Syntax("\n".join(lines[:300]), "diff", word_wrap=True))
        if len(lines) > 300:
            console.print(f"[dim]… {len(lines) - 300} lignes supplémentaires dans le fichier diff.[/]")
        for rejected_path, reason in proposal.rejected.items():
            console.print(f"[yellow]✗ Rejeté : {escape(rejected_path)} — {escape(reason)}[/]")
        if proposal.notes:
            console.print(f"[dim]Notes du modèle : {escape(proposal.notes)}[/]")
        console.print()

        # M5: Adversarial Diff Review
        from mono2micro.review.diff_reviewer import AdversarialDiffReviewer
        owned_tables = target_step.data_ownership.source_tables + target_step.data_ownership.target_tables
        reviewer = AdversarialDiffReviewer()
        violations = reviewer.review_diff(
            diff_text=diff_text,
            files_allowed=sorted(proposal.files),
            owned_tables=owned_tables,
        )
        if violations:
            console.print("[bold red]⛔ REJET ADVERSARIAL DU DIFF :[/]")
            for v in violations:
                console.print(f"  • [red]{v.rule.value}[/] ({v.file_path}:{v.line_number or '-'}): {v.description}")
                if v.code_excerpt:
                    console.print(f"    [dim]{escape(v.code_excerpt)}[/]")
            orchestrator.audit_logger.log_action(
                action=AuditActionType.DEVIL_ADVOCATE_BLOCKED,
                plan_id=plan.plan_id,
                plan_hash=plan.plan_hash or plan.compute_canonical_hash(),
                step_number=step,
                details={"violations": [v.description for v in violations]},
            )
            console.print("[bold red]❌ Application annulée en raison d'objections adversariales bloquantes.[/]\n")
            raise typer.Exit(code=1)

    files_allowed = sorted(proposal.files) if proposal else None
    shown_scope = files_allowed if proposal else target_step.files_in_scope

    # Request human approval
    console.print(f"[bold yellow]⚠️ DEMANDE D'APPROBATION HUMAINE FORMELLE POUR L'ÉTAPE {step} :[/]")
    console.print(f"[white]Titre :[/] {target_step.title}")
    console.print(f"[white]Périmètre des fichiers :[/] {', '.join(shown_scope) or 'Fichiers déclarés du module'}")
    console.print(f"[white]Procédure de Rollback :[/] {target_step.rollback.git_revert_command}\n")

    confirmation = confirm
    if not confirmation:
        confirmation = Prompt.ask("[bold red]Confirmez-vous l'application de cette étape sur branche isolée ? (Tapez 'OUI' pour approuver)[/]")

    try:
        token = orchestrator.step_7_request_human_approval(step, confirmation, files_allowed=files_allowed)
        console.print(f"[bold green]✓ Approbation accordée avec succès (Jeton: {token}).[/]\n")
    except Exception as e:
        console.print(f"[bold red]❌ Échec de permission :[/] {escape(str(e))}")
        raise typer.Exit(code=1)

    implementer = orchestrator.implementer

    if proposal:
        # Never write on top of the user's uncommitted work
        dirty = implementer.uncommitted_among(list(proposal.files))
        if dirty:
            console.print(f"[bold red]❌ Fichiers avec modifications non commitées :[/] {', '.join(dirty)}")
            console.print("[red]Commitez ou stashez-les avant 'agent apply'.[/]")
            raise typer.Exit(code=1)

    success, msg = implementer.prepare_isolation_branch(target_step)
    if success:
        console.print(f"[green]✓ {msg}[/]")
    else:
        console.print(f"[yellow]⚠️ {msg}[/]")

    if proposal:
        if not success:
            console.print("[bold red]❌ Écriture refusée : l'isolation sur branche Git est obligatoire.[/]")
            raise typer.Exit(code=1)
        ok, write_msg, written = implementer.apply_file_changes(target_step, proposal.files)
        if not ok:
            orchestrator.audit_logger.log_action(
                action=AuditActionType.STEP_APPLY_FAILED,
                plan_id=plan.plan_id,
                plan_hash=plan.plan_hash or plan.compute_canonical_hash(),
                step_number=step,
                details={"error": write_msg},
            )
            console.print(f"[bold red]❌ {escape(write_msg)}[/]")
            raise typer.Exit(code=1)
        orchestrator.audit_logger.log_action(
            action=AuditActionType.STEP_APPLY_SUCCESS,
            plan_id=plan.plan_id,
            plan_hash=plan.plan_hash or plan.compute_canonical_hash(),
            step_number=step,
            details={"written_files": written},
        )
        console.print(f"[bold green]✓ {len(written)} fichier(s) écrit(s) sur la branche isolée (non commités) :[/]")
        for w in written:
            console.print(f"  • {w}")
        console.print("\n[bold yellow]À faire :[/] relire avec [white]git diff[/], puis [white]agent verify --step "
                      f"{step}[/] ; annuler avec [white]git checkout -- . && git checkout -[/].")
    else:
        orchestrator.audit_logger.log_action(
            action=AuditActionType.STEP_APPLY_SUCCESS,
            plan_id=plan.plan_id,
            plan_hash=plan.plan_hash or plan.compute_canonical_hash(),
            step_number=step,
            details={"mode": "branch_initialized"},
        )
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
    llm_provider: Optional[str] = typer.Option(None, "--llm-provider", help="Fournisseur LLM : openai (ou compatible), anthropic, gemini. La clé se donne par variable d'environnement."),
    llm_model: Optional[str] = typer.Option(None, "--llm-model", help="Nom du modèle chez le fournisseur."),
    llm_base_url: Optional[str] = typer.Option(None, "--llm-base-url", help="URL de base (serveur compatible OpenAI, ex: http://localhost:11434/v1)."),
    llm_off: bool = typer.Option(False, "--llm-off", help="Désactiver le LLM (retour au mode heuristique local)."),
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

    if llm_off:
        specs.llm_provider = specs.llm_model = specs.llm_base_url = None
        console.print("[bold green]✓ LLM désactivé (mode heuristique local).[/]")
        updated = True

    if llm_provider:
        normalized = llm_provider.strip().lower()
        if normalized in SUPPORTED_PROVIDERS:
            specs.llm_provider = normalized
            console.print(f"[bold green]✓ Fournisseur LLM :[/] [white]{normalized}[/] [dim](clé via la variable d'environnement, jamais enregistrée)[/]")
            updated = True
        else:
            console.print(f"[red]Fournisseur inconnu. Choix : {', '.join(SUPPORTED_PROVIDERS)}[/]")

    if llm_model:
        specs.llm_model = llm_model.strip()
        console.print(f"[bold green]✓ Modèle LLM :[/] [white]{specs.llm_model}[/]")
        updated = True

    if llm_base_url:
        specs.llm_base_url = llm_base_url.strip()
        console.print(f"[bold green]✓ URL de base LLM :[/] [white]{specs.llm_base_url}[/]")
        updated = True

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
    table.add_row("LLM", f"{specs.llm_provider}/{specs.llm_model or 'modèle par défaut'}" if specs.llm_provider else "Désactivé (heuristiques locales)")

    console.print(table)
    console.print()
    console.print("[dim]Fichier éditable directement : .mono2micro/user_specifications.json[/]\n")


@app.command(name="approve")
def cmd_approve(
    path: str = typer.Option(".", "--path", "-p", help="Project directory path."),
    step: int = typer.Option(1, "--step", "-s", help="Step number to approve."),
    confirm: Optional[str] = typer.Option(None, "--confirm", "-c", help="Explicit confirmation string ('YES', 'OUI', or token)."),
):
    """Sign and persist human approval for a specific migration step."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)
    orchestrator.step_1_discover()
    orchestrator.step_3_analyze_domains()
    orchestrator.step_4_compare_options()
    plan = orchestrator.step_5_plan_migration()

    review = orchestrator.step_6_adversarial_review(step_number=step)
    if review.step_is_blocked:
        console.print(f"[bold red]Approval Refused: Step {step} is blocked by the devil's advocate.[/]")
        for r in review.blocking_reasons:
            console.print(f"  • [red]{r}[/]")
        raise typer.Exit(code=1)

    target_step = next((s for s in plan.steps if s.step_number == step), None)
    if not target_step:
        console.print(f"[red]Step {step} not found in plan.[/]")
        raise typer.Exit(code=1)

    confirmation = confirm
    if not confirmation:
        confirmation = Prompt.ask(f"[bold yellow]Approve step {step} ({target_step.title})? (Type 'YES' to confirm)[/]")

    try:
        token = orchestrator.step_7_request_human_approval(step, confirmation)
        console.print(f"[bold green]✓ Step {step} approved and signed (Plan Hash: {plan.plan_hash[:16]}..., Token: {token}).[/]")
        console.print("[dim green]✓ Approval recorded in .mono2micro/approvals.jsonl and .mono2micro/audit.jsonl[/]\n")
    except Exception as e:
        console.print(f"[bold red]❌ Approval failed:[/] {escape(str(e))}")
        raise typer.Exit(code=1)


@app.command(name="audit")
def cmd_audit(
    path: str = typer.Option(".", "--path", "-p", help="Project directory path."),
    limit: int = typer.Option(50, "--limit", "-n", help="Max records to display."),
):
    """Inspect persistent JSONL audit trail."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)
    records = orchestrator.audit_logger.read_all_audit_records()
    if not records:
        console.print("[dim yellow]No audit records found in .mono2micro/audit.jsonl[/]\n")
        return

    from rich.table import Table
    table = Table(title=f"[bold cyan]Audit Log Trail ({len(records)} records)[/]", box=None)
    table.add_column("Timestamp", style="dim")
    table.add_column("Action", style="bold white")
    table.add_column("Actor", style="cyan")
    table.add_column("Step", style="yellow")
    table.add_column("Plan Hash", style="magenta")

    for r in records[-limit:]:
        table.add_row(
            r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            r.action.value,
            r.actor,
            str(r.step_number or "-"),
            f"{r.plan_hash[:12]}..." if r.plan_hash else "-",
        )
    console.print(table)
    console.print()


@app.command(name="bench")
def cmd_bench(
    results_dir: str = typer.Option("benchmarks/results", "--output", "-o", help="Directory where benchmark results will be saved."),
):
    """Execute the empirical benchmark suite across pinned corpus items with ablations."""
    ConsoleFormatter.print_banner()
    from benchmarks.runner import BenchmarkRunner
    console.print("[bold cyan]🚀 Running Mono2Micro Benchmark Suite across 6 corpus projects...[/]\n")
    runner_inst = BenchmarkRunner(results_dir=results_dir)
    report = runner_inst.run_suite()

    from rich.table import Table
    table = Table(title="[bold cyan]Empirical Benchmark & Ablation Results[/]", box=None)
    table.add_column("Benchmark", style="bold white")
    table.add_column("Baseline", style="cyan")
    table.add_column("GT?", style="yellow")
    table.add_column("Precision", style="green")
    table.add_column("Recall", style="green")
    table.add_column("Modularity Q", style="magenta")
    table.add_column("Coupling", style="yellow")
    table.add_column("Shared Tbls", style="red")
    table.add_column("Tokens", style="dim")
    table.add_column("Cost ($)", style="dim")

    for r in report.corpus_runs:
        table.add_row(
            r.benchmark_name,
            r.baseline_mode.value,
            "Yes" if r.precision is not None else "Surrogate",
            f"{r.precision:.2f}" if r.precision is not None else "N/A",
            f"{r.recall:.2f}" if r.recall is not None else "N/A",
            f"{r.modularity_q:.2f}",
            f"{r.inter_domain_coupling_ratio:.2f}",
            str(r.shared_tables_count),
            str(r.tokens_consumed),
            f"${r.cost_usd:.4f}",
        )

    console.print(table)
    console.print(f"\n[bold green]✓ Benchmark completed successfully ({len(report.corpus_runs)} evaluation runs).[/]")
    console.print(f"[dim green]✓ Results saved in {results_dir}/ (JSON and Markdown table).[/]\n")


@app.command(name="doctor")
def cmd_doctor(
    path: str = typer.Option(".", "--path", "-p", help="Target project directory path."),
):
    """Diagnose local setup, offline readiness, capability matrix, and scan for prompt injection."""
    ConsoleFormatter.print_banner()
    resolved_path = str(Path(path).resolve())
    orchestrator = get_orchestrator(resolved_path)

    import sys
    py_ver = sys.version.split()[0]
    is_git = os.path.exists(os.path.join(resolved_path, ".git"))
    has_key = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )
    provider = orchestrator.user_specs.llm_provider

    console.print(f"[bold cyan]Mono2Micro System & Capability Diagnostics[/]\n")
    console.print(f"• Python version : [white]{py_ver}[/] (>= 3.10 required)")
    console.print(f"• Git repository : [{'green' if is_git else 'yellow'}]{'Yes' if is_git else 'No'}[/]")
    console.print(f"• Offline mode   : [bold green]Ready (100% offline analysis & AST graph)[/]")
    console.print(f"• LLM Provider   : [white]{provider or 'None (Offline Heuristics)'}[/]")
    console.print(f"• Active API Key : [{'green' if has_key else 'dim'}]{'Present in environment' if has_key else 'None (Safe Offline)'}[/]\n")

    from rich.table import Table
    table = Table(title="[bold cyan]Command Capability Matrix[/]", box=None)
    table.add_column("Command", style="bold white")
    table.add_column("Offline Capability (Default)", style="green")
    table.add_column("LLM-Augmented Mode (Optional)", style="cyan")
    table.add_column("API Key?", style="yellow")

    table.add_row("analyze", "Full AST inventory, components, facts", "Enriched semantic commentary", "No")
    table.add_row("graph", "AST dependency graph, Louvain modularity Q", "Semantic edge weighting", "No")
    table.add_row("plan", "Heuristic Bounded Contexts, 4 options matrix", "Domain naming refinement", "No")
    table.add_row("test-plan", "Devil's advocate static coupling check", "Adversarial edge-case generator", "No")
    table.add_row("apply", "Isolated git branch creation & rollback", "Code generation with diff review", "Required for codegen")
    table.add_row("verify", "Strict Quality Gate, boundary check", "Root-cause diagnostics on test failure", "No")
    table.add_row("bench", "Full 6-corpus ablation suite", "Hybrid agent precision evaluation", "Optional")

    console.print(table)
    console.print()

    # Scan for prompt injection in source files
    injection_warnings = []
    suspicious_patterns = [
        r'ignore\s+all\s+previous\s+instructions',
        r'you\s+are\s+now\s+in\s+developer\s+mode',
        r'system\s+prompt\s+override',
    ]
    for root, _, files in os.walk(resolved_path):
        if any(p in root.split(os.sep) for p in (".git", "node_modules", ".mono2micro")):
            continue
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".java", ".md")):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fl:
                        txt = fl.read()
                    for pat in suspicious_patterns:
                        if re.search(pat, txt, re.IGNORECASE):
                            injection_warnings.append(f"{os.path.relpath(fpath, resolved_path)}: matched '{pat}'")
                except Exception:
                    pass

    if injection_warnings:
        console.print("[bold red]⚠️ Potential Prompt Injection Warnings in Codebase Comments:[/]")
        for w in injection_warnings:
            console.print(f"  • [red]{w}[/]")
    else:
        console.print("[bold green]✓ Prompt Injection Check:[/] No suspicious instructions detected in codebase comments.")
    console.print()


def main():
    """CLI entrypoint."""
    app()


if __name__ == "__main__":
    main()
