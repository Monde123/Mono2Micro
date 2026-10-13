"""Controlled Implementer Agent (Role 5).

Enforces Workflow Step 8:
- Applies ONLY ONE approved step at a time.
- Requires explicit verification by PermissionEngine before any write.
- Isolates changes on a dedicated Git branch.
- Modifies strictly files within the approved scope.
- Enforces single-writer discipline.
- Keeps a clean diff and provides immediate rollback commands.
"""

import glob
import json
import os
import posixpath
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from mono2micro.core.permissions import PermissionEngine, ApprovalRecord, PermissionDeniedError
from mono2micro.core.security import SafePathValidator
from mono2micro.models.plan import StranglerStep
from mono2micro.core.security import PrivacyFilter, PrivacyLevel
from mono2micro.llm import LLMClient, extract_json
from mono2micro.tools.repo_scanner import IGNORED_DIRS

SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rb", ".php", ".cs", ".rs"}
MAX_SCOPE_FILES = 30
MAX_FILE_BYTES = 60_000
MAX_TOTAL_BYTES = 150_000
MAX_PROPOSED_FILE_BYTES = 200_000


class ProposalError(ValueError):
    """The model's proposal cannot be used (or cannot be requested safely)."""


@dataclass
class StepProposal:
    """Validated, not-yet-applied changes proposed by the model for one step."""
    files: Dict[str, str]                       # path -> COMPLETE new content
    originals: Dict[str, str]                   # path -> current content ('' for new files)
    rejected: Dict[str, str] = field(default_factory=dict)   # path -> reason
    notes: str = ""
    scope_files: List[str] = field(default_factory=list)
    new_files_prefix: str = ""


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "service"


