# Known Limitations & Experimental Scope

In accordance with our core tenet of empirical honesty, this document enumerates current limitations, edge cases, and experimental components of Mono2Micro.

## Current Technical Limitations
1. **Dynamic Reflection & Runtime Dependency Injection**:
   - In languages utilizing dynamic runtime reflection (e.g., dynamic Spring bean lookup or Python `getattr`/`importlib`), static AST parsing cannot guarantee 100% edge discovery. Such calls are marked as untracked dynamic dependencies.
2. **Distributed Transaction Decomposition (2PC / Sagas)**:
   - While cross-domain transactions spanning multiple database tables are detected and flagged as blocking risks, automated decomposition into distributed Saga orchestrators or Transactional Outbox patterns is currently marked **[EXPERIMENTAL]** and requires manual architect review.
3. **Database Migration Scripts**:
   - DDL splitting for PostgreSQL, MySQL, and SQLite dialects is supported deterministically. Stored procedures, triggers, and complex database-level functions are not automatically refactored and require developer intervention.
4. **LLM Context Window Ceilings**:
   - For monolith codebases exceeding 500,000 lines of code, full-code LLM prompts are chunked per bounded context. The agent relies primarily on offline AST dependency graphs and Louvain modularity to partition large repositories without sending whole codebases over the network.
5. **Polyglot Monorepos**:
   - Repositories containing mixed micro-frontends and multiple backend languages in a single subfolder may require explicit configuration in `.mono2micro/user_specifications.json`.

## Experimental Features
Features marked as `[EXPERIMENTAL]` are under active research and subject to refinement:
- Multi-region distributed routing generation
- Automatic saga compensation handler generation
- Autonomous multi-turn test repair on dynamic typing failures beyond 3 attempts
