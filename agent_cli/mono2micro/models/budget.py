"""LLM budget, token accounting, and cost tracking contracts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from mono2micro.models.time_utils import utc_now


class LLMBudgetTracker(BaseModel):
    """Tracks token and cost consumption against configured hard ceilings."""
    max_tokens: Optional[int] = None
    max_cost_usd: Optional[float] = None
    consumed_input_tokens: int = 0
    consumed_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    hard_stop_reached: bool = False
    stop_reason: Optional[str] = None
    last_updated: datetime = Field(default_factory=utc_now)

    @property
    def total_tokens(self) -> int:
        return self.consumed_input_tokens + self.consumed_output_tokens

    def record_usage(self, prompt_tokens: int, completion_tokens: int, cost_per_1k_input: float = 0.0015, cost_per_1k_output: float = 0.002) -> bool:
        """Record usage and evaluate if budget ceiling has been reached."""
        self.consumed_input_tokens += prompt_tokens
        self.consumed_output_tokens += completion_tokens
        delta_cost = (prompt_tokens / 1000.0 * cost_per_1k_input) + (completion_tokens / 1000.0 * cost_per_1k_output)
        self.estimated_cost_usd += delta_cost
        self.last_updated = utc_now()

        if self.max_tokens is not None and self.total_tokens >= self.max_tokens:
            self.hard_stop_reached = True
            self.stop_reason = f"Token budget ceiling reached ({self.total_tokens} >= {self.max_tokens})"
            return False

        if self.max_cost_usd is not None and self.estimated_cost_usd >= self.max_cost_usd:
            self.hard_stop_reached = True
            self.stop_reason = f"Cost budget ceiling reached (${self.estimated_cost_usd:.4f} >= ${self.max_cost_usd:.4f})"
            return False

        return True
