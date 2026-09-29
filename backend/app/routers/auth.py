"""Authentication routes: register (new company), login, current user, demo list.

Multi-tenant model: every user belongs to exactly one organization. Registration
creates a fresh organization + its first admin user; login/me always report the
caller's organization so the frontend can show tenant identity. The tenant used
for data access is derived server-side from the user (see deps.current_org) and
is never taken from the client.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status

from .. import auth, models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..seed.loader import DEMO_USERS

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_payload(db, user) -> dict:
    """Serialize a user together with its organization identity."""
    org = db.query(models.Organization).get(user.org_id) if user.org_id else None
    return {
        "id": user.id, "username": user.username, "name": user.name, "role": user.role,
        "org_id": user.org_id,
        "organization": org.name if org else None,
        "is_demo": bool(org.is_demo) if org else False,
    }


@router.post("/register", response_model=schemas.LoginResponse, status_code=status.HTTP_201_CREATED)
def register(body: schemas.RegisterRequest, db=Depends(get_db)):
    """Create a new company (organization) and its first admin, then sign them in.

    The new organization starts EMPTY — it does not receive any demo data.
    """
    username = body.username.strip().lower()
    if db.query(models.User).filter_by(username=username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="That username is already taken.")

    org = models.Organization(
        name=body.company_name.strip(),
        sector=(body.sector.strip() or "Unspecified"),
        description="", is_demo=False,
    )
    db.add(org)
    db.flush()  # assign org.id

    user = models.User(
        org_id=org.id, username=username,
        password_hash=auth.hash_password(body.password),
        name=body.admin_name.strip(), role="ciso",  # first admin gets full access
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_token(user.id, user.username, user.role)
    return {"token": token, "user": _user_payload(db, user)}


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, db=Depends(get_db)):
    username = body.username.strip().lower()
    user = db.query(models.User).filter_by(username=username).first()
    if user is None or not auth.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password.")
    token = auth.create_token(user.id, user.username, user.role)
    return {"token": token, "user": _user_payload(db, user)}


@router.get("/me")
def me(db=Depends(get_db), user=Depends(get_current_user)):
    return _user_payload(db, user)


@router.get("/demo-users")
def demo_users():
    """Non-sensitive listing to populate the demo login screen (no passwords stored here)."""
    return [{"username": u, "password": pw, "name": name, "role": role}
            for (u, pw, name, role) in DEMO_USERS]
