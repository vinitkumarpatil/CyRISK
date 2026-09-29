"""Model registry — importing this module registers all ORM classes."""
from ..database import Base  # noqa: F401

from .core import (  # noqa: F401
    Organization, BusinessUnit, BusinessService, Asset, AssetDependency,
)
from .security import (  # noqa: F401
    Vulnerability, Threat, Incident, Control, ControlAssessment, TelemetrySource,
)
from .risk import (  # noqa: F401
    FinancialAssumption, RiskSnapshot, RiskFinding, RiskContribution,
)
from .decisions import (  # noqa: F401
    MitigationAction, InvestmentOption, Scenario, Recommendation, Report,
)
from .frameworks import Framework, FrameworkControl, FrameworkMapping  # noqa: F401
from .users import User  # noqa: F401

__all__ = [
    "Organization", "BusinessUnit", "BusinessService", "Asset", "AssetDependency",
    "Vulnerability", "Threat", "Incident", "Control", "ControlAssessment",
    "TelemetrySource", "FinancialAssumption", "RiskSnapshot", "RiskFinding",
    "RiskContribution", "MitigationAction", "InvestmentOption", "Scenario",
    "Recommendation", "Report", "Framework", "FrameworkControl",
    "FrameworkMapping", "User",
]
