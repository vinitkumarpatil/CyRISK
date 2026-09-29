"""FastAPI application entrypoint for the CyberRisk Quant Platform.

Wires configuration, CORS, database init, first-run demo seeding, and all API
routers. Every protected route requires a bearer token (see routers/auth.py);
only the root and health endpoints are intentionally public (no sensitive data).
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, models  # noqa: F401  (importing models registers ORM classes)
from .database import init_db, SessionLocal
from .routers import ALL_ROUTERS
from .seed.loader import seed_demo, _ensure_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        if db.query(models.Organization).first() is None:
            seed_demo(db)        # first run: load the fictional demo enterprise
        else:
            _ensure_users(db)    # make sure demo logins always exist
    finally:
        db.close()
    yield


app = FastAPI(
    title=config.APP_NAME,
    version="1.0.0",
    description=("AI-powered continuous cyber risk quantification and investment "
                 "optimization. Converts security posture into ₹ financial risk "
                 "(SLE/ARO/ALE/VaR) with explainable, data-driven recommendations. "
                 "All figures are MODELLED ESTIMATES on SYNTHETIC demo data."),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in ALL_ROUTERS:
    app.include_router(_router)


@app.get("/", tags=["meta"])
def root():
    return {"app": config.APP_NAME, "version": "1.0.0", "status": "ok",
            "docs": "/docs", "health": "/api/health",
            "disclaimer": "Synthetic demo data; all figures are modelled estimates."}


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "healthy", "app": config.APP_NAME, "env": config.APP_ENV}
