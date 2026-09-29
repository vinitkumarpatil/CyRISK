"""Small shared helpers for the risk engine."""
from __future__ import annotations


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def saturating(value: float, ref: float) -> float:
    """Map [0, inf) -> [0, 1) smoothly; `ref` maps to 0.5."""
    if value <= 0 or ref <= 0:
        return 0.0
    return value / (value + ref)


def fmt_inr(amount: float) -> str:
    """Format rupees using the Indian crore/lakh convention."""
    if amount is None:
        return "₹0"
    a = float(amount)
    sign = "-" if a < 0 else ""
    a = abs(a)
    if a >= 1_00_00_000:
        return f"{sign}₹{a / 1_00_00_000:.2f} Cr"
    if a >= 1_00_000:
        return f"{sign}₹{a / 1_00_000:.2f} L"
    if a >= 1_000:
        return f"{sign}₹{a / 1_000:.1f} K"
    return f"{sign}₹{a:.0f}"


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def round_money(x: float) -> float:
    return round(float(x), 2)


def severity_rank(sev: str) -> int:
    order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    return order.get(sev, 0)
