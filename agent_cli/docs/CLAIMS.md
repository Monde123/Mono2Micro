# Mono2Micro Claims Ledger & Empirical Verification

This document records all architectural claims made by Mono2Micro and their empirical verification status.

## Claims Summary

| Claim ID | Claim Description | Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **CLM-01** | AST Parser detects untracked dynamic dependencies (`getattr`, `importlib.import_module`, `__import__`). | **VERIFIED** | Unit tests in `agent_cli/tests/test_dynamic.py` passing. |
| **CLM-02** | Benchmark runner evaluates official corpus with zero hardcoded simulated metrics. | **VERIFIED** | Verified by `scripts/verify_work.py` (G1, G2, G3). |
| **CLM-03** | Fix loop tracks actual token usage, API cost, and duration without static simulation defaults. | **VERIFIED** | Unit tests in `agent_cli/tests/test_milestone_m4.py` passing. |
| **CLM-04** | All source code, documentation, reports, and CLI messages are fully localized in English. | **VERIFIED** | Verified by localization audit and compliance checks. |
