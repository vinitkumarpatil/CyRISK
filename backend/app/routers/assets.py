"""Asset inventory + per-asset criticality drill-down."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from .. import models, schemas
from ..database import get_db
from ..deps import (get_current_user, current_org, get_result, get_state,
                    require_roles, invalidate)

router = APIRouter(prefix="/api/assets", tags=["assets"])

# Allow-lists mirror the import validator so a typed asset_type/environment
# always coerces to a value the engine understands.
ASSET_TYPES = {"server", "database", "endpoint", "network", "saas", "app"}
ENVIRONMENTS = {"production", "staging", "development", "dr"}


@router.post("", status_code=201)
def create_asset(body: schemas.AssetCreate, db=Depends(get_db),
                 user=Depends(require_roles("ciso", "analyst")),
                 org_id: int = Depends(current_org)):
    """Create a business asset in the caller's organization.

    The tenant (org_id) comes from the authenticated user's server-side identity
    via Depends(current_org); any org_id in the request body is ignored. Real
    (non-demo) assets are flagged is_demo=False, and the compute cache is
    invalidated so the new asset shows up in risk figures on the next read.
    """
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Asset name is required.")
    atype = body.asset_type.strip().lower()
    env = body.environment.strip().lower()
    asset = models.Asset(
        org_id=org_id, name=name,
        asset_type=atype if atype in ASSET_TYPES else "server",
        environment=env if env in ENVIRONMENTS else "production",
        ip_or_host=body.ip_or_host.strip()[:128],
        internet_facing=bool(body.internet_facing),
        business_value_inr=body.business_value_inr,
        revenue_impact_per_day_inr=body.revenue_impact_per_day_inr,
        data_sensitivity=body.data_sensitivity,
        operational_criticality=body.operational_criticality,
        regulatory_importance=body.regulatory_importance,
        records_count=body.records_count,
        owner=body.owner.strip()[:64],
        is_demo=False,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    invalidate(org_id)  # recompute risk so the new asset appears immediately
    return {"status": "created", "id": asset.id, "name": asset.name,
            "note": "Risk figures recompute on the next request."}


@router.get("")
def list_assets(db=Depends(get_db), user=Depends(get_current_user),
                org_id: int = Depends(current_org)):
    """Assets ranked by modelled ALE, with criticality score + tier."""
    result = get_result(db, org_id)
    crit = result["criticality_by_asset"]
    ale_by_asset = {a["asset_id"]: a for a in result["by_asset"]}
    out = []
    for a in get_state(db, org_id)["assets"]:
        agg = ale_by_asset.get(a["id"], {})
        cd = crit.get(a["id"], {})
        out.append({
            "id": a["id"], "name": a["name"], "asset_type": a["asset_type"],
            "environment": a["environment"], "bu_name": a["bu_name"],
            "service_name": a["service_name"], "internet_facing": a["internet_facing"],
            "owner": a["owner"], "records_count": a["records_count"],
            "business_value_inr": a["business_value_inr"],
            "criticality": cd.get("score", 0.0), "tier": cd.get("tier", "Low"),
            "ale_inr": agg.get("ale_inr", 0.0), "exposure_inr": agg.get("exposure_inr", 0.0),
            "vuln_count": agg.get("vuln_count", 0),
        })
    out.sort(key=lambda x: x["ale_inr"], reverse=True)
    return {"count": len(out), "assets": out}


@router.get("/{asset_id}")
def asset_detail(asset_id: int, db=Depends(get_db), user=Depends(get_current_user),
                 org_id: int = Depends(current_org)):
    result = get_result(db, org_id)
    state = get_state(db, org_id)
    asset = next((a for a in state["assets"] if a["id"] == asset_id), None)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    crit = result["criticality_by_asset"].get(asset_id, {})
    findings = [f for f in result["findings"] if f["asset_id"] == asset_id]
    findings.sort(key=lambda f: f["ale_inr"], reverse=True)
    return {
        "asset": asset,
        "criticality": crit,
        "ale_inr": round(sum(f["ale_inr"] for f in findings), 2),
        "exposure_inr": round(sum(f["sle_inr"] for f in findings), 2),
        "findings": findings,
        "ml_features": asset.get("_ml_features", {}),
    }


def _owned_asset(db, org_id: int, asset_id: int) -> models.Asset:
    """Fetch an asset ONLY if it belongs to the caller's org, else 404.

    This is the tenant-isolation guard for mutations: an asset id from another
    organization is indistinguishable from a non-existent one (404), so no
    cross-tenant existence is ever leaked, and demo data is fenced off from
    edits/deletes made through non-demo tenants.
    """
    asset = db.query(models.Asset).filter_by(id=asset_id, org_id=org_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    if asset.is_demo:
        # Meghdoot's showcase data stays exactly as seeded.
        raise HTTPException(status_code=403, detail="Demo assets are read-only.")
    return asset


@router.put("/{asset_id}")
def update_asset(asset_id: int, body: schemas.AssetUpdate, db=Depends(get_db),
                 user=Depends(require_roles("ciso", "analyst")),
                 org_id: int = Depends(current_org)):
    """Edit an existing asset in place (never creates a duplicate).

    Only the fields supplied in the body are changed; org ownership is enforced
    by _owned_asset, and the compute cache is invalidated so risk figures and
    counts refresh on the next read.
    """
    asset = _owned_asset(db, org_id, asset_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Asset name cannot be empty.")
        asset.name = name
    if "asset_type" in data:
        at = (data["asset_type"] or "").strip().lower()
        asset.asset_type = at if at in ASSET_TYPES else asset.asset_type
    if "environment" in data:
        env = (data["environment"] or "").strip().lower()
        asset.environment = env if env in ENVIRONMENTS else asset.environment
    if "ip_or_host" in data:
        asset.ip_or_host = (data["ip_or_host"] or "").strip()[:128]
    if "owner" in data:
        asset.owner = (data["owner"] or "").strip()[:64]
    for f in ("internet_facing", "business_value_inr", "revenue_impact_per_day_inr",
              "data_sensitivity", "operational_criticality", "regulatory_importance",
              "records_count"):
        if f in data and data[f] is not None:
            setattr(asset, f, data[f])
    db.commit()
    db.refresh(asset)
    invalidate(org_id)  # recompute risk with the corrected inputs
    return {"status": "updated", "id": asset.id, "name": asset.name,
            "note": "Risk figures recompute on the next request."}


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db=Depends(get_db),
                 user=Depends(require_roles("ciso", "analyst")),
                 org_id: int = Depends(current_org)):
    """Permanently delete an asset owned by the caller's org.

    Cascades remove the asset's vulnerabilities and dependency edges; we also
    clear inbound dependency edges (other assets that depended on this one) so
    no dangling references remain. Risk is recomputed on the next read.
    """
    asset = _owned_asset(db, org_id, asset_id)
    # Drop inbound dependency edges (the ORM cascade only covers the outbound side).
    db.query(models.AssetDependency).filter_by(depends_on_id=asset_id).delete(
        synchronize_session=False)
    name = asset.name
    db.delete(asset)
    db.commit()
    invalidate(org_id)  # refresh counts + risk so nothing stale remains
    return {"status": "deleted", "id": asset_id, "name": name,
            "note": "Risk figures recompute on the next request."}
