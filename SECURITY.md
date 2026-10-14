# Security Policy

## Reporting Security Issues
We take code safety, permission boundaries, and credential privacy seriously. If you discover a vulnerability, please report it privately:

- **Security Contact**: `koudankomoise@gmail.com`
- Please include reproduction steps, environment details, and proof of concept.
- We will acknowledge receipt within 48 hours and coordinate a coordinated disclosure release.

## Security Guarantees & Surface Model
1. **Zero Unsolicited Network Calls**: By default, no network requests are sent. Code scanning and AST construction run exclusively in local memory.
2. **Secret Redaction**: Any text payload prepared for external LLM evaluation passes through the deterministic `SecretMasker` (stripping AWS keys, OpenAI/Anthropic/Gemini tokens, JWTs, database connection strings).
3. **No Shell Execution**: Commands are parsed with `shlex.split` and executed with `shell=False`. Arbitrary shell injection via input interpolation is architecturally prevented.
4. **Path Traversal Protection**: All paths are resolved with `os.path.normpath` and checked against the repository root boundary. Traversal attempts (e.g. `../../etc/passwd`) are rejected.
5. **Signed Plan Integrity**: Migration plans are cryptographically sealed with a canonical SHA-256 hash. Modification of plans after approval prevents execution.
6. **Task Memory Expiry**: Facts and table assumptions tied to files cryptographically expire if the target file has been modified.
