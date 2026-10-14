# Known Limitations & Technical Scope

In accordance with our core tenet of empirical honesty, this document enumerates current technical boundaries, parser capabilities, and experimental scope of Mono2Micro.

## Technical Boundaries & Implementations

1. **Parser Backends**:
   - Python code is parsed using Python's standard library `ast` module (real AST).
   - JavaScript, TypeScript, and Java files are analyzed using regex-based structural extraction for classes, methods, imports, and table annotations.
2. **Dynamic Reflection & Runtime Dependency Injection**:
   - In languages utilizing dynamic runtime reflection, static analysis cannot guarantee 100% edge discovery.
   - For Python, non-literal `getattr`, `importlib.import_module`, and `__import__` calls are detected, flagged as `untracked_dynamic=True`, and accounted for in graph analysis.
3. **Database Schema Extraction**:
   - Deterministic DDL table splitting is supported for standard `CREATE TABLE` definitions (compatible with PostgreSQL, MySQL, and SQLite syntax). Stored procedures, triggers, and proprietary procedural database extensions require manual intervention.
4. **Large Monolith Analysis**:
   - Analysis relies on local, offline static dependency graphs and Louvain modularity partitioning without sending full source code over the network.
5. **Distributed Transactions**:
   - Cross-domain transactions spanning multiple database tables are detected and flagged as architectural risks; automated decomposition into distributed Saga orchestrators is marked experimental.
