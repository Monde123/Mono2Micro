"""Tests for the LLM client layer (no real network access)."""

import io
import json
import urllib.error
import urllib.request

import pytest

from mono2micro.config import UserSpecifications
from mono2micro.llm import (
    HTTPLLMClient, LLMConfig, LLMError, build_client, build_client_from_specs,
    extract_json, resolve_api_key,
)

KEY = "sk-test-SECRETKEY1234567890abcdef"


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


@pytest.fixture
def capture(monkeypatch):
    seen = {}
    def fake(provider_payload):
        def _urlopen(req, timeout=None):
            seen["url"] = req.full_url
            seen["headers"] = {k.lower(): v for k, v in req.header_items()}
            seen["body"] = json.loads(req.data.decode())
            return _Resp(provider_payload)
        monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
        return seen
    monkeypatch.setattr("time.sleep", lambda s: None)
    return fake


def _client(provider, model="m", base_url=None, key=KEY):
    return build_client(provider, model=model, base_url=base_url, api_key=key)


def test_openai_request_and_parse(capture):
    seen = capture({"choices": [{"message": {"content": "hello"}}]})
    out = _client("openai").complete("sys", "usr")
    assert out == "hello"
    assert seen["url"].endswith("/v1/chat/completions")
    assert seen["headers"]["authorization"] == f"Bearer {KEY}"
    assert seen["body"]["messages"][0] == {"role": "system", "content": "sys"}
    assert "max_completion_tokens" in seen["body"]


def test_anthropic_request_and_parse(capture):
    seen = capture({"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]})
    out = _client("anthropic").complete("sys", "usr")
    assert out == "ab"
    assert seen["url"] == "https://api.anthropic.com/v1/messages"
    assert seen["headers"]["x-api-key"] == KEY
    assert seen["headers"]["anthropic-version"]
    assert seen["body"]["system"] == "sys"


def test_gemini_key_is_in_header_not_url(capture):
    seen = capture({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})
    out = _client("gemini", model="some-model").complete("sys", "usr")
    assert out == "ok"
    assert KEY not in seen["url"]
    assert seen["headers"]["x-goog-api-key"] == KEY


def test_local_openai_compatible_server_needs_no_key(capture):
    seen = capture({"choices": [{"message": {"content": "local"}}]})
    c = _client("openai", base_url="http://localhost:11434/v1", key=None)
    assert c.complete("s", "u") == "local"
    assert "authorization" not in seen["headers"]
    assert "max_tokens" in seen["body"]


def test_missing_key_for_hosted_provider_raises():
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        build_client("anthropic", api_key=None)


def test_model_required_when_no_default():
    with pytest.raises(LLMError, match="model"):
        build_client("openai", api_key=KEY)



def test_unknown_provider_rejected():
    with pytest.raises(LLMError):
        build_client("nope", model="x", api_key=KEY)


def test_http_error_never_leaks_key(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    def boom(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 401, "Unauthorized", {}, io.BytesIO(f"bad key {KEY}".encode()))
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(LLMError) as exc:
        _client("anthropic").complete("s", "u")
    assert KEY not in str(exc.value)


def test_retries_on_rate_limit_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = {"n": 0}
    def flaky(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.HTTPError(req.full_url, 429, "rate", {}, io.BytesIO(b"slow down"))
        return _Resp({"choices": [{"message": {"content": "done"}}]})
    monkeypatch.setattr(urllib.request, "urlopen", flaky)
    assert _client("openai").complete("s", "u") == "done"
    assert calls["n"] == 3


def test_client_repr_hides_key():
    assert KEY not in repr(_client("openai"))


def test_api_key_comes_from_environment_only():
    assert resolve_api_key("openai", env={"OPENAI_API_KEY": " abc "}) == "abc"
    assert resolve_api_key("openai", env={}) is None


def test_build_from_specs_none_when_unconfigured():
    assert build_client_from_specs(UserSpecifications()) is None


def test_build_from_specs_prompts_for_key_when_asked(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    specs = UserSpecifications(llm_provider="anthropic")
    client = build_client_from_specs(specs, ask_key=True, prompt_fn=lambda _: KEY)
    assert isinstance(client, HTTPLLMClient)


def test_key_is_never_part_of_persisted_specs():
    assert KEY not in json.dumps(UserSpecifications(llm_provider="anthropic").model_dump())
    assert "api_key" not in UserSpecifications.model_fields


@pytest.mark.parametrize("raw", [
    '{"a": 1}',
    '```json\n{"a": 1}\n```',
    'Voici le résultat :\n{"a": 1}\nBonne journée',
])
def test_extract_json_variants(raw):
    assert extract_json(raw) == {"a": 1}


def test_extract_json_rejects_garbage():
    with pytest.raises(LLMError):
        extract_json("pas de json ici")


def test_usage_and_pricing_calculation():
    from mono2micro.llm.pricing import calculate_cost, LLMUsage, PRICING_TABLE_DATE
    assert PRICING_TABLE_DATE == "2024-10-01"
    # gpt-4o: 2.50 input, 10.00 output per 1M
    cost = calculate_cost("gpt-4o", 1000, 2000)
    expected = (1000 / 1e6) * 2.50 + (2000 / 1e6) * 10.00
    assert abs(cost - expected) < 1e-6

