"""Tests for Security, SecretMasker and SafePathValidator."""

import pytest
import os
import tempfile
from mono2micro.core.security import (
    SecretMasker,
    SafePathValidator,
    PathTraversalError,
    PrivacyLevel,
    PrivacyFilter,
)


def test_secret_masker_openai():
    raw = 'const key = "sk-abcdef1234567890abcdef1234567890";'
    masked = SecretMasker.mask_text(raw)
    assert "sk-" not in masked
    assert "[REDACTED_OPENAI_KEY]" in masked


def test_secret_masker_gemini_and_aws():
    raw = 'GEMINI_KEY = "AIzaSyD1234567890abcdefghijklmnopqrstuv" and AWS_KEY="AKIAIOSFODNN7EXAMPLE"'
    masked = SecretMasker.mask_text(raw)
    assert "AIza" not in masked
    assert "[REDACTED_GEMINI_KEY]" in masked
    assert "AKIA" not in masked
    assert "[REDACTED_AWS_ACCESS_KEY]" in masked


def test_secret_masker_database_password():
    raw = 'DATABASE_URL="postgres://admin:super_secret_password_99@localhost:5432/proddb"'
    masked = SecretMasker.mask_text(raw)
    assert "super_secret_password_99" not in masked
    assert "[REDACTED_DB_PASSWORD]" in masked
    assert "postgres://admin:[REDACTED_DB_PASSWORD]@localhost:5432/proddb" in masked


def test_safe_path_validator_within_boundary():
    with tempfile.TemporaryDirectory() as temp_dir:
        validator = SafePathValidator(temp_dir)
        safe_path = validator.resolve_safe("src/module/service.py")
        assert safe_path.is_relative_to(validator.base_path)
        assert validator.is_safe("nested/dir/file.txt") is True


def test_safe_path_validator_blocks_traversal():
    with tempfile.TemporaryDirectory() as temp_dir:
        validator = SafePathValidator(temp_dir)
        
        with pytest.raises(PathTraversalError):
            validator.resolve_safe("../../../etc/passwd")

        with pytest.raises(PathTraversalError):
            validator.resolve_safe("..")

        assert validator.is_safe("../../secret.env") is False


def test_privacy_filter_metadata_only():
    filter_ = PrivacyFilter(PrivacyLevel.METADATA_ONLY)
    code = "function transferMoney(from, to, amount) { debit(from, amount); credit(to, amount); }"
    out = filter_.sanitize_snippet(code, "services/bank.js")
    assert "transferMoney" not in out
    assert "[CONTENU MASQUÉ PAR POLITIQUE METADATA_ONLY" in out


def test_privacy_filter_anonymized_symbols():
    filter_ = PrivacyFilter(PrivacyLevel.ANONYMIZED_SYMBOLS)
    code = 'def get_user():\n    # Confidential client comment\n    return "SuperSecretClientName"'
    out = filter_.sanitize_snippet(code, "user.py")
    assert "Confidential client comment" not in out
    assert "SuperSecretClientName" not in out
    assert "def get_user():" in out
