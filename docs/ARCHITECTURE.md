# Mono2Micro Architecture & Agent Topology

Mono2Micro implements the research principles published by Hatem Hammad, Thaer Sahmoud, and Abed Al Rahman Abu Ghazala (2023) in *Convert Monolithic Application to Microservice Application* ([alphaXiv:2306.08851](https://www.alphaxiv.org/abs/2306.08851)).

## Multi-Agent Architecture
Mono2Micro coordinates specialized sub-agents with strict separation of concerns:

```
                      ┌──────────────────────┐
                      │   LEAD ORCHESTRATOR  │
                      └──────────┬───────────┘
                                 │
     ┌──────────────┬────────────┼────────────┬──────────────┐
     ▼              ▼            ▼            ▼              ▼
┌──────────┐  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ ANALYZER │  │ ARCHITECT │ │ REVIEWER │ │ MIGRATOR │ │  BENCHMARKER │
└──────────┘  └───────────┘ └──────────┘ └──────────┘ └──────────────┘
```

1. **ANALYZER (`mono2micro/analysis/`)**:
   - Parses AST across Python, JavaScript/TypeScript, and Java.
   - Extracts module, class, and call dependency graph.
   - Extracts SQL queries, MyBatis XML mappers, and JPA `@Entity` definitions.
   - Computes Newman-Girvan Modularity $Q$ using Louvain community clustering.
   - Calculates inter-domain coupling ratio and identifies shared database tables.

2. **ARCHITECT (`mono2micro/agents/migration_architect.py`)**:
   - Compares the 4 architectural alternatives (Modular Monolith, Strangler Microservices, Serverless, Domain Microkernel).
   - Enforces Principle 1: if team size $\le 2$ or goal is modularity/cost, recommends the Modular Monolith to avoid the distributed systems tax.
   - Produces phased Strangler Fig migration plans sealed with SHA-256 canonical hashes.

3. **REVIEWER (`mono2micro/review/`)**:
   - Challenges every plan step before implementation.
   - Enforces adversarial diff review: blocks unauthorized cross-domain imports, direct foreign table accesses, and cascading synchronous RPC calls.
   - Maintains grounded task memory where each memory fragment retains its file path, line number, and SHA-256 hash. Invalidates memories automatically if target files are modified.

4. **MIGRATOR (`mono2micro/migration/`)**:
   - Applies deterministic AST/pattern codemods (function extraction, facade injection, gateway routing, feature flags).
   - Runs the Generate -> Test -> Fix loop (max 3 attempts).
   - If tests fail after 3 attempts, performs automatic repository rollback.

5. **VERIFIER (`mono2micro/agents/verifier.py`)**:
   - Enforces strict binary Quality Gates.
   - Forbids score averaging or compensating critical failures.
   - Executes authorized user test commands safely without shell injection.
