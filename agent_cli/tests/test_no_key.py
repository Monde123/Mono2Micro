"""Tests for G8: graceful no-key behavior when LLM credentials are absent."""

import os
from mono2micro.llm.client import resolve_api_key, build_client_from_specs
from mono2micro.config import UserSpecifications
from mono2micro.models.benchmarks import BenchmarkBaselineMode, BenchmarkCorpusItem, BenchmarkRunResult


def test_no_key_behavior(monkeypatch):
    """G8: When no API key is provided, LLM helper returns None and does not crash."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert resolve_api_key("gemini") is None
    assert resolve_api_key("openai") is None
    assert resolve_api_key("anthropic") is None

    specs = UserSpecifications(llm_provider="gemini")
    client = build_client_from_specs(specs, ask_key=False)
    assert client is None


def test_no_key_benchmark_mode():
    """G8: LLM benchmark modes without key produce NOT_RUN status with no metric numbers."""
    from benchmarks.runner import BenchmarkRunner
    from benchmarks.corpus import OFFICIAL_CORPUS

    runner = BenchmarkRunner(results_dir="/tmp/bench_test")
    item = list(OFFICIAL_CORPUS.values())[0]

    # Without API key, LLM_ONLY_NO_TOOLS must return NOT_RUN
    res = runner.evaluate_corpus_item(item, BenchmarkBaselineMode.LLM_ONLY_NO_TOOLS)
    assert res.status == "NOT_RUN"
    assert res.modularity_q is None
    assert res.tokens_consumed is None
    assert res.cost_usd is None
