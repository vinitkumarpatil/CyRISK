"""Security telemetry entities: vulns, threats, incidents, controls, sources."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    cve_id = Column(String, default="")
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    cvss = Column(Float, default=5.0)                 # 0..10
    severity = Column(String, default="Medium")        # Critical/High/Medium/Low
    exploit_available = Column(Boolean, default=False)
    internet_exposed = Column(Boolean, default=False)
    status = Column(String, default="open")            # open/remediating/closed
    category = Column(String, default="software")      # software/config/patch/web/network
    patch_available = Column(Boolean, default=True)
    age_days = Column(Integer, default=30)
    remediation_cost_inr = Column(Float, default=200000.0)
    source = Column(String, default="Nessus (simulated)")
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_demo = Column(Boolean, default=True)

    asset = relationship("Asset", back_populates="vulnerabilities")


class Threat(Base):
    __tablename__ = "threats"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    threat_actor = Column(String, default="")
    category = Column(String, default="ransomware")
    ttp = Column(String, default="")                   # MITRE ATT&CK style ref
    likelihood_weight = Column(Float, default=0.5)     # 0..1 contextual multiplier
    relevance = Column(Float, default=0.5)             # 0..1 relevance to org sector
    description = Column(Text, default="")
    source = Column(String, default="MISP feed (simulated)")
    is_demo = Column(Boolean, default=True)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, default="malware")
    occurred_at = Column(DateTime, default=datetime.utcnow)
    financial_impact_inr = Column(Float, default=0.0)
    downtime_hours = Column(Float, default=0.0)
    records_affected = Column(Integer, default=0)
    root_cause = Column(String, default="")
    description = Column(Text, default="")
    is_demo = Column(Boolean, default=True)

    asset = relationship("Asset", back_populates="incidents")


class Control(Base):
    __tablename__ = "controls"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    key = Column(String, nullable=False)               # mfa, patch_management, ...
    name = Column(String, nullable=False)
    category = Column(String, default="preventive")
    description = Column(Text, default="")
    # Raw inputs -> transparent effectiveness score in engine
    config_strength = Column(Float, default=0.5)       # 0..1 how well configured
    coverage = Column(Float, default=0.5)              # 0..1 fraction of estate covered
    compliance_status = Column(String, default="Partial")  # Compliant/Partial/Non-Compliant
    maturity = Column(Integer, default=2)              # 0..5
    monitored = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=True)

    assessments = relationship("ControlAssessment", back_populates="control", cascade="all, delete-orphan")


class ControlAssessment(Base):
    __tablename__ = "control_assessments"
    id = Column(Integer, primary_key=True)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=False)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    effectiveness = Column(Float, default=0.5)          # 0..1 snapshot of computed value
    method = Column(String, default="telemetry-derived")
    evidence = Column(Text, default="")
    notes = Column(Text, default="")

    control = relationship("Control", back_populates="assessments")


class TelemetrySource(Base):
    __tablename__ = "telemetry_sources"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    source_type = Column(String, nullable=False)  # vuln_scanner/siem/iam/edr/cspm/asset_inventory/threat_intel
    name = Column(String, nullable=False)
    vendor = Column(String, default="")
    status = Column(String, default="simulated")   # simulated/connected
    last_sync = Column(DateTime, default=datetime.utcnow)
    record_count = Column(Integer, default=0)
    health = Column(String, default="healthy")
    description = Column(Text, default="")
    is_demo = Column(Boolean, default=True)
