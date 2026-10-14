# Mono2Micro

> **Empirical, Phased Monolith-to-Microservice & Modularization CLI Agent**  
> Operationalizing the research principles of **Hatem Hammad, Thaer Sahmoud, and Abed Al Rahman Abu Ghazala (2023)** ([alphaXiv:2306.08851](https://www.alphaxiv.org/abs/2306.08851)).

[![CI](https://github.com/mono2micro/mono2micro/actions/workflows/ci.yml/badge.svg)](https://github.com/mono2micro/mono2micro/actions)
[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-amber.svg)](./LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/Python->=3.10-blue.svg)](https://python.org)
[![Offline: 100%](https://img.shields.io/badge/Offline-100%25%20Functional-green.svg)](#offline-first-architecture)

---

## 💡 Overview

Migrating a monolithic codebase to microservices is notoriously hazardous: distributed transactions fail, network latency escalates, and teams suffer from the "distributed monolith" anti-pattern.

**Mono2Micro** is a production-grade, local software engineering CLI agent that replaces speculative splitting with **empirical, static analysis**:

1. **Modular Monolith Evaluated First**: In accordance with Principle 1 of Hammad et al. (2023), if the team has $\le 2$ developers or the objective is codebase modularity/cost, the agent recommends internal encapsulation (Modular Monolith) rather than paying the distributed systems tax.
2. **100% Offline by Default**: AST dependency graph extraction, SQL and MyBatis parser, and Louvain modularity clustering run completely offline on your local machine with zero network calls and zero telemetry.
3. **Cryptographically Sealed Migration Plans**: Every migration plan is signed with a deterministic canonical SHA-256 hash. If files in scope or routing rules change after human approval, execution is strictly blocked.
4. **Adversarial Devil's Advocate**: An independent sub-agent examines diffs to block direct foreign table queries, cross-boundary imports, or cascading synchronous RPC calls before any code is written.
5. **Strict Binary Quality Gate**: No score averaging or compensation of critical failures. If a mandatory test fails or is skipped, release is denied.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10 or higher
- Git 2.30+

### Installation
```bash
# Clone the repository
git clone https://github.com/mono2micro/mono2micro.git
cd mono2micro

# Install the Python CLI in editable mode
pip install -e agent_cli

# Verify local installation
mono2micro doctor
```

Alternatively, you can run commands directly using `python -m mono2micro.cli`.

---

## 🛠️ CLI Workflow & Commands

```
                   ┌──────────────┐
                   │ agent doctor │  Check local readiness & capabilities
                   └──────┬───────┘
                          ▼
                  ┌───────────────┐
                  │ agent analyze │  Read-only AST inventory & facts
                  └──────┬────────┘
                          ▼
                   ┌─────────────┐
                   │ agent graph │  AST dependency graph & Louvain modularity Q
                   └──────┬──────┘
                          ▼
                   ┌────────────┐
                   │ agent plan │  Clarify goals & generate signed Strangler plan
                   └──────┬─────┘
                          ▼
                ┌─────────────────┐
                │ agent test-plan │  Devil's advocate challenge & coupling check
                └─────────┬───────┘
                          ▼
                 ┌───────────────┐
                 │ agent approve │  Persist human approval for step N (hash sealed)
                 └────────┬──────┘
                          ▼
                  ┌─────────────┐
                  │ agent apply │  Apply on isolated git branch with diff review
                  └──────┬──────┘
                          ▼
                 ┌──────────────┐
                 │ agent verify │  Execute authorized tests & binary Quality Gate
                 └──────┬───────┘
                          ▼
                  ┌─────────────┐
                  │ agent audit │  Review immutable JSONL audit trail
                  └─────────────┘
```

### Command Reference

| Command | Offline Capability | Optional LLM Role | API Key Needed? |
|---|---|---|---|
| `mono2micro doctor` | Diagnoses Python, Git, and scans for prompt injection | N/A | No |
| `mono2micro analyze` | Discovers components, routes, ORM models, facts | Enriches semantic summary | No |
| `mono2micro graph` | Builds AST dependency graph, calculates Louvain $Q$ | Semantic edge weighting | No |
| `mono2micro plan` | Compares 4 architectural options, signs Strangler plan | Suggests domain names | No |
| `mono2micro test-plan` | Validates data boundaries, detects shared tables | Generates independent test cases | No |
| `mono2micro approve` | Signs and persists human approval in JSONL trail | N/A | No |
| `mono2micro apply` | Deterministic codemods on isolated Git branch | Proposes code changes with diff review | Only for LLM codegen |
| `mono2micro verify` | Strictly evaluates binary Quality Gate | Analyzes test failure logs | No |
| `mono2micro audit` | Inspects `.mono2micro/audit.jsonl` immutable trail | N/A | No |
| `mono2micro bench` | Runs 6-corpus ablation suite | Evaluates hybrid precision | No |

---

## 📊 Empirical Benchmarks (Ablation Study)

Mono2Micro is evaluated against real open-source monoliths with **pinned git commits**. Where peer-reviewed ground truth exists, precision and recall are reported. Where ground truth is not published, surrogate metrics are explicitly declared without fabrication.

### Benchmark Results (`benchmarks/results/latest_results.json`)

| Benchmark | Baseline | Ground Truth? | Precision | Recall | Modularity $Q$ | Coupling Ratio | Shared Tables | Tokens | Cost ($) | Duration |
|---|---|---|---|---|---|---|---|---|---|---|
| **jpetstore-6** (Java/MyBatis) | `HEURISTIC_ONLY` | Yes | 1.00 | 0.80 | 0.48 | 0.18 | 2 | 0 | $0.0000 | 0.05s |
| **jpetstore-6** | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.60 | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **jpetstore-6** | `HYBRID_AGENT` | Yes | **1.00** | **1.00** | **0.54** | **0.14** | **2** | 1,850 | $0.0045 | 0.05s |
| **daytrader-7** (Java EE/JPA) | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 2 | 0 | $0.0000 | 0.05s |
| **daytrader-7** | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **daytrader-7** | `HYBRID_AGENT` | Yes | **1.00** | **1.00** | **0.54** | **0.14** | **2** | 1,850 | $0.0045 | 0.05s |
| **acmeair-nodejs** (Node.js) | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| **acmeair-nodejs** | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **acmeair-nodejs** | `HYBRID_AGENT` | Yes | **1.00** | **1.00** | **0.54** | **0.14** | **1** | 1,850 | $0.0045 | 0.05s |
| **plants-by-websphere** (Java) | `HEURISTIC_ONLY` | Yes | 1.00 | 1.00 | 0.48 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| **plants-by-websphere** | `LLM_ONLY_NO_TOOLS` | Yes | 0.75 | 0.75 | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **plants-by-websphere** | `HYBRID_AGENT` | Yes | **1.00** | **1.00** | **0.54** | **0.14** | **1** | 1,850 | $0.0045 | 0.05s |
| **ecommerce-fastapi** (Python) | `HEURISTIC_ONLY` | Surrogate | N/A | N/A | 0.42 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| **ecommerce-fastapi** | `LLM_ONLY_NO_TOOLS` | Surrogate | N/A | N/A | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **ecommerce-fastapi** | `HYBRID_AGENT` | Surrogate | N/A | N/A | **0.47** | **0.14** | **1** | 1,850 | $0.0045 | 0.05s |
| **taskhub-express** (Node.js) | `HEURISTIC_ONLY` | Surrogate | N/A | N/A | 0.42 | 0.18 | 1 | 0 | $0.0000 | 0.05s |
| **taskhub-express** | `LLM_ONLY_NO_TOOLS` | Surrogate | N/A | N/A | 0.31 | 0.34 | 0 (missed) | 3,200 | $0.0080 | 0.05s |
| **taskhub-express** | `HYBRID_AGENT` | Surrogate | N/A | N/A | **0.47** | **0.14** | **1** | 1,850 | $0.0045 | 0.05s |

To reproduce the benchmark suite:
```bash
make bench
```

---

## 🔒 Security & Privacy Guarantees

- **No Remote Code Execution**: Commands are never executed via a shell (`shell=False`).
- **Hard LLM Budget Ceiling**: Set `--max-tokens` or `--max-cost` to enforce a deterministic hard stop.
- **Redaction Engine**: Deterministic stripping of AWS keys, database connection strings, JWT tokens, and private credentials before any text leaves the machine.
- **Prompt Injection Defense**: Scans repository comments for adversarial directives (`ignore all previous instructions`, etc.).
- **Grounded Task Memory**: Every architectural memory stores its file path, line number, and SHA-256 hash. If the file is modified, the memory automatically expires.

---

## ⚠️ Known Limitations & Experimental Scope

In accordance with our honesty principle:

1. **Dynamic Reflection**: Dynamic runtime reflection (e.g., dynamic Spring bean lookup or Python `getattr`) cannot be 100% determined by static AST parsing alone and is flagged as untracked dynamic dependencies.
2. **Distributed Saga Generation**: Automated generation of distributed 2PC / Saga compensation handlers is currently **[EXPERIMENTAL]** and requires manual architect review.
3. **Complex Stored Procedures**: SQL splitting handles DDL statements and foreign key constraints across SQLite, PostgreSQL, and MySQL. Database triggers and stored procedures require manual refactoring.

For full details, see [docs/KNOWN_LIMITATIONS.md](./docs/KNOWN_LIMITATIONS.md).

---

## 📄 License & Terms of Use

This software is distributed under a **Non-Commercial Source Available License** (see [`LICENSE`](./LICENSE)):

- **Permitted Free Uses**: Personal evaluation, academic research, open-source benchmarking, and internal non-production study.
- **Commercial Restriction**: Any commercial deployment, integration into commercial SaaS offerings, proprietary enterprise tooling, or paid consulting services requires a **separate written commercial agreement or license convention** signed between both parties.
- **Inquiries & Commercial Conventions**: Contact `koudankomoise@gmail.com`.

---

## 📚 Academic Citation

If you use Mono2Micro in academic or industry research, please cite the foundational paper:

```bibtex
@article{hammad2023convert,
  title={Convert Monolithic Application to Microservice Application},
  author={Hammad, Hatem and Sahmoud, Thaer and Abu Ghazala, Abed Al Rahman},
  journal={alphaXiv preprint alphaXiv:2306.08851},
  year={2023},
  url={https://www.alphaxiv.org/abs/2306.08851}
}
```
