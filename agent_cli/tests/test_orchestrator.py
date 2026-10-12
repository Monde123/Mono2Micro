"""Tests for MigrationOrchestrator full workflow execution."""

import tempfile
import pytest
from pathlib import Path
from mono2micro.core.orchestrator import MigrationOrchestrator
from mono2micro.models.objectives import MigrationGoalType
from mono2micro.models.options import ArchitectureOptionType


def test_orchestrator_lifecycle():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create minimal project layout
        (root / "package.json").write_text('{"name": "test-monolith", "dependencies": {"express": "^4.18.0"}}', encoding="utf-8")
        src = root / "src"
        src.mkdir()
        (src / "app.js").write_text('const express = require("express"); const app = express(); app.get("/api", (req, res) => res.send("ok"));', encoding="utf-8")

        orchestrator = MigrationOrchestrator(tmp)

        # 1. Discovery
        discovery = orchestrator.step_1_discover()
        assert discovery.total_files_scanned >= 2
        assert "Express.js" in discovery.frameworks_detected

        # 2. Clarify Objectives
        obj = orchestrator.step_2_clarify_objectives(
            primary_goal=MigrationGoalType.CODEBASE_MODULARITY,
            user_rationale="Simplify code organization",
            team_size=2
        )
        assert obj.can_be_solved_within_monolith is True

        # 3. Domains
        domains = orchestrator.step_3_analyze_domains()
        assert len(domains) >= 1

        # 4. Compare Options
        options = orchestrator.step_4_compare_options()
        assert options.recommended_option in (
            ArchitectureOptionType.MODULAR_MONOLITH,
            ArchitectureOptionType.POSTPONE_MIGRATION
        )

        # 5. Plan
        plan = orchestrator.step_5_plan_migration()
        assert len(plan.steps) >= 1

        # 6. Adversarial Review
        review = orchestrator.step_6_adversarial_review(step_number=1)
        assert review.target_step_number == 1
        assert len(review.independent_test_cases) >= 1

        # 7. Quality Gate with simulation
        qg = orchestrator.step_9_verify_quality_gate(step_number=1, authorized_commands=[
            ("echo 'Test ok'", "Simple verification smoke test")
        ])
        assert qg.overall_passed is True

        # 8. Report
        report = orchestrator.step_10_generate_report()
        assert report.target_project_path == tmp
        assert len(report.cited_paper_principles) == 7
        
        md = report.to_markdown()
        assert "Rapport d'Évolution Architecturale" in md
