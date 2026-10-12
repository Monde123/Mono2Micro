"""Tests for CLI Typer commands."""

import tempfile
from pathlib import Path
from typer.testing import CliRunner
from mono2micro.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout
    assert "plan" in result.stdout
    assert "test-plan" in result.stdout
    assert "apply" in result.stdout
    assert "verify" in result.stdout


def test_cli_analyze_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text('{"dependencies": {"express": "4.18.2"}}', encoding="utf-8")

        result = runner.invoke(app, ["analyze", "--path", tmp])
        assert result.exit_code == 0
        assert "Inventaire Factuel du Dépôt" in result.stdout
        assert "Express.js" in result.stdout
        assert "Faits Empiriques Vérifiés" in result.stdout


def test_cli_plan_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text('{"dependencies": {"express": "4.18.2"}}', encoding="utf-8")

        result = runner.invoke(app, ["plan", "--path", tmp, "--goal", "CODEBASE_MODULARITY", "--team-size", "2"])
        assert result.exit_code == 0
        assert "Analyse des Domaines Métier" in result.stdout
        assert "Comparatif des 4 Trajectoires Architecturales" in result.stdout
        assert "MODULAR_MONOLITH" in result.stdout


def test_cli_test_plan_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text('{"dependencies": {"express": "4.18.2"}}', encoding="utf-8")

        result = runner.invoke(app, ["test-plan", "--path", tmp, "--step", "1"])
        assert result.exit_code == 0
        assert "Intervention du Sous-Agent Contradicteur" in result.stdout
        assert "Scénarios de Tests Indépendants" in result.stdout


def test_cli_verify_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text('{"dependencies": {"express": "4.18.2"}}', encoding="utf-8")

        result = runner.invoke(app, ["verify", "--path", tmp, "--step", "1", "--test-cmd", "echo 'smoke test passed'"])
        assert result.exit_code == 0
        assert "QUALITY GATE" in result.stdout
        assert "Rapport complet exporté dans" in result.stdout
