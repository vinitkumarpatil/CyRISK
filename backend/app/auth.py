"""Lightweight auth utilities: password hashing + signed session tokens.

Deliberately dependency-free (stdlib only). Tokens are HMAC-signed JSON with an
expiry; suitable for a demo, not a substitute for a hardened IdP in production.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import time

from . import config

_PBKDF2_ITERS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERS)
    return f"pbkdf2${_PBKDF2_ITERS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iters, salt_hex, hash_hex = stored.split("$")
        if scheme != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(payload_b64: str) -> str:
    sig = hmac.new(config.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return _b64e(sig)


def create_token(user_id: int, username: str, role: str) -> str:
    exp = int(time.time()) + config.TOKEN_TTL_HOURS * 3600
    payload = {"sub": user_id, "username": username, "role": role, "exp": exp}
    payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{payload_b64}.{_sign(payload_b64)}"


def decode_token(token: str) -> dict | None:
    try:
        payload_b64, sig = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(payload_b64)):
        return None
    try:
        payload = json.loads(_b64d(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload
