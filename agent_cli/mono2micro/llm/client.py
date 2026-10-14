"""Minimal HTTP clients for OpenAI-compatible, Anthropic and Gemini APIs.

Design rules:
- The API key is supplied by the user (environment variable or hidden prompt).
  It is NEVER written to disk, to .mono2micro/, to reports or to logs.
- Standard library only (urllib): no extra dependency, no vendor SDK lock-in.
- 'openai' also covers any OpenAI-compatible server (Ollama, vLLM, OpenRouter,
  Groq, ...) through a custom base URL; local servers may run without a key.
"""

import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Dict, Any




SUPPORTED_PROVIDERS = ("openai", "anthropic", "gemini")

API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
}

# Model names change quickly: only Anthropic has a default; for the other
# providers the user must choose the model explicitly (config --llm-model).
DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5"}

ANTHROPIC_VERSION = "2023-06-01"
RETRYABLE_STATUS = {429, 500, 502, 503, 529}


class LLMError(RuntimeError):
    """Any failure while configuring or calling the language model."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str
    max_tokens: int = 4096
    timeout: float = 120.0


from mono2micro.llm.pricing import LLMUsage, calculate_cost


class LLMClient(ABC):
    """Single-turn completion interface used by all agents."""

    last_usage: Optional[LLMUsage] = None

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's text reply for a system + user prompt."""

    def complete_with_usage(self, system: str, user: str) -> Tuple[str, LLMUsage]:
        """Return text reply alongside measured token usage and cost."""
        reply = self.complete(system, user)
        usage = self.last_usage or LLMUsage()
        return reply, usage


class HTTPLLMClient(LLMClient):
    def __init__(self, config: LLMConfig, api_key: Optional[str], max_retries: int = 2):
        if config.provider not in SUPPORTED_PROVIDERS:
            raise LLMError(
                f"Unknown provider '{config.provider}'. Choices: {', '.join(SUPPORTED_PROVIDERS)}."
            )
        is_local_compatible = (
            config.provider == "openai"
            and config.base_url.rstrip("/") != DEFAULT_BASE_URLS["openai"]
        )
        if not api_key and not is_local_compatible:
            raise LLMError(
                f"No API key provided for '{config.provider}'. Set the environment variable "
                f"{API_KEY_ENV[config.provider]}."
            )
        self.config = config
        self._api_key = api_key or ""
        self._max_retries = max_retries
        self.last_usage: Optional[LLMUsage] = None

    def __repr__(self) -> str:  # never expose the key
        return f"HTTPLLMClient(provider={self.config.provider!r}, model={self.config.model!r}, key=***)"

    # ---- request construction -------------------------------------------------

    def _build_request(self, system: str, user: str):
        c = self.config
        base = c.base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}

        if c.provider == "openai":
            url = f"{base}/chat/completions"
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            cap_field = (
                "max_completion_tokens"
                if base == DEFAULT_BASE_URLS["openai"] else "max_tokens"
            )
            body = {
                "model": c.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                cap_field: c.max_tokens,
            }
        elif c.provider == "anthropic":
            url = f"{base}/v1/messages"
            headers["x-api-key"] = self._api_key
            headers["anthropic-version"] = ANTHROPIC_VERSION
            body = {
                "model": c.model,
                "max_tokens": c.max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        else:  # gemini: key in a header, never in the URL
            url = f"{base}/v1beta/models/{c.model}:generateContent"
            headers["x-goog-api-key"] = self._api_key
            body = {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": c.max_tokens},
            }

        return urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
        )

    # ---- response parsing -----------------------------------------------------

    def _parse(self, data: dict) -> str:
        try:
            if self.config.provider == "openai":
                return data["choices"][0]["message"]["content"] or ""
            if self.config.provider == "anthropic":
                return "".join(
                    b.get("text", "") for b in data["content"] if b.get("type") == "text"
                )
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected response format from provider '{self.config.provider}'.") from exc

    def _parse_usage(self, data: dict) -> LLMUsage:
        c = self.config
        in_tok = 0
        out_tok = 0
        if c.provider == "openai":
            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)
        elif c.provider == "anthropic":
            usage = data.get("usage", {})
            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
        else:  # gemini
            usage = data.get("usageMetadata", {})
            in_tok = usage.get("promptTokenCount", 0)
            out_tok = usage.get("candidatesTokenCount", 0)

        tot_tok = in_tok + out_tok
        cost = calculate_cost(c.model, in_tok, out_tok)
        return LLMUsage(input_tokens=in_tok, output_tokens=out_tok, total_tokens=tot_tok, cost_usd=cost)

    # ---- transport ------------------------------------------------------------

    def _scrub(self, text: str) -> str:
        from mono2micro.core.security import SecretMasker  # lazy: avoids import cycle
        if self._api_key:
            text = text.replace(self._api_key, "[REDACTED_KEY]")
        return SecretMasker.mask_text(text)

    def complete_with_usage(self, system: str, user: str) -> Tuple[str, LLMUsage]:
        last_error = "unknown error"
        for attempt in range(self._max_retries + 1):
            request = self._build_request(system, user)
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout) as resp:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    text = self._parse(raw_data)
                    usage = self._parse_usage(raw_data)
                    self.last_usage = usage
                    return text, usage
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = exc.read().decode("utf-8", errors="ignore")[:300]
                except Exception:
                    pass
                last_error = self._scrub(f"HTTP {exc.code} {detail}".strip())
                if exc.code not in RETRYABLE_STATUS or attempt == self._max_retries:
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = self._scrub(f"Network error: {exc}")
                if attempt == self._max_retries:
                    break
            except json.JSONDecodeError as exc:
                raise LLMError("Provider response was not valid JSON.") from exc
            time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"LLM call failed ({self.config.provider}): {last_error}")

    def complete(self, system: str, user: str) -> str:
        text, _ = self.complete_with_usage(system, user)
        return text


