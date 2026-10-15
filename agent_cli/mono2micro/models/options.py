"""Architectural options comparison models.

Enforces systematic comparison between:
1. Keep current monolith as-is
2. Modularize the monolith (Modular Monolith)
3. Progressive Strangler Fig microservice extraction
4. Postpone migration
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ArchitectureOptionType(str, Enum):
    KEEP_MONOLITH = "KEEP_MONOLITH"
    MODULAR_MONOLITH = "MODULAR_MONOLITH"
    STRANGLER_MICROSERVICES = "STRANGLER_MICROSERVICES"
    POSTPONE_MIGRATION = "POSTPONE_MIGRATION"


class OptionEvaluation(BaseModel):
    """Detailed evaluation of an architectural path."""
    option_type: ArchitectureOptionType
    title: str
    summary: str
    expected_benefits: List[str] = Field(default_factory=list)
    implementation_costs: List[str] = Field(default_factory=list)
    operational_risks: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    
    # Quantitative estimates (indicative)
    complexity_rating: str  # "LOW", "MEDIUM", "HIGH", "VERY HIGH"
    operational_overhead: str  # "MINIMAL", "MODERATE", "SIGNIFICANT", "HEAVY"
    suitability_score: float = Field(ge=0.0, le=1.0)
    is_recommended: bool = False
    recommendation_rationale: str = ""


class OptionsComparisonMatrix(BaseModel):
    """Comparative analysis across all 4 options."""
    evaluations: List[OptionEvaluation]
    recommended_option: ArchitectureOptionType
    synthesis: str = ""
    synthesis_fr: Optional[str] = None
    key_tradeoffs: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        syn = data.get("synthesis") or data.get("synthesis_fr") or ""
        data["synthesis"] = syn
        data["synthesis_fr"] = syn
        super().__init__(**data)
