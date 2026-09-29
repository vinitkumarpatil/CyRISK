"""Shared FastAPI dependencies: auth, org resolution, and a compute cache.

The full risk computation (including 5000-simulation Monte-Carlo VaR) is
relatively expensive, so results are cached per organization and invalidated
whenever underlying data changes (demo reload, telemetry simulation, imports,
assumption edits). Scenarios/optimizer operate on cloned state and never touch
this cache or the database.
"""
from __future__ import annotations
import threading

from fastapi import Depends, Header, HTTPException, status

from . import auth, models
from .database import get_db
from .engine import state as state_mod
from .engine import risk_engine, recommend, frameworks_data
from .seed import frameworks_catalog

_CACHE: dict[int, dict] = {}
_LOCK = threading.RLock()


def invalidate(org_id: int | None = None) -> None:
    with _LOCK:
        if org_id is None:
            _CACHE.clear()
        else:
            _CACHE.pop(org_id, None)


def _entry(org_id: int) -> dict:
    return _CACHE.setdefault(org_id, {})


# --- Auth dependencies -------------------------------------------------------
# Defined before current_org so tenant resolution can be derived from the
# authenticated user's SERVER-SIDE identity, never from client-supplied input.
def get_current_user(authorization: str | None = Header(default=None), db=Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing bearer token.",
                            headers={"WWW-Authenticate": "Bearer"})
    token = authorization.split(" ", 1)[1].strip()
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token.",
                            headers={"WWW-Authenticate": "Bearer"})
    user = db.query(models.User).get(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user.")
    return user


def require_roles(*roles: str):
    def _dep(user=Depends(get_current_user)):
        if roles and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Requires role: {', '.join(roles)}.")
        return user
    return _dep


def current_org(user=Depends(get_current_user)) -> int:
    """Resolve the active tenant strictly from the authenticated user.

    The organization id comes from the server-side user record loaded via the
    bearer token — NEVER from a query param, body, or header the client controls.
    Every data route depends on this, so no request can reach another tenant's
    rows by supplying a different organization_id.
    """
    if user.org_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Your account is not linked to an organization.")
    return user.org_id


def get_state(db, org_id: int) -> dict:
    with _LOCK:
        e = _entry(org_id)
        if "state" not in e:
            e["state"] = state_mod.build_state(db, org_id)
        return e["state"]


def get_result(db, org_id: int) -> dict:
    with _LOCK:
        e = _entry(org_id)
        if "result" not in e:
            e["result"] = risk_engine.compute(get_state(db, org_id))
        return e["result"]


# __APPEND_DEPS__


def options_for(db, org_id: int) -> list:
    """Load InvestmentOption rows as engine-shaped option dicts."""
    rows = db.query(models.InvestmentOption).filter_by(org_id=org_id).all()
    return [{"key": o.key, "name": o.name, "category": o.category,
             "control_key": o.control_key, "action": o.action, "cost": o.cost_inr,
             "effort": o.effort, "params": o.params or {}} for o in rows]


def get_recommendations(db, org_id: int) -> list:
    with _LOCK:
        e = _entry(org_id)
        if "recommendations" not in e:
            e["recommendations"] = recommend.recommend(
                get_state(db, org_id), options_for(db, org_id),
                baseline=get_result(db, org_id))
        return e["recommendations"]


def get_frameworks(db, org_id: int) -> list:
    with _LOCK:
        e = _entry(org_id)
        if "frameworks" not in e:
            result = get_result(db, org_id)
            ceff = {c["key"]: c["effectiveness"] for c in result["controls"]}
            e["frameworks"] = frameworks_data.assess_frameworks(
                frameworks_catalog.FRAMEWORKS, ceff)
        return e["frameworks"]


# --- Auth dependencies moved above current_org (see top of module) -----------
