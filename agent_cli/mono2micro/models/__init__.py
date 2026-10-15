from pydantic import BaseModel
if not hasattr(BaseModel, "model_dump"):
    def _model_dump_compat(self, *args, **kwargs):
        mode = kwargs.pop("mode", None)
        if mode == "json":
            import json
            return json.loads(self.json())
        return self.dict(*args, **kwargs)
    BaseModel.model_dump = _model_dump_compat

from mono2micro.models.time_utils import utc_now
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
from mono2micro.models.audit import (
    AuditActionType,
    AuditLogRecord,
    PlanApproval,
)
from mono2micro.models.graph import (
    DependencyNodeType,
    DependencyEdgeType,
    DependencyNode,
    DependencyEdge,
    DependencyGraph,
    PartitionCandidate,
    PartitionEvaluation,
)
from mono2micro.models.data_analysis import (
    PersistenceMechanism,
    TableAccessOperation,
    TableAccessRecord,
    ForeignKeyRelation,
    TransactionScope,
    DataLayerAnalysis,
)
from mono2micro.models.benchmarks import (
    BenchmarkBaselineMode,
    BenchmarkCorpusItem,
    BenchmarkRunResult,
    BenchmarkEvaluationReport,
)
from mono2micro.models.migration import (
    CodemodKind,
    CodemodResult,
    FixLoopAttempt,
    FixLoopSession,
    GatewayRouteConfig,
    FeatureFlagConfig,
)
from mono2micro.models.memory import (
    AdversarialDiffRule,
    AdversarialDiffViolation,
    GroundedMemoryProof,
    TaskMemoryItem,
)
from mono2micro.models.budget import LLMBudgetTracker
from mono2micro.models.doctor import CommandCapability, DoctorReport

__all__ = [
    "utc_now",
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
    "AuditActionType",
    "AuditLogRecord",
    "PlanApproval",
    "DependencyNodeType",
    "DependencyEdgeType",
    "DependencyNode",
    "DependencyEdge",
    "DependencyGraph",
    "PartitionCandidate",
    "PartitionEvaluation",
    "PersistenceMechanism",
    "TableAccessOperation",
    "TableAccessRecord",
    "ForeignKeyRelation",
    "TransactionScope",
    "DataLayerAnalysis",
    "BenchmarkBaselineMode",
    "BenchmarkCorpusItem",
    "BenchmarkRunResult",
    "BenchmarkEvaluationReport",
    "CodemodKind",
    "CodemodResult",
    "FixLoopAttempt",
    "FixLoopSession",
    "GatewayRouteConfig",
    "FeatureFlagConfig",
    "AdversarialDiffRule",
    "AdversarialDiffViolation",
    "GroundedMemoryProof",
    "TaskMemoryItem",
    "LLMBudgetTracker",
    "CommandCapability",
    "DoctorReport",
]
