"""Mono2Micro Migration Subsystem (MIGRATOR Agent).

Provides:
- Deterministic AST / pattern codemods (extract, facade, gateway, flags)
- Generate -> Test -> Fix loop (max 3 attempts with automatic git restoration)
- Gateway routing & feature flag scaffolding
- Token, cost, and duration accounting
"""

from mono2micro.models.migration import (
    CodemodKind,
    CodemodResult,
    FixLoopAttempt,
    FixLoopSession,
    GatewayRouteConfig,
    FeatureFlagConfig,
)

__all__ = [
    "CodemodKind",
    "CodemodResult",
    "FixLoopAttempt",
    "FixLoopSession",
    "GatewayRouteConfig",
    "FeatureFlagConfig",
]
