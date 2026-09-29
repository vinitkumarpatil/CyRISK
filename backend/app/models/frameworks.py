"""Cybersecurity framework mapping entities."""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class Framework(Base):
    __tablename__ = "frameworks"
    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False)         # iso27001/nist_csf/cis/rbi/sebi
    name = Column(String, nullable=False)
    full_name = Column(String, default="")
    version = Column(String, default="")
    description = Column(Text, default="")

    controls = relationship("FrameworkControl", back_populates="framework", cascade="all, delete-orphan")


class FrameworkControl(Base):
    __tablename__ = "framework_controls"
    id = Column(Integer, primary_key=True)
    framework_id = Column(Integer, ForeignKey("frameworks.id"), nullable=False)
    control_ref = Column(String, nullable=False)  # e.g. A.9.4.2 / PR.AC-1 / CIS-6
    category = Column(String, default="")
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    internal_control_key = Column(String, default="")  # links to our Control.key

    framework = relationship("Framework", back_populates="controls")
    mappings = relationship("FrameworkMapping", back_populates="framework_control", cascade="all, delete-orphan")


class FrameworkMapping(Base):
    """Assessment/mapping of a framework control to internal state (NOT a
    compliance certification). Status is an assessment, editable."""
    __tablename__ = "framework_mappings"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    framework_control_id = Column(Integer, ForeignKey("framework_controls.id"), nullable=False)
    internal_control_key = Column(String, default="")
    status = Column(String, default="Review Required")  # Covered/Partial/Potential Gap/Review Required
    evidence = Column(Text, default="")
    notes = Column(Text, default="")
    editable = Column(Boolean, default=True)

    framework_control = relationship("FrameworkControl", back_populates="mappings")
