"""Provider-agnostic LLM access using a user-supplied API key."""

from mono2micro.llm.client import (
    LLMClient,
    LLMConfig,
    LLMError,
    HTTPLLMClient,
    SUPPORTED_PROVIDERS,
    API_KEY_ENV,
    build_client,
    build_client_from_specs,
    resolve_api_key,
)
from mono2micro.llm.json_utils import extract_json

__all__ = [
    "LLMClient", "LLMConfig", "LLMError", "HTTPLLMClient",
    "SUPPORTED_PROVIDERS", "API_KEY_ENV",
    "build_client", "build_client_from_specs", "resolve_api_key",
    "extract_json",
]