# ---- factories ---------------------------------------------------------------

def resolve_api_key(provider: str, env: Optional[dict] = None) -> Optional[str]:
    """Read the user's key from the environment (never from project files)."""
    var = API_KEY_ENV.get(provider)
    if not var:
        return None
    value = (env if env is not None else os.environ).get(var, "").strip()
    return value or None


def build_client(
    provider: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 4096,
) -> LLMClient:
    provider = (provider or "").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise LLMError(f"Unknown provider '{provider}'. Choices: {', '.join(SUPPORTED_PROVIDERS)}.")
    chosen_model = model or DEFAULT_MODELS.get(provider)
    if not chosen_model:
        raise LLMError(
            f"No model defined for '{provider}'. Use: agent config --llm-model <model-name>."
        )
    config = LLMConfig(
        provider=provider,
        model=chosen_model,
        base_url=base_url or DEFAULT_BASE_URLS[provider],
        max_tokens=max_tokens,
    )
    return HTTPLLMClient(config, api_key or resolve_api_key(provider))


def build_client_from_specs(
    specs,
    ask_key: bool = False,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> Optional[LLMClient]:
    """Build a client from persisted settings, or None when no LLM is configured.

    The key comes from the environment; with ask_key=True it is requested through a
    hidden prompt and kept in memory for this run only.
    """
    provider = getattr(specs, "llm_provider", None)
    if not provider:
        return None
    provider = provider.lower()

    api_key = resolve_api_key(provider)
    if not api_key and ask_key:
        if prompt_fn is None:
            import getpass
            prompt_fn = getpass.getpass
        api_key = (prompt_fn(f"API key for {provider} (hidden input, never saved to disk): ") or "").strip() or None

    return build_client(
        provider=provider,
        model=getattr(specs, "llm_model", None),
        base_url=getattr(specs, "llm_base_url", None),
        api_key=api_key,
    )

