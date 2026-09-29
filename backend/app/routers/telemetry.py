"""Telemetry / data-source connectors (all simulated for the demo)."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from .. import models
from ..database import get_db
from ..deps import get_current_user, current_org

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get("")
def list_sources(db=Depends(get_db), user=Depends(get_current_user),
                 org_id: int = Depends(current_org)):
    rows = db.query(models.TelemetrySource).filter_by(org_id=org_id).all()
    sources = [{
        "id": s.id, "source_type": s.source_type, "name": s.name, "vendor": s.vendor,
        "status": s.status, "record_count": s.record_count, "health": s.health,
        "last_sync": s.last_sync.isoformat() if s.last_sync else None,
        "description": s.description,
    } for s in rows]
    return {"count": len(sources), "sources": sources,
            "note": "All connectors are simulated feeds over synthetic demo data."}
