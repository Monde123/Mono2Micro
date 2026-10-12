"""Discovery models.

Strict distinction between verifiable empirical facts and model assumptions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class ComponentType(str, Enum):
    API_ROUTER = "API_ROUTER"
    BUSINESS_SERVICE = "BUSINESS_SERVICE"
    DATABASE_ORM = "DATABASE_ORM"
    DATABASE_RAW = "DATABASE_RAW"
    BACKGROUND_WORKER = "BACKGROUND_WORKER"
    CRON_JOB = "CRON_JOB"
    UI_FRONTEND = "UI_FRONTEND"
    TEST_SUITE = "TEST_SUITE"
    DEPLOYMENT_CONFIG = "DEPLOYMENT_CONFIG"
    UNKNOWN = "UNKNOWN"


class FactEvidenceType(str, Enum):
    FILE_EXISTS = "FILE_EXISTS"
    IMPORT_STATEMENT = "IMPORT_STATEMENT"
    PACKAGE_DEPENDENCY = "PACKAGE_DEPENDENCY"
    DATABASE_MIGRATION = "DATABASE_MIGRATION"
    ROUTE_DEFINITION = "ROUTE_DEFINITION"
    DOCKERFILE_DIRECTIVE = "DOCKERFILE_DIRECTIVE"
    TEST_CONFIG = "TEST_CONFIG"


class VerifiedFact(BaseModel):
    """An empirical observation verified directly on the filesystem or static AST."""
    fact_id: str
    evidence_type: FactEvidenceType
    file_path: str
    line_number: Optional[int] = None
    observation: str
    code_snippet: Optional[str] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class AssumptionCertainty(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ModelAssumption(BaseModel):
    """An inference produced by the AI model or heuristic analysis.

    NEVER presented as an established fact. Requires explicit confirmation.
    """
    assumption_id: str
    statement: str
    rationale: str
    certainty: AssumptionCertainty
    based_on_facts: List[str] = Field(default_factory=list, description="IDs of VerifiedFacts that inspired this assumption")
    requires_user_confirmation: bool = True
    user_confirmed: Optional[bool] = None
    user_notes: Optional[str] = None


class DetectedComponent(BaseModel):
    """Component detected in the target repository."""
    name: str
    relative_path: str
    component_type: ComponentType
    language: str
    framework_or_library: Optional[str] = None
    entrypoint: Optional[str] = None
    loc_estimate: int = 0
    inbound_dependencies: List[str] = Field(default_factory=list)
    outbound_dependencies: List[str] = Field(default_factory=list)


class DatabaseCouplingInfo(BaseModel):
    """Identified database usage and shared tables coupling."""
    db_type: str = "UNKNOWN"
    connection_strings_detected: int = 0
    detected_models_or_tables: List[str] = Field(default_factory=list)
    cross_module_table_access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping from table/model name to list of modules accessing it"
    )
    raw_sql_queries_found: int = 0
    migrations_path: Optional[str] = None


class DiscoveryReport(BaseModel):
    """Complete read-only repository discovery report."""
    target_directory: str
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    languages_detected: List[str] = Field(default_factory=list)
    frameworks_detected: List[str] = Field(default_factory=list)
    total_files_scanned: int = 0
    total_loc_scanned: int = 0
    components: List[DetectedComponent] = Field(default_factory=list)
    database_coupling: DatabaseCouplingInfo = Field(default_factory=DatabaseCouplingInfo)
    test_frameworks_detected: List[str] = Field(default_factory=list)
    ci_cd_configs_detected: List[str] = Field(default_factory=list)
    verified_facts: List[VerifiedFact] = Field(default_factory=list)
    model_assumptions: List[ModelAssumption] = Field(default_factory=list)
    analysis_limitations: List[str] = Field(default_factory=list)