class ImplementerAgent:
    """Agent in charge of controlled, isolated modifications upon explicit human approval."""

    def __init__(self, target_directory: str, permission_engine: PermissionEngine):
        self.target_directory = target_directory
        self.permission_engine = permission_engine
        self.validator = SafePathValidator(target_directory)

    def prepare_isolation_branch(self, step: StranglerStep) -> Tuple[bool, str]:
        """Create an isolated git branch for the step changes."""
        branch_name = f"mono2micro/step-{step.step_number}-{step.target_bounded_context.lower()}"
        
        try:
            # Check if git is available in target dir
            res = subprocess.run(
                ["git", "status"],
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode != 0:
                return False, "Le répertoire cible n'est pas un dépôt Git initialisé. Recommandation: 'git init'."

            # Create and switch to isolated branch
            create_res = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                check=False
            )
            if create_res.returncode != 0:
                # If branch already exists, switch to it
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.target_directory,
                    capture_output=True,
                    text=True,
                    check=False
                )

            return True, f"Branche isolée '{branch_name}' prête pour l'étape {step.step_number}."
        except Exception as e:
            return False, f"Impossible de préparer la branche Git : {str(e)}"

    def apply_file_changes(
        self,
        step: StranglerStep,
        modifications: Dict[str, str],
    ) -> Tuple[bool, str, List[str]]:
        """Apply modifications only after verifying human permission and file boundaries."""
        # 1. Verify permission engine
        target_files = list(modifications.keys())
        self.permission_engine.verify_permission_to_apply_step(step.step_number, target_files)

        # 2. Check path containment
        for rel_path in target_files:
            self.validator.resolve_safe(rel_path)

        applied_files: List[str] = []
        try:
            for rel_path, new_content in modifications.items():
                abs_path = self.validator.resolve_safe(rel_path)
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(new_content, encoding="utf-8")
                applied_files.append(rel_path)

            # Mark step executed in permissions
            self.permission_engine.mark_step_executed(step.step_number)
            step.approved_by_human = True
            
            return True, f"Succès : {len(applied_files)} fichier(s) modifiés avec succès dans le périmètre autorisé.", applied_files
        except Exception as e:
            return False, f"Erreur lors de l'application des modifications : {str(e)}", applied_files


    def uncommitted_among(self, paths: List[str]) -> List[str]:
        """Return those paths that have uncommitted local changes (empty if not a git repo)."""
        res = subprocess.run(
            ["git", "status", "--porcelain", "--"] + list(paths),
            cwd=self.target_directory, capture_output=True, text=True, check=False,
        )
        if res.returncode != 0:
            return []
        return [line[3:].strip() for line in res.stdout.splitlines() if line.strip()]

    # ------------------------------------------------------------------ LLM proposals

    def expand_scope(self, step: StranglerStep) -> List[str]:
        """Resolve the step scope (files, directories, globs) to concrete source files."""
        root = self.validator.base_path
        found: List[str] = []
        total = 0

        def add(path: Path) -> bool:
            nonlocal total
            try:
                rel = path.resolve().relative_to(root).as_posix()
                size = path.stat().st_size
            except (ValueError, OSError):
                return True
            if path.suffix.lower() not in SOURCE_EXTS or size > MAX_FILE_BYTES or rel in found:
                return True
            if len(found) >= MAX_SCOPE_FILES or total + size > MAX_TOTAL_BYTES:
                return False
            found.append(rel)
            total += size
            return True

        for entry in step.files_in_scope:
            for raw in (e.strip() for e in entry.split(",")):
                if not raw:
                    continue
                if any(ch in raw for ch in "*?["):
                    candidates = [Path(m) for m in glob.glob(str(root / raw), recursive=True)]
                else:
                    candidates = [root / raw]
                for cand in candidates:
                    if cand.is_file():
                        if not add(cand):
                            return sorted(found)
                    elif cand.is_dir():
                        for dirpath, dirs, files in os.walk(cand):
                            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith("."))
                            for name in sorted(files):
                                if not add(Path(dirpath) / name):
                                    return sorted(found)
        return sorted(found)

    _SYSTEM = (
        "Tu es un ingénieur senior spécialisé en migration progressive de monolithes (patron Strangler Fig). "
        "Tu implémentes UNE seule étape, de façon minimale, réversible et sans changer le comportement observable. "
        "Règles strictes : (1) ne modifie que les fichiers fournis, ou crée de nouveaux fichiers UNIQUEMENT sous le "
        "préfixe indiqué ; (2) renvoie le contenu COMPLET de chaque fichier, jamais un diff ; (3) n'invente aucune "
        "règle métier et ne mets aucun secret ; (4) si l'étape ne peut pas être réalisée sans information manquante, "
        'renvoie {"files":{}, "notes":"<ce qui manque>"}. Réponds UNIQUEMENT par un JSON : '
        '{"files":{"chemin":"contenu complet"},"notes":"résumé et points de vigilance"}.'
    )

    def propose_modifications(
        self,
        step: StranglerStep,
        llm: LLMClient,
        privacy_level: str = "FULL_CODE_REDACTED",
        business_notes: Optional[str] = None,
    ) -> StepProposal:
        """Ask the model for the step's code changes and validate them strictly.

        Nothing is written here. The caller must show the diff, obtain human
        approval for exactly the returned paths, and only then call apply_file_changes.
        """
        if str(privacy_level).upper() != PrivacyLevel.FULL_CODE_REDACTED.value:
            raise ProposalError(
                "La génération de code exige la politique FULL_CODE_REDACTED : avec METADATA_ONLY ou "
                "ANONYMIZED_SYMBOLS le modèle ne voit pas le code réel et ses fichiers ne pourraient pas être réécrits."
            )

        scope_files = self.expand_scope(step)
        if not scope_files:
            raise ProposalError(
                f"Aucun fichier source exploitable dans le périmètre de l'étape {step.step_number}. "
                "Définissez le domaine avec : agent config --set-domain \"Nom=chemin/**\"."
            )

        prefix = f"services/{_slug(step.target_bounded_context)}/"
        privacy = PrivacyFilter(PrivacyLevel.FULL_CODE_REDACTED)
        originals: Dict[str, str] = {}
        blocks: List[str] = []
        for rel in scope_files:
            raw = self.validator.resolve_safe(rel).read_text(encoding="utf-8", errors="ignore")
            originals[rel] = raw
            blocks.append(f"=== FICHIER: {rel} ===\n{privacy.sanitize_snippet(raw, rel)}")

        brief = {
            "etape": step.step_number,
            "titre": step.title,
            "description": step.description,
            "contexte_metier": step.target_bounded_context,
            "routage": f"{step.routing_strategy.value} — {step.routing_details}",
            "donnees": {
                "strategie": step.data_ownership.strategy.value,
                "tables_source": step.data_ownership.source_tables,
                "double_ecriture": step.data_ownership.dual_write_required,
            },
            "criteres_de_succes": step.success_criteria,
            "retour_arriere": step.rollback.steps_fr,
            "prefixe_nouveaux_fichiers": prefix,
            "notes_equipe": privacy.sanitize_snippet(business_notes or "", "notes"),
        }
        user = (
            "Étape à implémenter :\n" + json.dumps(brief, ensure_ascii=False, indent=2)
            + "\n\nCode actuel (secrets masqués) :\n\n" + "\n\n".join(blocks)
        )

        data = extract_json(llm.complete(self._SYSTEM, user))
        files_raw = data.get("files") if isinstance(data, dict) else None
        notes = str(data.get("notes", ""))[:2000] if isinstance(data, dict) else ""
        if not isinstance(files_raw, dict) or not files_raw:
            raise ProposalError(f"Le modèle n'a proposé aucune modification. {notes}".strip())

        accepted: Dict[str, str] = {}
        rejected: Dict[str, str] = {}
        for path, content in files_raw.items():
            reason = self._reject_reason(path, content, set(scope_files), prefix, originals)
            if reason == "unchanged":
                continue
            if reason:
                rejected[str(path)] = reason
            else:
                accepted[path] = content

        if not accepted:
            raise ProposalError(
                "Toutes les modifications proposées ont été rejetées : "
                + "; ".join(f"{k} ({v})" for k, v in rejected.items())
            )
        return StepProposal(
            files=accepted,
            originals={p: originals.get(p, "") for p in accepted},
            rejected=rejected,
            notes=notes,
            scope_files=scope_files,
            new_files_prefix=prefix,
        )

    @staticmethod
    def _reject_reason(path, content, scope: set, prefix: str, originals: Dict[str, str]) -> Optional[str]:
        if not isinstance(path, str) or not path:
            return "chemin invalide"
        unified = path.replace("\\", "/")
        norm = posixpath.normpath(unified)
        if norm != unified or norm.startswith(("/", "..")) or norm == ".":
            return "chemin non normalisé ou hors dépôt"
        if norm not in scope and not norm.startswith(prefix):
            return "hors périmètre autorisé"
        if not isinstance(content, str):
            return "contenu non textuel"
        if "\x00" in content or len(content.encode("utf-8")) > MAX_PROPOSED_FILE_BYTES:
            return "contenu binaire ou trop volumineux"
        original = originals.get(norm)
        if "[REDACTED" in content and (original is None or "[REDACTED" not in original):
            return "contient un marqueur de secret masqué (écriture refusée pour ne pas corrompre le fichier)"
        if original is not None and content == original:
            return "unchanged"
        return None
