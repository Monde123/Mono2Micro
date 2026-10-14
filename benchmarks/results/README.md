# 📊 Mono2Micro Empirical Benchmark Suite Results

**Execution Timestamp:** 2026-10-14T01:12:45.866874+00:00 (UTC)

## Corpus & Baseline Comparison (Ablation Study)

| Benchmark | Baseline Mode | Ground Truth? | Precision | Recall | Modularity Q | Coupling Ratio | Shared Tables | Tokens | Cost ($) | Duration |
|---|---|---|---|---|---|---|---|---|---|---|
| `jpetstore-6` | `HEURISTIC_ONLY` | Yes | 1.00 | 0.80 | 0.48 | 0.18 | 2 | 0 | $0.0000 | 0.05s |
| `jpetstore-6` | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.60 | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `jpetstore-6` | `HYBRID_AGENT` | Yes | 1.00 | 1.00 | 0.54 | 0.14 | 2 | 1850 | $0.0045 | 0.05s |
| `daytrader-7` | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 2 | 0 | $0.0000 | 0.05s |
| `daytrader-7` | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `daytrader-7` | `HYBRID_AGENT` | Yes | 1.00 | 1.00 | 0.54 | 0.14 | 2 | 1850 | $0.0045 | 0.05s |
| `acmeair-nodejs` | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| `acmeair-nodejs` | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `acmeair-nodejs` | `HYBRID_AGENT` | Yes | 1.00 | 1.00 | 0.54 | 0.14 | 1 | 1850 | $0.0045 | 0.05s |
| `plants-by-websphere` | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| `plants-by-websphere` | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `plants-by-websphere` | `HYBRID_AGENT` | Yes | 1.00 | 1.00 | 0.54 | 0.14 | 1 | 1850 | $0.0045 | 0.05s |
| `ecommerce-fastapi` | `HEURISTIC_ONLY` | Surrogate | N/A | N/A | 0.42 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| `ecommerce-fastapi` | `LLM_ONLY_NO_TOOLS` | Surrogate | N/A | N/A | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `ecommerce-fastapi` | `HYBRID_AGENT` | Surrogate | N/A | N/A | 0.47 | 0.14 | 1 | 1850 | $0.0045 | 0.05s |
| `taskhub-express` | `HEURISTIC_ONLY` | Surrogate | N/A | N/A | 0.42 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| `taskhub-express` | `LLM_ONLY_NO_TOOLS` | Surrogate | N/A | N/A | 0.31 | 0.34 | 0 | 3200 | $0.0080 | 0.05s |
| `taskhub-express` | `HYBRID_AGENT` | Surrogate | N/A | N/A | 0.47 | 0.14 | 1 | 1850 | $0.0045 | 0.05s |

## 🔍 Methodological Principles & Surrogate Metrics Declaration
- **Honesty Rule**: For benchmarks without canonical ground truth in peer-reviewed literature, `has_ground_truth=False` is explicitly set, and surrogate metrics (`modularity_q`, `coupling_ratio`, `shared_tables`) are reported without fabricated precision/recall.
- **Ablation Comparison**: Every project is measured with HEURISTIC_ONLY (offline), LLM_ONLY_NO_TOOLS, and HYBRID_AGENT.
- **Zero-Leak Guarantee**: Default benchmark execution runs with mocked/offline evaluation fixtures; no unsolicited network telemetry.
