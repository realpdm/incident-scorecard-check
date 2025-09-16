"""Data models for Incident.io and Cortex.io APIs using Pydantic."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Incident.io Models
class IncidentService(BaseModel):
    """Service affected by an incident."""
    id: str
    name: str
    summary: Optional[str] = None


class IncidentSeverity(BaseModel):
    """Incident severity level."""
    id: str
    name: str
    rank: int


class IncidentStatus(BaseModel):
    """Current status of an incident."""
    id: str
    name: str
    category: str


class Incident(BaseModel):
    """Incident from Incident.io API."""
    id: str
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    severity: IncidentSeverity
    status: IncidentStatus
    services: List[IncidentService] = Field(default_factory=list)
    visibility: str


# Cortex.io Models
class ScorecardRule(BaseModel):
    """Individual scorecard rule."""
    expression: str
    level: str
    title: str
    description: Optional[str] = None
    weight: Optional[int] = None


class ScorecardScore(BaseModel):
    """Score for a specific rule."""
    rule: ScorecardRule
    score: Optional[float] = None
    level: Optional[str] = None


class ServiceScorecard(BaseModel):
    """Scorecard data for a service."""
    service_tag: str
    scorecard_tag: str
    scores: List[ScorecardScore] = Field(default_factory=list)
    total_score: Optional[float] = None
    current_level: Optional[str] = None


class CortexService(BaseModel):
    """Service information from Cortex.io."""
    tag: str
    title: str
    summary: Optional[str] = None
    type: Optional[str] = None


# Report Models
class ServiceImpactReport(BaseModel):
    """Report showing incident impact on service scorecard scores."""
    service_name: str
    service_tag: str
    incident_count: int
    incidents: List[str] = Field(default_factory=list)  # incident IDs
    scorecards: List[ServiceScorecard] = Field(default_factory=list)  # Multiple scorecards
    total_score: Optional[float] = None


class IncidentReport(BaseModel):
    """Complete report of incidents and their impact on service scores."""
    report_generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_incidents: int
    impacted_services: List[ServiceImpactReport] = Field(default_factory=list)
