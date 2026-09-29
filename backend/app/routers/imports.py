"""Safe data import routes (CSV / JSON) for vulnerabilities and assets.

Security posture:
 - extension allow-list (.csv/.json) and a hard byte-size cap (config.MAX_UPLOAD_BYTES)
 - a row-count cap to bound memory/CPU
 - every field is validated and coerced; strings are length-capped and stripped;
   numerics are bounded; enums are checked against allow-lists
 - imported rows are scoped to the current org and marked is_demo=False
 - nothing from the file is ever executed or used in a raw SQL string (ORM only)
"""
from __future__ import annotations
import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from .. import models, config
from ..database import get_db
from ..deps import get_current_user, require_roles, current_org, invalidate

router = APIRouter(prefix="/api/imports", tags=["imports"])

MAX_ROWS = 5000
_STR_CAP = 256
SEVERITIES = {"Critical", "High", "Medium", "Low"}
VSTATUS = {"open", "remediating", "closed"}
VCATEGORY = {"software", "config", "patch", "web", "network", "identity"}
ASSET_TYPES = {"server", "database", "endpoint", "network", "saas", "app"}
ENVIRONMENTS = {"production", "staging", "development", "dr"}


def _clean_str(v, cap: int = _STR_CAP) -> str:
    return str(v if v is not None else "").strip()[:cap]


def _num(v, lo: float, hi: float, default: float) -> float:
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


def _boolean(v) -> bool:
    return _clean_str(v).lower() in ("1", "true", "yes", "y", "t")


def _ext_of(filename: str) -> str:
    name = (filename or "").lower()
    return name[name.rfind("."):] if "." in name else ""


# __APPEND_IMPORTS__


async def _read_rows(file: UploadFile) -> list[dict]:
    """Validate size/extension, then parse the upload into a list of row dicts."""
    ext = _ext_of(file.filename)
    if ext not in config.ALLOWED_UPLOAD_EXT:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type '{ext}'. Allowed: "
                                   f"{', '.join(sorted(config.ALLOWED_UPLOAD_EXT))}.")
    raw = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(raw) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413,
                            detail=f"File exceeds {config.MAX_UPLOAD_BYTES} bytes.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    if ext == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc
        if isinstance(data, dict):
            data = data.get("rows") or data.get("data") or [data]
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="JSON must be a list of records.")
        rows = [r for r in data if isinstance(r, dict)]
    else:
        rows = list(csv.DictReader(io.StringIO(text)))

    if not rows:
        raise HTTPException(status_code=400, detail="No records found in file.")
    if len(rows) > MAX_ROWS:
        raise HTTPException(status_code=413,
                            detail=f"Too many rows ({len(rows)}); limit is {MAX_ROWS}.")
    return rows


# __APPEND_IMPORTS2__


def _import_vulns(db, org_id: int, rows: list[dict]) -> dict:
    valid_assets = {a.id for a in db.query(models.Asset.id).filter_by(org_id=org_id)}
    imported, skipped = 0, []
    for i, r in enumerate(rows, 1):
        title = _clean_str(r.get("title"))
        if not title:
            skipped.append({"row": i, "reason": "missing title"})
            continue
        try:
            asset_id = int(r.get("asset_id"))
        except (TypeError, ValueError):
            skipped.append({"row": i, "reason": "invalid asset_id"})
            continue
        if asset_id not in valid_assets:
            skipped.append({"row": i, "reason": f"asset_id {asset_id} not in this org"})
            continue
        sev = _clean_str(r.get("severity"), 16).title()
        cat = _clean_str(r.get("category"), 24).lower()
        status = _clean_str(r.get("status"), 16).lower()
        db.add(models.Vulnerability(
            org_id=org_id, asset_id=asset_id, cve_id=_clean_str(r.get("cve_id"), 32),
            title=title, cvss=_num(r.get("cvss"), 0.0, 10.0, 5.0),
            severity=sev if sev in SEVERITIES else "Medium",
            category=cat if cat in VCATEGORY else "software",
            status=status if status in VSTATUS else "open",
            exploit_available=_boolean(r.get("exploit_available")),
            internet_exposed=_boolean(r.get("internet_exposed")),
            patch_available=_boolean(r.get("patch_available")) if r.get("patch_available") is not None else True,
            age_days=int(_num(r.get("age_days"), 0, 100000, 30)),
            remediation_cost_inr=_num(r.get("remediation_cost_inr"), 0, 1e11, 200000.0),
            source=_clean_str(r.get("source"), 64) or "Imported", is_demo=False))
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}


