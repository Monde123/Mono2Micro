"""Adversarial diff review and grounded task memory contracts.

Enforces M5:
- Adversarial rules on diff (out-of-scope imports, direct cross-domain table access, synchronous call chains)
- Grounded task memory: each memory keeps its proof (file, line, file_hash) and expires when the file changes.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from mono2micro.models.time_utils import utc_now


class AdversarialDiffRule(str, Enum):
    NEW_OUT_OF_SCOPE_IMPORT = "NEW_OUT_OF_SCOPE_IMPORT"
    DIRECT_CROSS_DOMAIN_TABLE_ACCESS = "DIRECT_CROSS_DOMAIN_TABLE_ACCESS"
    SYNCHRONOUS_CHAINED_RPC = "SYNCHRONOUS_CHAINED_RPC"
    CIRCULAR_DEPENDENCY_INTRODUCED = "CIRCULAR_DEPENDENCY_INTRODUCED"
    PROMPT_INJECTION_PATTERN_DETECTED = "PROMPT_INJECTION_PATTERN_DETECTED"


class AdversarialDiffViolation(BaseModel):
    rule: AdversarialDiffRule
    file_path: str
    line_number: Optional[int] = None
    severity: str = "BLOCKING"
    description: str
    code_excerpt: Optional[str] = None


class GroundedMemoryProof(BaseModel):
    file_path: str
    line_number: int
    content_sha256: str


class TaskMemoryItem(BaseModel):
    """A verified memory fragment with physical filesystem evidence."""
    memory_id: str
    key: str
    observation: str
    proof: GroundedMemoryProof
    created_at: datetime = Field(default_factory=utc_now)
    last_verified_at: datetime = Field(default_factory=utc_now)
    is_expired: bool = False
    expiry_reason: Optional[str] = None
