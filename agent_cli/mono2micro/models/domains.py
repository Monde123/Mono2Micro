"""Domain analysis and bounded context models.

Enforces Principle 2 of Hammad et al. (2023):
Analyze business domain and propose candidate bounded contexts as hypotheses.
Never invent business rules that are not grounded in code/schema evidence.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class DomainEvidenceSource(str, Enum):
    DIRECTORY_STRUCTURE = "DIRECTORY_STRUCTURE"
    DATABASE_TABLES = "DATABASE_TABLES"
    API_ROUTE_PREFIX = "API_ROUTE_PREFIX"
    SERVICE_CLASS = "SERVICE_CLASS"
    EVENT_TOPIC = "EVENT_TOPIC"
    USER_DOMAIN_SPEC = "USER_DOMAIN_SPEC"
    LLM_INFERENCE = "LLM_INFERENCE"  # hypothesis proposed by the language model


class DomainEvidence(BaseModel):
    """Concrete pointer grounding a domain boundary."""
    source_type: DomainEvidenceSource
    file_or_symbol_path: str
    description: str
    strength: float = Field(ge=0.0, le=1.0, description="Evidence confidence from 0 to 1")


class CouplingLevel(str, Enum):
    LOOSE = "LOOSE"        # Very few dependencies, easy early extraction candidate
    MODERATE = "MODERATE"  # Some shared data or calls, requires adapter
    TIGHT = "TIGHT"        # Highly entangled, shared transactions, foreign keys


class BoundedContextHypothesis(BaseModel):
    """Candidate bounded context proposed from empirical hints."""
    context_id: str
    name: str
    suggested_responsibility: str
    evidences: List[DomainEvidence] = Field(default_factory=list)
    identified_entities: List[str] = Field(default_factory=list)
    identified_api_endpoints: List[str] = Field(default_factory=list)
    coupling_level: CouplingLevel = CouplingLevel.MODERATE
    coupling_notes: str = ""
    
    # Dependencies with other contexts
    inbound_dependencies: List[str] = Field(default_factory=list, description="Other contexts that call this context")
    outbound_dependencies: List[str] = Field(default_factory=list, description="Contexts that this context calls")
    shared_database_tables: List[str] = Field(default_factory=list, description="Tables shared with other contexts")
    
    # Hypothesis status
    user_confirmed: Optional[bool] = None
    user_feedback: Optional[str] = None
    extraction_feasibility_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Higher score means lower coupling, better candidate for early Strangler Fig phase"
    )
