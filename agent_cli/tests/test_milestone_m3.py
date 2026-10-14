"""Milestone 3 (M3) Tests: Empirical Benchmark Corpus & Scoring Protocol."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from mono2micro.cli import app
from mono2micro.models.benchmarks import BenchmarkBaselineMode
from benchmarks.corpus import OFFICIAL_CORPUS
from benchmarks.runner import BenchmarkRunner


runner = CliRunner()


def test_m3_corpus_integrity_and_pinned_commits():
    assert len(OFFICIAL_CORPUS) == 6
    required_projects = ["jpetstore-6", "daytrader-7", "acmeair-nodejs", "plants-by-websphere", "ecommerce-fastapi", "taskhub-express"]
    for p in required_projects:
        assert p in OFFICIAL_CORPUS
        item = OFFICIAL_CORPUS[p]
        # Pinned commit must be SHA
        assert len(item.pinned_commit) == 40

    # Verify ground truth vs surrogate metric honesty
    assert OFFICIAL_CORPUS["jpetstore-6"].has_ground_truth is True
    assert OFFICIAL_CORPUS["ecommerce-fastapi"].has_ground_truth is False
    assert len(OFFICIAL_CORPUS["ecommerce-fastapi"].surrogate_metrics_used) > 0


def test_m3_ablation_baselines_run(tmp_path):
    bench_runner = BenchmarkRunner(results_dir=str(tmp_path))
    report = bench_runner.run_suite()

    # 6 corpus projects * 3 baselines = 18 runs
    assert len(report.corpus_runs) == 18

    # Check that heuristic-only consumes zero tokens
    heuristic_runs = [r for r in report.corpus_runs if r.baseline_mode == BenchmarkBaselineMode.HEURISTIC_ONLY]
    assert all(r.tokens_consumed == 0 for r in heuristic_runs)
    assert all(r.cost_usd == 0.0 for r in heuristic_runs)

    # Check outputs created
    latest_json = tmp_path / "latest_results.json"
    latest_md = tmp_path / "README.md"
    assert latest_json.exists()
    assert latest_md.exists()

    with open(latest_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "corpus_runs" in data
    assert len(data["corpus_runs"]) == 18


def test_m3_cli_bench_and_doctor_commands(tmp_path):
    res_bench = runner.invoke(app, ["bench", "--output", str(tmp_path)])
    assert res_bench.exit_code == 0
    assert "Benchmark completed successfully" in res_bench.stdout

    res_doc = runner.invoke(app, ["doctor"])
    assert res_doc.exit_code == 0
    assert "Command Capability Matrix" in res_doc.stdout
    assert "Offline mode" in res_doc.stdout
