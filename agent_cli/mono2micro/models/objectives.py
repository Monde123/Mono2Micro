"""Objectives clarification models.

Enforces Principle 1 of Hammad et al. (2023):
Clarify the business & operational motivation before picking any architecture.
Never assume microservices are automatically desirable.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class MigrationGoalType(str, Enum):
    TARGETED_SCALABILITY = "TARGETED_SCALABILITY"  # e.g. only 1 endpoint receives 90% of traffic
    TEAM_AUTONOMY = "TEAM_AUTONOMY"               # Multiple independent teams colliding on the codebase
    DEPLOY_FREQUENCY = "DEPLOY_FREQUENCY"         # Need to deploy a small feature 10x/day without rebuilding all
    FAULT_ISOLATION = "FAULT_ISOLATION"           # A failure in reporting should not crash payments
    TECH_DIVERSITY = "TECH_DIVERSITY"             # Need specialized stack (e.g. Python for ML, Go for low latency)
    INFRASTRUCTURE_COST = "INFRASTRUCTURE_COST"   # Optimize resource usage
    CODEBASE_MODULARITY = "CODEBASE_MODULARITY"   # Code is spaghetti, need clear boundaries
    UNKNOWN_OR_TREND = "UNKNOWN_OR_TREND"         # "We heard microservices are best practice"


class NonMicroserviceAlternative(BaseModel):
    """Alternative solution that could achieve the goal without microservice distributed complexity."""
    title: str
    description: str
    estimated_complexity: str  # LOW, MEDIUM, HIGH
    avoids_distributed_tax: bool = True
    tradeoff_summary: str


class MigrationObjectiveClarification(BaseModel):
    """User-provided or refined architectural objective."""
    primary_goal: MigrationGoalType
    secondary_goals: List[MigrationGoalType] = Field(default_factory=list)
    user_rationale: str
    current_team_size: int = 1
    current_deploy_frequency_per_week: float = 1.0
    pain_points: List[str] = Field(default_factory=list)
    
    # Critical evaluation: can this be solved without microservices?
    can_be_solved_within_monolith: bool = False
    monolith_solution_notes: Optional[str] = None
    suggested_alternatives: List[NonMicroserviceAlternative] = Field(default_factory=list)
