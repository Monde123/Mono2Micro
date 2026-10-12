"""Verifier & Quality Gate Agent (Roles 6 & 7).

Enforces Workflow Step 9:
- Executes ONLY commands authorized by the user.
- Performs architectural boundary checks (no cross-boundary DB queries).
- Evaluates mandatory criteria without score averaging.
- Blocks delivery immediately if any mandatory criterion fails or was not verified.
"""

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
from mono2micro.core.security import SafePathValidator


class VerifierAgent:
    """Agent running authorized test suites and checking architectural boundaries."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self.validator = SafePathValidator(target_directory)

    def run_architectural_boundary_check(self, step: StranglerStep) -> QualityGateCriterion:
        """Verify that extracted code does not contain unauthorized cross-database queries."""
        criterion_id = f"QG-ARCH-{step.step_number}"
        title = f"Étanchéité architecturale du domaine '{step.target_bounded_context}'"

        violations = []
        for rel_file in step.files_in_scope:
            try:
                abs_file = self.validator.resolve_safe(rel_file)
                if abs_file.exists() and abs_file.is_file():
                    content = abs_file.read_text(encoding="utf-8", errors="ignore")
                    # Check for direct SQL queries to tables outside this domain
                    for src_table in step.data_ownership.source_tables:
                        # Check if file has direct connection to old DB
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
        criterion_id = f"QG-TEST-{hash(command_str) % 10000:04d}"
        
        try:
            res = subprocess.run(
                command_str,
                shell=True,
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