def _import_assets(db, org_id: int, rows: list[dict]) -> dict:
    imported, skipped = 0, []
    for i, r in enumerate(rows, 1):
        name = _clean_str(r.get("name"))
        if not name:
            skipped.append({"row": i, "reason": "missing name"})
            continue
        atype = _clean_str(r.get("asset_type"), 24).lower()
        env = _clean_str(r.get("environment"), 24).lower()
        db.add(models.Asset(
            org_id=org_id, name=name,
            asset_type=atype if atype in ASSET_TYPES else "server",
            environment=env if env in ENVIRONMENTS else "production",
            ip_or_host=_clean_str(r.get("ip_or_host"), 128),
            internet_facing=_boolean(r.get("internet_facing")),
            business_value_inr=_num(r.get("business_value_inr"), 0, 1e12, 0.0),
            revenue_impact_per_day_inr=_num(r.get("revenue_impact_per_day_inr"), 0, 1e11, 0.0),
            data_sensitivity=int(_num(r.get("data_sensitivity"), 0, 5, 1)),
            operational_criticality=int(_num(r.get("operational_criticality"), 0, 5, 1)),
            regulatory_importance=int(_num(r.get("regulatory_importance"), 0, 5, 1)),
            records_count=int(_num(r.get("records_count"), 0, 1e10, 0)),
            owner=_clean_str(r.get("owner"), 64), is_demo=False))
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}


_IMPORTERS = {"vulnerabilities": _import_vulns, "assets": _import_assets}

# __APPEND_IMPORTS3__

_TEMPLATES = {
    "vulnerabilities": {
        "required": ["asset_id", "title"],
        "optional": ["cve_id", "cvss", "severity", "category", "status",
                     "exploit_available", "internet_exposed", "patch_available",
                     "age_days", "remediation_cost_inr", "source"],
        "enums": {"severity": sorted(SEVERITIES), "status": sorted(VSTATUS),
                  "category": sorted(VCATEGORY)},
        "note": "asset_id must reference an existing asset in the current organization.",
    },
    "assets": {
        "required": ["name"],
        "optional": ["asset_type", "environment", "ip_or_host", "internet_facing",
                     "business_value_inr", "revenue_impact_per_day_inr", "data_sensitivity",
                     "operational_criticality", "regulatory_importance", "records_count", "owner"],
        "enums": {"asset_type": sorted(ASSET_TYPES), "environment": sorted(ENVIRONMENTS)},
        "note": "data_sensitivity / operational_criticality / regulatory_importance are 0–5.",
    },
}


@router.get("/template/{kind}")
def template(kind: str, user=Depends(get_current_user)):
    if kind not in _TEMPLATES:
        raise HTTPException(status_code=404,
                            detail=f"Unknown import kind. Options: {', '.join(_TEMPLATES)}.")
    return {"kind": kind, **_TEMPLATES[kind],
            "formats": sorted(config.ALLOWED_UPLOAD_EXT),
            "max_bytes": config.MAX_UPLOAD_BYTES, "max_rows": MAX_ROWS}


@router.post("/{kind}")
async def import_data(kind: str, file: UploadFile = File(...), db=Depends(get_db),
                      user=Depends(require_roles("ciso", "analyst")),
                      org_id: int = Depends(current_org)):
    """Import validated records from an uploaded CSV/JSON file into the current org."""
    importer = _IMPORTERS.get(kind)
    if importer is None:
        raise HTTPException(status_code=404,
                            detail=f"Unknown import kind. Options: {', '.join(_IMPORTERS)}.")
    rows = await _read_rows(file)
    summary = importer(db, org_id, rows)
    invalidate(org_id)  # recompute risk with the imported data
    return {"status": "imported", "kind": kind, "total_rows": len(rows),
            "imported": summary["imported"], "skipped_count": len(summary["skipped"]),
            "skipped": summary["skipped"][:50],
            "note": "Risk figures recompute on the next request; imported rows are "
                    "flagged as non-demo data."}
