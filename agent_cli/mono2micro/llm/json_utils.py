"""Robust extraction of JSON from LLM text output (untrusted input)."""

import json
import re
from typing import Any

from mono2micro.llm.client import LLMError

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Any:
    """Parse the first JSON object/array found in an LLM reply.

    Accepts raw JSON, JSON inside a Markdown fence, or JSON surrounded by prose.
    Raises LLMError when nothing parseable is found; callers must still validate
    the structure, since the content is untrusted.
    """
    if not text or not text.strip():
        raise LLMError("Réponse vide du modèle.")

    candidates = [text.strip()]
    candidates += [m.strip() for m in _FENCE.findall(text)]

    # Fallback: outermost braces/brackets in free text
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            candidates.append(text[start:end + 1])

    for cand in candidates:
        try:
            return json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
    raise LLMError("Impossible d'extraire un JSON valide de la réponse du modèle.")
