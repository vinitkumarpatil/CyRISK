"""Core organizational + asset entities."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sector = Column(String, default="Financial Services")
    description = Column(Text, default="")
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business_units = relationship("BusinessUnit", back_populates="organization", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="organization", cascade="all, delete-orphan")


class BusinessUnit(Base):
    __tablename__ = "business_units"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    head = Column(String, default="")

    organization = relationship("Organization", back_populates="business_units")
    assets = relationship("Asset", back_populates="business_unit")
    services = relationship("BusinessService", back_populates="business_unit")


class BusinessService(Base):
    __tablename__ = "business_services"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    bu_id = Column(Integer, ForeignKey("business_units.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    criticality_tier = Column(String, default="Tier-2")  # Tier-0..Tier-3

    business_unit = relationship("BusinessUnit", back_populates="services")
    assets = relationship("Asset", back_populates="service")


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    bu_id = Column(Integer, ForeignKey("business_units.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("business_services.id"), nullable=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, default="server")  # server/database/endpoint/network/saas/app
    environment = Column(String, default="production")
    ip_or_host = Column(String, default="")
    internet_facing = Column(Boolean, default=False)
    # Criticality factors (raw inputs -> transparent criticality score in engine)
    business_value_inr = Column(Float, default=0.0)          # replacement/business value
    revenue_impact_per_day_inr = Column(Float, default=0.0)  # revenue lost per day of downtime
    data_sensitivity = Column(Integer, default=1)            # 0..5
    operational_criticality = Column(Integer, default=1)     # 0..5
    regulatory_importance = Column(Integer, default=1)       # 0..5
    records_count = Column(Integer, default=0)               # PII/records held
    owner = Column(String, default="")
    tags = Column(JSON, default=list)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="assets")
    business_unit = relationship("BusinessUnit", back_populates="assets")
    service = relationship("BusinessService", back_populates="assets")
    vulnerabilities = relationship("Vulnerability", back_populates="asset", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="asset")
    dependencies = relationship(
        "AssetDependency", foreign_keys="AssetDependency.asset_id",
        back_populates="asset", cascade="all, delete-orphan",
    )


class AssetDependency(Base):
    __tablename__ = "asset_dependencies"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    depends_on_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    dependency_type = Column(String, default="uses")  # uses/hosts/authenticates/data-flow

    asset = relationship("Asset", foreign_keys=[asset_id], back_populates="dependencies")
    depends_on = relationship("Asset", foreign_keys=[depends_on_id])
