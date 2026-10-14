"""Model pricing table and cost calculation based on token usage.

All rates are documented per 1,000,000 tokens as of the documented effective date.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

PRICING_TABLE_DATE = "2024-10-01"

# Format: (input_cost_per_million_usd, output_cost_per_million_usd)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    # Anthropic
    "claude-sonnet-5-5": (3.00, 15.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    # Google Gemini
    "gemini-1.5-pro": (3.50, 10.50),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
}

DEFAULT_FALLBACK_PRICE = (1.00, 3.00)


@dataclass
class LLMUsage:
    """Provider-reported token usage and calculated dollar cost."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    pricing_date: str = PRICING_TABLE_DATE


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost for input and output tokens using the price table."""
    model_key = model.lower().strip()
    rate = MODEL_PRICING.get(model_key)
    if not rate:
        # Match by prefix (e.g. gpt-4o-2024-08-06 -> gpt-4o)
        for key, r in MODEL_PRICING.items():
            if key in model_key:
                rate = r
                break
    if not rate:
        rate = DEFAULT_FALLBACK_PRICE

    input_rate, output_rate = rate
    cost = (input_tokens / 1_000_000.0) * input_rate + (output_tokens / 1_000_000.0) * output_rate
    return round(cost, 6)
