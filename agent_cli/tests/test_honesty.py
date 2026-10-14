"""Honesty and anti-simulation contract tests.

Verifies that no simulated numbers, forbidden offsets, or unverified claims
exist in the repository.
"""

import os
import re
import json
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FORBIDDEN_FILES = [
    "agent_cli/benchmarks/runner.py",
    "agent_cli/mono2micro/migration/fix_loop.py",
]

FORBIDDEN_PHRASES = [
    "simulated",
    "mocked results",
    "+ 0.05",
]

METRIC_FIELDS = [
    "modularity_q",
    "coupling_ratio",
    "tokens",
    "cost",
    "false_block_rate",
    "tokens_per_attempt",
    "cost_per_attempt",
]


def test_no_forbidden_phrases():
    """G1: runner.py and fix_loop.py must not contain simulation markers."""
    for rel_path in FORBIDDEN_FILES:
        full_path = os.path.join(ROOT_DIR, rel_path)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in content, f"Forbidden phrase '{phrase}' found in {rel_path}"


def test_no_hardcoded_metric_constants():
    """G1: Metric fields must not be assigned numeric literals."""
    for rel_path in FORBIDDEN_FILES:
        full_path = os.path.join(ROOT_DIR, rel_path)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        for field in METRIC_FIELDS:
            # Pattern: field = 0.123 or field=123 (excluding default params like 0 or None)
            matches = re.findall(rf"\b{field}\b\s*=\s*([0-9]+\.?[0-9]*)", content)
            for m in matches:
                # Allowed defaults are 0 or 0.0
                if m not in ("0", "0.0"):
                    pytest.fail(f"Hardcoded metric value {field}={m} found in {rel_path}")


def test_claims_ledger_honesty():
    """G4: docs/CLAIMS.md must exist and have zero UNVERIFIED entries."""
    claims_path = os.path.join(ROOT_DIR, "docs/CLAIMS.md")
    assert os.path.exists(claims_path), "docs/CLAIMS.md must exist"
    with open(claims_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "UNVERIFIED" not in content, "docs/CLAIMS.md must not contain UNVERIFIED"


def test_results_json_schema():
    """G2: Every cell in latest_results.json must have valid status and provenance."""
    results_path = os.path.join(ROOT_DIR, "benchmarks/results/latest_results.json")
    if not os.path.exists(results_path):
        pytest.skip("latest_results.json not yet generated")
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("results", [data])
    for item in items:
        status = item.get("status")
        assert status in ("MEASURED", "NOT_RUN", "UNAVAILABLE"), f"Invalid status {status}"
        if status == "MEASURED":
            assert item.get("n"), "MEASURED cell missing n"
            assert item.get("raw_output_path"), "MEASURED cell missing raw_output_path"
            assert item.get("tool_commit"), "MEASURED cell missing tool_commit"
        if status == "NOT_RUN":
            assert "modularity_q" not in item or item["modularity_q"] is None, "NOT_RUN cell must not hold numbers"
