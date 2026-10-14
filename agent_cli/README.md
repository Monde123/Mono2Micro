# Mono2Micro Python CLI (`agent_cli`)

> **Local command-line engineering agent** for empirical monolith-to-microservice migration and modularization, based on Hammad et al. (2023) ([alphaXiv:2306.08851](https://www.alphaxiv.org/abs/2306.08851)).

---

## Installation
```bash
cd agent_cli
pip install -e .
```

Verify installation:
```bash
mono2micro --help
# or
agent --help
```

---

## Core Commands
- `mono2micro doctor`: System diagnostics, capability matrix, and prompt injection detection.
- `mono2micro analyze`: Read-only AST code and persistence discovery (0 execution).
- `mono2micro graph`: AST dependency graph, Louvain modularity clustering ($Q$), and schema export.
- `mono2micro plan`: Objective clarification and SHA-256 signed Strangler Fig roadmap.
- `mono2micro test-plan`: Devil's advocate challenge, data boundary check, and test preparation.
- `mono2micro approve`: Signs and records human approval in immutable JSONL trail.
- `mono2micro apply`: Controlled codemod application on isolated Git branch with full diff review.
- `mono2micro verify`: Enforces strict binary Quality Gate with authorized user tests.
- `mono2micro audit`: Inspects `.mono2micro/audit.jsonl` audit records.
- `mono2micro bench`: Runs empirical 6-corpus ablation benchmark suite.

---

## Security Model
- **Offline First**: All analysis, graphs, planning, and verification execute offline without an API key.
- **Zero Shell Injection**: Subprocesses run with `shell=False` and tokenized commands.
- **Secret Redaction**: Sensitive API tokens, JWTs, and database passwords are masked deterministically.
- **Tamper Protection**: Plans are cryptographically signed with SHA-256 canonical hashes.
