"""Paper reference data and citations.

Grounding reference:
Hatem Hammad, Thaer Sahmoud and Abed Al Rahman Abu Ghazala (2023).
"Convert Monolithic Application to Microservice Application".
alphaXiv: https://www.alphaxiv.org/abs/2306.08851
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class PaperPrincipleId(str, Enum):
    CLARIFY_OBJECTIVES = "PRINCIPLE_1_CLARIFY_OBJECTIVES"
    DOMAIN_ANALYSIS = "PRINCIPLE_2_DOMAIN_ANALYSIS"
    INCREMENTAL_EVOLUTION = "PRINCIPLE_3_INCREMENTAL_EVOLUTION"
    LOW_COUPLING_FIRST = "PRINCIPLE_4_LOW_COUPLING_FIRST"
    STRANGLER_FIG_ROUTING = "PRINCIPLE_5_STRANGLER_FIG_ROUTING"
    DATA_SEPARATION_OWNERSHIP = "PRINCIPLE_6_DATA_SEPARATION_OWNERSHIP"
    CONTINUOUS_TESTING_ROLLBACK = "PRINCIPLE_7_CONTINUOUS_TESTING_ROLLBACK"


class PaperPrincipleCitation(BaseModel):
    """Citation linking a recommendation to the academic paper principles."""
    principle_id: PaperPrincipleId
    principle_name: str
    paper_section: str
    paper_page: Optional[int] = None
    summary: str
    applicability_guideline: str
    caveat: str


PAPER_PRINCIPLES: dict[PaperPrincipleId, PaperPrincipleCitation] = {
    PaperPrincipleId.CLARIFY_OBJECTIVES: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.CLARIFY_OBJECTIVES,
        principle_name="Clarification of objectives before architectural choice",
        paper_section="Section I & Section II: Background & Motivation",
        paper_page=1,
        summary="Never split a monolith without a clearly identified business or operational goal (targeted scalability, team independence, delivery cadence).",
        applicability_guideline="If the goal can be satisfied within the monolith (e.g., vertical scaling, caching, internal modularization), prefer the simplest solution.",
        caveat="The paper does not advocate microservices as an end in itself."
    ),
    PaperPrincipleId.DOMAIN_ANALYSIS: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.DOMAIN_ANALYSIS,
        principle_name="Domain analysis and bounded contexts (DDD)",
        paper_section="Section III: Domain-Driven Design and Decomposition",
        paper_page=3,
        summary="Decompose according to business domain boundaries (Bounded Contexts) rather than horizontal technical layers.",
        applicability_guideline="Boundaries inferred from code are hypotheses that must be verified with domain experts.",
        caveat="Do not invent business rules absent from the source code."
    ),
    PaperPrincipleId.INCREMENTAL_EVOLUTION: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.INCREMENTAL_EVOLUTION,
        principle_name="Incremental evolution vs. Big Bang rewrite",
        paper_section="Section IV: Migration Strategies and Phasing",
        paper_page=4,
        summary="Proscribe full application rewrites. Allow old and new systems to coexist step by step.",
        applicability_guideline="Each step must be small, autonomous, production-ready, and independently verifiable.",
        caveat="A Big Bang migration carries disproportionate critical failure risk."
    ),
    PaperPrincipleId.LOW_COUPLING_FIRST: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.LOW_COUPLING_FIRST,
        principle_name="Start with a loosely coupled component",
        paper_section="Section IV.B: Service Selection for Early Extraction",
        paper_page=5,
        summary="Prioritize extracting a peripheral subdomain with minimal dependencies on the central database and the rest of the code.",
        applicability_guideline="Use the first extracted service to test CI/CD pipelines, observability, and network mechanisms.",
        caveat="Do not tackle the transactional core or shared entities in the first step."
    ),
    PaperPrincipleId.STRANGLER_FIG_ROUTING: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.STRANGLER_FIG_ROUTING,
        principle_name="Strangler Fig progressive routing",
        paper_section="Section V: The Strangler Application Pattern",
        paper_page=6,
        summary="Insert a gateway or routing component to gradually shift traffic from monolith endpoints to the new service.",
        applicability_guideline="Enables progressive rollout (canary, feature flags, URL routing) and early anomaly detection.",
        caveat="Requires user session management and distributed request consistency."
    ),
    PaperPrincipleId.DATA_SEPARATION_OWNERSHIP: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.DATA_SEPARATION_OWNERSHIP,
        principle_name="Exclusive ownership and data splitting",
        paper_section="Section VI: Database Decomposition & Data Consistency",
        paper_page=7,
        summary="A microservice must own its dedicated database. No direct inter-service database access.",
        applicability_guideline="Explicitly address table splitting, shared foreign keys, and substitute local ACID transactions with events or saga patterns if necessary.",
        caveat="Data separation is NEVER an automatic operation: it requires rigorous validation of eventual consistency."
    ),
    PaperPrincipleId.CONTINUOUS_TESTING_ROLLBACK: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.CONTINUOUS_TESTING_ROLLBACK,
        principle_name="Independent tests, Quality Gate, and systematic reversibility",
        paper_section="Section VII: Testing, Verification and Fallback Mechanisms",
        paper_page=8,
        summary="Each migration step must include regression tests, API contract tests, and a documented, tested rollback procedure.",
        applicability_guideline="The Quality Gate must block production deployment if any mandatory criterion fails. Averaging results is strictly prohibited.",
        caveat="If rollback is not guaranteed, the step must not be approved."
    ),
}
