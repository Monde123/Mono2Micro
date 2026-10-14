# Contributing to Mono2Micro

Thank you for your interest in contributing to Mono2Micro! We welcome contributions that uphold empirical rigor, safety guarantees, and scientific honesty.

## Core Tenets
1. **Offline by Default**: Every core feature (discovery, dependency graphs, Louvain modularity, Strangler planning, codemods, verification) MUST work 100% offline without any API key or network access.
2. **Honesty & Ground Truth**: Never fabricate benchmark results. If ground truth is unavailable for a repository, declare surrogate metrics explicitly.
3. **Strict Quality Gates**: Changes must have unit tests, clean typing, and pass `make test` and `make bench`.
4. **Adversarial Safety**: Model outputs are untrusted inputs; every modification must be bounded, reviewed, and reversible.

## Development Setup
```bash
# Clone the repository
git clone https://github.com/mono2micro/mono2micro.git
cd mono2micro

# Install python dependencies in editable mode
pip install -e agent_cli

# Run tests
make test

# Run benchmark suite
make bench
```

## Pull Request Lifecycle
- Small, focused commits with clear titles.
- Each PR must include tests demonstrating acceptance criteria.
- Reviewers evaluate structural safety, memory leaks, and boundary isolation.
