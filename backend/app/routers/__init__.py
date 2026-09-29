"""Router registry — import every APIRouter and expose them as ALL_ROUTERS."""
from . import (
    auth, demo, dashboard, risk, assets, vulnerabilities, controls, telemetry,
    scenarios, investments, optimizer, frameworks, recommendations, assistant,
    model_info, assumptions, reports, imports,
)

ALL_ROUTERS = [
    auth.router, demo.router, dashboard.router, risk.router, assets.router,
    vulnerabilities.router, controls.router, telemetry.router, scenarios.router,
    investments.router, optimizer.router, frameworks.router, recommendations.router,
    assistant.router, model_info.router, assumptions.router, reports.router,
    imports.router,
]
