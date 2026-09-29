"""Pydantic request/response schemas for the API layer (Pydantic v2)."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


# --- Auth --------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    token: str
    user: dict


class RegisterRequest(BaseModel):
    """Onboard a new company: creates an organization + its first admin user."""
    company_name: str = Field(min_length=2, max_length=120)
    admin_name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=256)
    sector: str = Field(default="", max_length=120)


# --- Assets ------------------------------------------------------------------
class AssetCreate(BaseModel):
    """Create a single business asset. org_id is derived server-side from the
    authenticated user's organization and is never accepted from the client."""
    name: str = Field(min_length=1, max_length=256)
    asset_type: str = Field(default="server", max_length=24)
    environment: str = Field(default="production", max_length=24)
    ip_or_host: str = Field(default="", max_length=128)
    internet_facing: bool = False
    business_value_inr: float = Field(default=0.0, ge=0, le=1e12)
    revenue_impact_per_day_inr: float = Field(default=0.0, ge=0, le=1e11)
    data_sensitivity: int = Field(default=1, ge=0, le=5)
    operational_criticality: int = Field(default=1, ge=0, le=5)
    regulatory_importance: int = Field(default=1, ge=0, le=5)
    records_count: int = Field(default=0, ge=0, le=10_000_000_000)
    owner: str = Field(default="", max_length=64)


class AssetUpdate(BaseModel):
    """Partial update of an existing asset. Every field is optional; only the
    fields supplied are changed. org_id can never be set from the client — the
    tenant is derived server-side and ownership is re-checked on the row."""
    name: str | None = Field(default=None, min_length=1, max_length=256)
    asset_type: str | None = Field(default=None, max_length=24)
    environment: str | None = Field(default=None, max_length=24)
    ip_or_host: str | None = Field(default=None, max_length=128)
    internet_facing: bool | None = None
    business_value_inr: float | None = Field(default=None, ge=0, le=1e12)
    revenue_impact_per_day_inr: float | None = Field(default=None, ge=0, le=1e11)
    data_sensitivity: int | None = Field(default=None, ge=0, le=5)
    operational_criticality: int | None = Field(default=None, ge=0, le=5)
    regulatory_importance: int | None = Field(default=None, ge=0, le=5)
    records_count: int | None = Field(default=None, ge=0, le=10_000_000_000)
    owner: str | None = Field(default=None, max_length=64)


# --- Scenarios ---------------------------------------------------------------
class Mutation(BaseModel):
    op: str
    control_key: str | None = None
    fields: dict[str, Any] | None = None
    filter: dict[str, Any] | None = None
    set: dict[str, Any] | None = None
    vuln: dict[str, Any] | None = None
    key: str | None = None
    value: Any | None = None
    add_age_days: int | None = None


class ScenarioRequest(BaseModel):
    name: str = "Untitled scenario"
    description: str = ""
    mutations: list[Mutation] = Field(default_factory=list)
    save: bool = False


class InvestmentScenarioRequest(BaseModel):
    """Run a what-if from a set of investment option keys."""
    option_keys: list[str] = Field(default_factory=list)
    save: bool = False
    name: str = "Investment scenario"


# --- Optimizer ---------------------------------------------------------------
class OptimizeRequest(BaseModel):
    budget_inr: float = Field(gt=0, le=1e12)


# --- Assistant / NLQ ---------------------------------------------------------
class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


# --- Assumptions -------------------------------------------------------------
class AssumptionUpdate(BaseModel):
    key: str
    value: float = Field(ge=0)


# --- Reports -----------------------------------------------------------------
class ReportRequest(BaseModel):
    kind: str = Field(default="executive", pattern="^(executive|technical)$")
    fmt: str = Field(default="json", pattern="^(json|pdf)$")
    budget_inr: float | None = Field(default=None, gt=0, le=1e12)
