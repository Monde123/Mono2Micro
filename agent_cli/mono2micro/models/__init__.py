"""Mono2Micro Domain and Data Models."""

from mono2micro.models.paper_reference import (
    PaperPrincipleId,
    PaperPrincipleCitation,
    PAPER_PRINCIPLES,
)
from mono2micro.models.discovery import (
    ComponentType,
    FactEvidenceType,
    VerifiedFact,
    AssumptionCertainty,
    ModelAssumption,
    DetectedComponent,
    DatabaseCouplingInfo,
    DiscoveryReport,
)
from mono2micro.models.objectives import (
    MigrationGoalType,
    NonMicroserviceAlternative,
    MigrationObjectiveClarification,
)
from mono2micro.models.domains import (
    DomainEvidenceSource,
    DomainEvidence,
    CouplingLevel,
    BoundedContextHypothesis,
)
from mono2micro.models.options import (
    ArchitectureOptionType,
    OptionEvaluation,
    OptionsComparisonMatrix,
)
from mono2micro.models.plan import (
    RoutingStrategyType,
    DataSeparationStrategy,
    DataOwnershipPlan,
    RollbackProcedure,
    StranglerStep,
    StranglerPlan,
)
from mono2micro.models.adversarial import (
    ObjectionSeverity,
    AdversarialObjection,
    HiddenCouplingRisk,
    IndependentTestCase,
    AdversarialReview,
)
from mono2micro.models.quality_gate import (
    CriterionStatus,
    QualityGateCategory,
    QualityGateCriterion,
    QualityGateResult,
)
from mono2micro.models.report import FinalReport

__all__ = [
    "PaperPrincipleId",
    "PaperPrincipleCitation",
    "PAPER_PRINCIPLES",
    "ComponentType",
    "FactEvidenceType",
    "VerifiedFact",
    "AssumptionCertainty",
    "ModelAssumption",
    "DetectedComponent",
    "DatabaseCouplingInfo",
    "DiscoveryReport",
    "MigrationGoalType",
    "NonMicroserviceAlternative",
    "MigrationObjectiveClarification",
    "DomainEvidenceSource",
    "DomainEvidence",
    "CouplingLevel",
    "BoundedContextHypothesis",
    "ArchitectureOptionType",
    "OptionEvaluation",
    "OptionsComparisonMatrix",
    "RoutingStrategyType",
    "DataSeparationStrategy",
    "DataOwnershipPlan",
    "RollbackProcedure",
    "StranglerStep",
    "StranglerPlan",
    "ObjectionSeverity",
    "AdversarialObjection",
    "HiddenCouplingRisk",
    "IndependentTestCase",
    "AdversarialReview",
    "CriterionStatus",
    "QualityGateCategory",
    "QualityGateCriterion",
    "QualityGateResult",
    "FinalReport",
]
