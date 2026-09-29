"""Risk quantification entities: assumptions, findings, contributions, snapshots."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean,
)
from sqlalchemy.orm import relationship

from ..database import Base


class FinancialAssumption(Base):
    """Editable global assumptions that drive the financial model (transparent)."""
    __tablename__ = "financial_assumptions"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, default="INR")
    category = Column(String, default="impact")
    description = Column(Text, default="")
    editable = Column(Boolean, default=True)


class RiskSnapshot(Base):
    """Point-in-time enterprise risk state -> powers trends & continuous view."""
    __tablename__ = "risk_snapshots"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    label = Column(String, default="")
    trigger = Column(String, default="manual")  # manual/demo-load/telemetry/scenario/remediation
    enterprise_risk_score = Column(Float, default=0.0)     # 0..100
    total_ale_inr = Column(Float, default=0.0)             # expected annual loss
    total_exposure_inr = Column(Float, default=0.0)        # single-event aggregate exposure
    var95_inr = Column(Float, default=0.0)                 # 95% value-at-risk (annual)
    var99_inr = Column(Float, default=0.0)
    likelihood_avg = Column(Float, default=0.0)
    open_vulns = Column(Integer, default=0)
    critical_vulns = Column(Integer, default=0)
    avg_control_effectiveness = Column(Float, default=0.0)
    top_contributors = Column(JSON, default=list)
    by_business_unit = Column(JSON, default=list)
    by_category = Column(JSON, default=list)
    control_effectiveness = Column(JSON, default=list)
    framework_coverage = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)

    findings = relationship("RiskFinding", back_populates="snapshot", cascade="all, delete-orphan")
    contributions = relationship("RiskContribution", back_populates="snapshot", cascade="all, delete-orphan")


class RiskFinding(Base):
    """Granular per-(asset,vulnerability) computed risk with full breakdown."""
    __tablename__ = "risk_findings"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("risk_snapshots.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    vuln_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, default="vulnerability")
    severity = Column(String, default="Medium")
    likelihood = Column(Float, default=0.0)     # annualized probability 0..1
    sle_inr = Column(Float, default=0.0)         # single loss expectancy
    aro = Column(Float, default=0.0)             # annual rate of occurrence
    ale_inr = Column(Float, default=0.0)         # annual loss expectancy = SLE*ARO
    breakdown = Column(JSON, default=dict)       # full explainable trace
    created_at = Column(DateTime, default=datetime.utcnow)

    snapshot = relationship("RiskSnapshot", back_populates="findings")


class RiskContribution(Base):
    """Ranked risk driver contributing to total enterprise exposure."""
    __tablename__ = "risk_contributions"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("risk_snapshots.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    kind = Column(String, default="finding")     # finding/asset/control/threat/category
    label = Column(String, nullable=False)
    ref_id = Column(Integer, nullable=True)
    ale_inr = Column(Float, default=0.0)
    share = Column(Float, default=0.0)           # fraction of total 0..1
    likelihood_contrib = Column(Float, default=0.0)
    control_weakness = Column(String, default="")
    recommended_action = Column(String, default="")
    expected_reduction_inr = Column(Float, default=0.0)

    snapshot = relationship("RiskSnapshot", back_populates="contributions")
