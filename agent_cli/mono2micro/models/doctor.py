"""Diagnostics, capability matrix, and prompt injection scanning models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CommandCapability(BaseModel):
    command: str
    offline_capability: str
    llm_accelerated_capability: str
    requires_api_key: bool = False
    local_model_supported: bool = True


class DoctorReport(BaseModel):
    python_version: str
    is_git_repository: bool
    configured_provider: Optional[str] = None
    has_active_api_key: bool
    is_offline_ready: bool = True
    capabilities: List[CommandCapability] = Field(default_factory=list)
    prompt_injection_warnings: List[str] = Field(default_factory=list)
