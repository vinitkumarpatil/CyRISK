"""Evidence-based reporting routes: generate structured JSON or PDF reports.

Every figure in a report is assembled from the computed engine result, the
recommendation engine, the framework assessment, and (optionally) the optimizer
output — all traceable to the model, all carrying the synthetic-data disclaimer.
"""
from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .. import models, schemas, config
from ..database import get_db
from ..deps import (get_current_user, current_org, get_result,
                    get_recommendations, get_frameworks, get_state, options_for)
from ..engine import reports as reports_engine, optimizer as optimizer_engine

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = config.BASE_DIR / "generated_reports"


@router.post("/generate")
def generate(body: schemas.ReportRequest, db=Depends(get_db),
             user=Depends(get_current_user), org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    recommendations = get_recommendations(db, org_id)
    frameworks = get_frameworks(db, org_id)

    optimizer_out = None
    if body.budget_inr:
        optimizer_out = optimizer_engine.optimize(
            get_state(db, org_id), options_for(db, org_id), body.budget_inr)

    payload = reports_engine.build_report(
        result, recommendations, frameworks, optimizer_out, kind=body.kind)

    report = models.Report(org_id=org_id, title=payload["title"], kind=body.kind,
                           fmt=body.fmt, payload=payload)
    db.add(report)
    db.flush()  # assign id for filename

    if body.fmt == "pdf":
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            path = REPORTS_DIR / f"report_{org_id}_{report.id}.pdf"
            reports_engine.render_pdf(payload, str(path))
            report.file_path = str(path)
        except Exception as exc:  # reportlab missing or render failure
            db.rollback()
            raise HTTPException(status_code=500,
                                detail=f"PDF generation failed: {exc}") from exc
    db.commit()

    return {"status": "generated", "id": report.id, "kind": report.kind,
            "fmt": report.fmt, "title": report.title,
            "download_url": f"/api/reports/{report.id}/download",
            "payload": payload}


@router.get("")
def list_reports(db=Depends(get_db), user=Depends(get_current_user),
                 org_id: int = Depends(current_org)):
    rows = (db.query(models.Report).filter_by(org_id=org_id)
            .order_by(models.Report.created_at.desc()).limit(50).all())
    return {"count": len(rows), "reports": [
        {"id": r.id, "title": r.title, "kind": r.kind, "fmt": r.fmt,
         "created_at": r.created_at.isoformat() if r.created_at else None,
         "has_file": bool(r.file_path),
         "download_url": f"/api/reports/{r.id}/download"} for r in rows]}


@router.get("/{report_id}")
def get_report(report_id: int, db=Depends(get_db), user=Depends(get_current_user),
               org_id: int = Depends(current_org)):
    r = db.query(models.Report).filter_by(id=report_id, org_id=org_id).first()
    if r is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return {"id": r.id, "title": r.title, "kind": r.kind, "fmt": r.fmt,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "payload": r.payload}


@router.get("/{report_id}/download")
def download_report(report_id: int, db=Depends(get_db), user=Depends(get_current_user),
                    org_id: int = Depends(current_org)):
    r = db.query(models.Report).filter_by(id=report_id, org_id=org_id).first()
    if r is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    if r.fmt == "pdf" and r.file_path:
        import os
        if not os.path.exists(r.file_path):
            raise HTTPException(status_code=404, detail="Report file missing on server.")
        return FileResponse(r.file_path, media_type="application/pdf",
                            filename=f"cyberrisk_report_{r.id}.pdf")
    return {"id": r.id, "title": r.title, "kind": r.kind, "fmt": r.fmt, "payload": r.payload}
