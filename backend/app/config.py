"""Application configuration (env-driven, no secrets committed)."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Core settings -----------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'cyberrisk.db').as_posix()}")
APP_NAME = "CyberRisk Quant Platform"
APP_ENV = os.getenv("APP_ENV", "development")

# CORS: comma-separated origins. Vite dev server defaults included.
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
).split(",")

# --- Auth (lightweight, demo-only) -------------------------------------------
# NOTE: demo-grade token signing key. Override in .env for any real deployment.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-in-production")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))

# --- Optional LLM for NL assistant (deterministic fallback if unset) ---------
# The assistant NEVER lets an LLM invent financial numbers; the LLM only
# rephrases answers computed from real model data. Left disabled by default.
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# --- File upload limits (safe import handling) -------------------------------
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB
ALLOWED_UPLOAD_EXT = {".csv", ".json"}

# --- Financial modelling constants (rupees) ----------------------------------
CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
