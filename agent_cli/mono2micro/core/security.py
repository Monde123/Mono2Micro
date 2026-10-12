"""Security, sandboxing, path isolation and secret redaction engine.

Enforces:
- Treat repository files and scripts as UNTRUSTED data.
- Strict secret redaction: LLM API keys and repo credentials never leak.
- Path traversal prevention.
- Privacy filtering for transmissions to user-configured LLM providers.
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from enum import Enum


class PathTraversalError(Exception):
    """Raised when a file path escapes the designated workspace directory."""
    pass


class PrivacyLevel(str, Enum):
    METADATA_ONLY = "METADATA_ONLY"            # Only file paths, AST counts, framework names
    ANONYMIZED_SYMBOLS = "ANONYMIZED_SYMBOLS"  # Function/class signatures, stripped comments & literals
    FULL_CODE_REDACTED = "FULL_CODE_REDACTED"  # Full code snippets with rigorous regex secret redaction


class SecretMasker:
    """Detects and masks sensitive credentials, tokens, and keys."""

    SECRET_PATTERNS = [
        # OpenAI keys
        (re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_OPENAI_KEY]"),
        # Google AI / GCP API keys
        (re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), "[REDACTED_GEMINI_KEY]"),
        # Anthropic keys
        (re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_ANTHROPIC_KEY]"),
        # AWS Access Keys
        (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_ACCESS_KEY]"),
        # GitHub Personal Access Tokens
        (re.compile(r"gh[pousr]_[0-9a-zA-Z]{36,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
        # Generic Bearer tokens
        (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), "Bearer [REDACTED_BEARER_TOKEN]"),
        # Passwords in database URIs: postgres://user:pass@host:5432/db
        (re.compile(r"://([^:]+):([^@]+)@", re.IGNORECASE), r"://\1:[REDACTED_DB_PASSWORD]@"),
        # Generic Secret / Password env vars
        (re.compile(r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'), r'\1="[REDACTED_VALUE]"'),
    ]

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Redact all recognized sensitive token patterns."""
        if not text:
            return text
        sanitized = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


class SafePathValidator:
    """Validates that all accessed paths strictly reside inside the target root."""

    def __init__(self, base_directory: str):
        self.base_path = Path(base_directory).resolve()

    def resolve_safe(self, relative_or_absolute_path: str) -> Path:
        """Resolve path and verify it stays inside base_directory."""
        candidate = (self.base_path / relative_or_absolute_path).resolve()
        
        # Check boundary
        try:
            candidate.relative_to(self.base_path)
        except ValueError:
            raise PathTraversalError(
                f"TENTATIVE D'ÉVASION DÉTECTÉE: Le chemin '{relative_or_absolute_path}' sort du périmètre autorisé '{self.base_path}'"
            )
        
        return candidate

    def is_safe(self, path_str: str) -> bool:
        """Check if path is safe without throwing."""
        try:
            self.resolve_safe(path_str)
            return True
        except PathTraversalError:
            return False


class PrivacyFilter:
    """Prepares payload before any external LLM call according to user's privacy policy."""

    def __init__(self, privacy_level: PrivacyLevel = PrivacyLevel.FULL_CODE_REDACTED):
        self.privacy_level = privacy_level

    def sanitize_snippet(self, code_snippet: str, file_path: str) -> str:
        """Apply privacy rules based on selected privacy level."""
        if not code_snippet:
            return ""

        # Step 1: Always apply secret masker regardless of level
        redacted = SecretMasker.mask_text(code_snippet)

        if self.privacy_level == PrivacyLevel.METADATA_ONLY:
            return f"[CONTENU MASQUÉ PAR POLITIQUE METADATA_ONLY: {file_path} - {len(code_snippet.splitlines())} lignes]"

        if self.privacy_level == PrivacyLevel.ANONYMIZED_SYMBOLS:
            # Strip string literals and comments to avoid transmitting proprietary data
            no_strings = re.sub(r'".*?"|\'.*?\'', '""', redacted)
            no_comments = re.sub(r'#.*|//.*', '', no_strings)
            return no_comments

        return redacted
