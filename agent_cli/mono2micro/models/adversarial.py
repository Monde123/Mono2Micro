"""Adversarial and devil's advocate models.

Enforces Workflow Step 6:
An independent adversarial sub-agent challenges assumptions, searches for hidden couplings,
and prepares independent test scenarios BEFORE any code changes.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from mono2micro.models.time_utils import utc_now


class ObjectionSeverity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    OBSERVATION = "OBSERVATION"


class AdversarialObjection(BaseModel):
    """Specific objection raised by the devil's advocate agent."""
    objection_id: str
    severity: ObjectionSeverity
    topic: str
    argument: str = ""
    argument_fr: Optional[str] = None
    evidence_or_counterexample: str
    suggested_remedy: str
    is_resolved: bool = False
    resolution_notes: Optional[str] = None

    def __init__(self, **data):
        arg = data.get("argument") or data.get("argument_fr") or ""
        data["argument"] = arg
        data["argument_fr"] = arg
        super().__init__(**data)


class HiddenCouplingRisk(BaseModel):
    """Hidden dependency or shared state uncovered by deep inspection."""
    coupling_name: str
    module_a: str
    module_b: str
    coupling_mechanism: str
    impact_if_separated: str
    recommended_mitigation: str


class IndependentTestCase(BaseModel):
    """Test scenario designed independently of the implementer's rationale."""
    case_id: str
    title: str
    intent: str
    preconditions: List[str]
    input_or_trigger: str
    expected_outcome: str
    failure_symptom: str
    is_regression_test: bool = True
    is_contract_test: bool = False


class AdversarialReview(BaseModel):
    """Complete devil's advocate evaluation of a proposal or step."""
    reviewed_at: datetime = Field(default_factory=utc_now)
    target_step_number: Optional[int] = None
    step_is_blocked: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    objections: List[AdversarialObjection] = Field(default_factory=list)
    hidden_coupling_risks: List[HiddenCouplingRisk] = Field(default_factory=list)
    independent_test_cases: List[IndependentTestCase] = Field(default_factory=list)
    ambiguous_requirements: List[str] = Field(default_factory=list)
    recommendation_summary: str = ""
    recommendation_summary_fr: Optional[str] = None

    def __init__(self, **data):
        rec = data.get("recommendation_summary") or data.get("recommendation_summary_fr") or ""
        data["recommendation_summary"] = rec
        data["recommendation_summary_fr"] = rec
        super().__init__(**data)
