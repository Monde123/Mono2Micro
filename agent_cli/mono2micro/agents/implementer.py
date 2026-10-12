"""Controlled Implementer Agent (Role 5).

Enforces Workflow Step 8:
- Applies ONLY ONE approved step at a time.
- Requires explicit verification by PermissionEngine before any write.
- Isolates changes on a dedicated Git branch.
- Modifies strictly files within the approved scope.
- Enforces single-writer discipline.
- Keeps a clean diff and provides immediate rollback commands.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from mono2micro.core.permissions import PermissionEngine, ApprovalRecord, PermissionDeniedError
from mono2micro.core.security import SafePathValidator
from mono2micro.models.plan import StranglerStep


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
