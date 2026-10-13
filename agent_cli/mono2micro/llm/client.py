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
from typing import Callable, Optional

from mono2micro.core.security import SecretMasker


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


class LLMClient(ABC):
    """Single-turn completion interface used by all agents."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's text reply for a system + user prompt."""


class HTTPLLMClient(LLMClient):
    def __init__(self, config: LLMConfig, api_key: Optional[str], max_retries: int = 2):
        if config.provider not in SUPPORTED_PROVIDERS:
            raise LLMError(
                f"Fournisseur inconnu '{config.provider}'. Choix : {', '.join(SUPPORTED_PROVIDERS)}."
            )
        is_local_compatible = (
            config.provider == "openai"
            and config.base_url.rstrip("/") != DEFAULT_BASE_URLS["openai"]
        )
        if not api_key and not is_local_compatible:
            raise LLMError(
                f"Aucune clé API pour '{config.provider}'. Définissez la variable "
                f"d'environnement {API_KEY_ENV[config.provider]}."
            )
        self.config = config
        self._api_key = api_key or ""
        self._max_retries = max_retries

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
            raise LLMError(f"Réponse inattendue du fournisseur '{self.config.provider}'.") from exc

    # ---- transport ------------------------------------------------------------

    def _scrub(self, text: str) -> str:
        if self._api_key:
            text = text.replace(self._api_key, "[REDACTED_KEY]")
        return SecretMasker.mask_text(text)

    def complete(self, system: str, user: str) -> str:
        last_error = "erreur inconnue"
        for attempt in range(self._max_retries + 1):
            request = self._build_request(system, user)
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout) as resp:
                    return self._parse(json.loads(resp.read().decode("utf-8")))
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
                last_error = self._scrub(f"Erreur réseau : {exc}")
                if attempt == self._max_retries:
                    break
            except json.JSONDecodeError as exc:
                raise LLMError("Réponse du fournisseur non JSON.") from exc
            time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"Appel LLM échoué ({self.config.provider}) : {last_error}")


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
        raise LLMError(f"Fournisseur inconnu '{provider}'. Choix : {', '.join(SUPPORTED_PROVIDERS)}.")
    chosen_model = model or DEFAULT_MODELS.get(provider)
    if not chosen_model:
        raise LLMError(
            f"Aucun modèle défini pour '{provider}'. Utilisez : agent config --llm-model <nom-du-modèle>."
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
        api_key = (prompt_fn(f"Clé API {provider} (saisie masquée, non enregistrée) : ") or "").strip() or None

    return build_client(
        provider=provider,
        model=getattr(specs, "llm_model", None),
        base_url=getattr(specs, "llm_base_url", None),
        api_key=api_key,
    )
