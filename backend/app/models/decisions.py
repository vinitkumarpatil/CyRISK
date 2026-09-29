"""Decision-support entities: mitigations, investments, scenarios, reports."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean,
)

from ..database import Base


class MitigationAction(Base):
    """A concrete remediation/mitigation action tied to controls & assets."""
    __tablename__ = "mitigation_actions"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    action_type = Column(String, default="control_improvement")
    control_key = Column(String, default="")       # control this improves
    cost_inr = Column(Float, default=0.0)
    effort = Column(String, default="Medium")      # Low/Medium/High
    status = Column(String, default="proposed")
    affected_asset_ids = Column(JSON, default=list)
    is_demo = Column(Boolean, default=True)


class InvestmentOption(Base):
    """Candidate investment for the optimizer. Expected reduction is computed
    live by the engine (data-driven) from `improves` params, never hardcoded."""
    __tablename__ = "investment_options"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    category = Column(String, default="control")
    control_key = Column(String, default="")           # control improved (if any)
    action = Column(String, default="improve_control")  # improve_control/patch_vulns/reduce_exposure
    cost_inr = Column(Float, default=0.0)
    effort = Column(String, default="Medium")
    # Parameters describing what the investment changes (engine simulates these):
    params = Column(JSON, default=dict)  # e.g. {"target_config":0.95,"target_coverage":0.95}
    is_demo = Column(Boolean, default=True)


class Scenario(Base):
    """A what-if scenario: a set of mutations applied to a cloned model state."""
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    spec = Column(JSON, default=dict)      # list of mutations
    result = Column(JSON, default=dict)    # before/after computed result
    created_at = Column(DateTime, default=datetime.utcnow)
    is_demo = Column(Boolean, default=True)


class Recommendation(Base):
    """AI/model-generated mitigation recommendation with full cost-benefit."""
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("risk_snapshots.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    priority = Column(String, default="Medium")     # Critical/High/Medium/Low
    control_key = Column(String, default="")
    cost_inr = Column(Float, default=0.0)
    expected_risk_reduction = Column(Float, default=0.0)      # 0..1 of enterprise risk
    expected_ale_reduction_inr = Column(Float, default=0.0)
    rosi = Column(Float, default=0.0)               # percent
    effort = Column(String, default="Medium")
    affected_asset_ids = Column(JSON, default=list)
    rationale = Column(JSON, default=dict)          # explainable "why"
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    kind = Column(String, default="executive")   # executive/technical
    fmt = Column(String, default="json")
    created_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, default=dict)
    file_path = Column(String, default="")
