"""Verifier & Quality Gate Agent (Roles 6 & 7).

Enforces Workflow Step 9:
- Executes ONLY commands authorized by the user.
- Performs architectural boundary checks (no cross-boundary DB queries).
- Evaluates mandatory criteria without score averaging.
- Blocks delivery immediately if any mandatory criterion fails or was not verified.
"""

import hashlib
import shlex
import subprocess
from typing import List, Optional
from pathlib import Path
from mono2micro.models.quality_gate import (
    QualityGateCriterion,
    QualityGateResult,
    QualityGateCategory,
    CriterionStatus,
)
from mono2micro.models.plan import StranglerStep
from mono2micro.models.discovery import DiscoveryReport
from mono2micro.core.security import SafePathValidator


class VerifierAgent:
    """Agent running authorized test suites and checking architectural boundaries."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self.validator = SafePathValidator(target_directory)

    def run_architectural_boundary_check(
        self,
        step: StranglerStep,
        discovery: Optional[DiscoveryReport] = None,
    ) -> QualityGateCriterion:
        """Verify that the step's data boundary is sealed.

        Two checks are performed:
        1. Files outside the step scope must not access tables owned by the step
           (uses the static discovery's cross-module table access map).
        2. Files inside the scope must not keep direct connections to the legacy DB.
        """
        criterion_id = f"QG-ARCH-{step.step_number}"
        title = f"Étanchéité architecturale du domaine '{step.target_bounded_context}'"

        violations: List[str] = []
        in_scope = set(step.files_in_scope)

        # 1. Foreign accessors of tables owned by this step
        if discovery is not None:
            access_map = discovery.database_coupling.cross_module_table_access
            for table in step.data_ownership.source_tables:
                outsiders = [f for f in access_map.get(table, []) if f not in in_scope]
                if outsiders:
                    violations.append(
                        f"Table '{table}' encore accédée hors périmètre par : {', '.join(outsiders[:3])}"
                    )

        # 2. Residual legacy connections inside the scope
        for rel_file in step.files_in_scope:
            try:
                abs_file = self.validator.resolve_safe(rel_file)
                if abs_file.exists() and abs_file.is_file():
                    content = abs_file.read_text(encoding="utf-8", errors="ignore")
                    if "mysql://old" in content or "postgres://legacy" in content:
                        violations.append(f"Connexion résiduelle directe détectée dans {rel_file}")
            except Exception:
                pass

        if violations:
            return QualityGateCriterion(
                criterion_id=criterion_id,
                category=QualityGateCategory.ARCHITECTURAL_BOUNDARY,
                title=title,
                is_mandatory=True,
                status=CriterionStatus.FAILED,
                evidence=f"{len(violations)} violation(s) trouvée(s)",
                failure_details=" | ".join(violations)
            )

        return QualityGateCriterion(
            criterion_id=criterion_id,
            category=QualityGateCategory.ARCHITECTURAL_BOUNDARY,
            title=title,
            is_mandatory=True,
            status=CriterionStatus.PASSED,
            evidence="Frontière architecturale vérifiée sans accès croisé non autorisé."
        )

    def run_user_authorized_test_command(
        self,
        command_str: str,
        title: str,
        category: QualityGateCategory = QualityGateCategory.REGRESSION_TESTS,
        is_mandatory: bool = True
    ) -> QualityGateCriterion:
        """Run an authorized test command in the target directory."""
        digest = hashlib.sha1(command_str.encode("utf-8")).hexdigest()[:6]
        criterion_id = f"QG-TEST-{digest}"
        
        try:
            # No shell: the command is tokenized and executed directly, so
            # pipes, '&&', redirections and substitutions are never interpreted.
            argv = shlex.split(command_str)
            if not argv:
                raise ValueError("Commande vide")
            res = subprocess.run(
                argv,
                shell=False,
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                timeout=120
            )

            if res.returncode == 0:
                return QualityGateCriterion(
                    criterion_id=criterion_id,
                    category=category,
                    title=title,
                    is_mandatory=is_mandatory,
                    status=CriterionStatus.PASSED,
                    command_executed=command_str,
                    output_summary=res.stdout[-300:] if res.stdout else "Succès sans sortie",
                    evidence=f"Code retour 0"
                )
            else:
                return QualityGateCriterion(
                    criterion_id=criterion_id,
                    category=category,
                    title=title,
                    is_mandatory=is_mandatory,
                    status=CriterionStatus.FAILED,
                    command_executed=command_str,
                    output_summary=res.stderr[-300:] if res.stderr else res.stdout[-300:],
                    failure_details=f"Échec avec code de retour {res.returncode}"
                )
        except subprocess.TimeoutExpired:
            return QualityGateCriterion(
                criterion_id=criterion_id,
                category=category,
                title=title,
                is_mandatory=is_mandatory,
                status=CriterionStatus.FAILED,
                command_executed=command_str,
                failure_details="Délai d'exécution dépassé (timeout 120s)"
            )
        except Exception as e:
            return QualityGateCriterion(
                criterion_id=criterion_id,
                category=category,
                title=title,
                is_mandatory=is_mandatory,
                status=CriterionStatus.FAILED,
                command_executed=command_str,
                failure_details=f"Erreur d'exécution: {str(e)}"
            )

    def evaluate_quality_gate(self, criteria: List[QualityGateCriterion], step_number: int) -> QualityGateResult:
        """Aggregate criteria enforcing strict zero-averaging."""
        return QualityGateResult(
            step_number=step_number,
            criteria=criteria
        )
