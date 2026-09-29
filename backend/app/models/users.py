"""User model for role-aware login, linked to an organization (tenant)."""
from sqlalchemy import Column, Integer, String, ForeignKey
from ..database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    # Tenant link: every user belongs to exactly one organization. Tenant
    # isolation is derived from this server-side value (see deps.current_org).
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, default="")
    role = Column(String, default="executive")  # executive/ciso/analyst
