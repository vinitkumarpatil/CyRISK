"""Deterministic natural-language query layer for the risk data.

CRITICAL: every number returned here is read directly from the computed risk
result / recommendations — this layer NEVER invents financial figures. An
optional LLM (disabled by default) may only rephrase text; the numbers are
always sourced from the model. Intent detection is keyword/regex based.
"""
from __future__ import annotations
import re

from . import fmt_inr

_CR = 10_000_000.0
_LAKH = 100_000.0


def parse_amount(text: str) -> float | None:
    """Extract an INR amount, understanding crore/lakh and Indian digit grouping."""
    t = text.lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|l|k|thousand)?", t)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or ""
    if unit in ("crore", "cr"):
        return val * _CR
    if unit in ("lakh", "lac", "l"):
        return val * _LAKH
    if unit in ("k", "thousand"):
        return val * 1_000.0
    # bare number: assume rupees only if large, else treat as crore for demo phrasing
    return val if val >= 100000 else val * _CR


def _has(q: str, *words) -> bool:
    return any(w in q for w in words)


# __APPEND_NLQ__


def answer(question: str, result: dict, recommendations: list | None = None,
           frameworks: list | None = None) -> dict:
    """Route a question to a deterministic answer computed from `result`."""
    q = (question or "").lower().strip()
    ent = result["enterprise"]
    recommendations = recommendations or []

    def resp(intent, text, data=None, suggest="optimize"):
        return {"intent": intent, "answer": text, "data": data or {},
                "numbers_source": "computed risk model (synthetic demo data)"}

    if _has(q, "optimize", "budget", "invest", "allocate", "spend"):
        amt = parse_amount(q)
        return {"intent": "optimize_budget", "answer":
                (f"Run the optimizer with a budget of {fmt_inr(amt)}." if amt else
                 "Specify a budget (e.g. ₹1 crore) to optimize the investment portfolio."),
                "budget_inr": amt, "action_required": "run_optimizer",
                "numbers_source": "computed risk model (synthetic demo data)"}

    if _has(q, "risk score", "overall risk", "risk band", "how risky", "posture"):
        return resp("risk_score",
                    f"Enterprise risk score is {ent['risk_score']}/100 ({ent['risk_band']}).",
                    {"risk_score": ent["risk_score"], "risk_band": ent["risk_band"],
                     "breakdown": ent["risk_score_breakdown"]})

    if _has(q, "var", "value at risk", "worst case", "worst-case", "tail"):
        return resp("value_at_risk",
                    f"Modelled annual Value-at-Risk: 95% {fmt_inr(ent['var95_inr'])}, "
                    f"99% {fmt_inr(ent['var99_inr'])} (Monte-Carlo, {ent['var_detail']['simulations']} sims).",
                    {"var95_inr": ent["var95_inr"], "var99_inr": ent["var99_inr"],
                     "detail": ent["var_detail"]})

    if _has(q, "total", "expected annual loss", "expected loss", "ale", "eal", "how much", "exposure"):
        return resp("total_ale",
                    f"Expected Annual Loss (ALE) is {fmt_inr(ent['total_ale_inr'])}; "
                    f"aggregate single-event exposure is {fmt_inr(ent['total_exposure_inr'])}. "
                    f"These are modelled estimates.",
                    {"total_ale_inr": ent["total_ale_inr"], "total_exposure_inr": ent["total_exposure_inr"]})

    if _has(q, "top risk", "biggest", "top contributor", "main risk", "driver", "highest risk"):
        top = result["contributors"][:5]
        lines = "; ".join(f"{c['label']} ({fmt_inr(c['ale_inr'])})" for c in top)
        return resp("top_contributors", f"Top risk contributors: {lines}.", {"contributors": top})

    if _has(q, "weak control", "worst control", "control gap", "weakest", "control effectiveness"):
        weak = result["controls"][:5]
        lines = "; ".join(f"{c['name']} ({c['rating']}, {c['effectiveness']:.0%})" for c in weak)
        return resp("weak_controls", f"Weakest controls: {lines}.", {"controls": weak})

    if _has(q, "critical asset", "most important", "crown jewel", "which asset", "top asset"):
        assets = sorted(result["by_asset"], key=lambda a: a["ale_inr"], reverse=True)[:5]
        lines = "; ".join(f"{a['name']} ({fmt_inr(a['ale_inr'])})" for a in assets)
        return resp("top_assets", f"Highest-risk assets by ALE: {lines}.", {"assets": assets})

    if _has(q, "business unit", "department", "by unit", "which unit", "by bu"):
        return resp("by_business_unit",
                    "Risk by business unit: " +
                    "; ".join(f"{b['business_unit']} ({fmt_inr(b['ale_inr'])})" for b in result["by_business_unit"][:6]),
                    {"by_business_unit": result["by_business_unit"]})

    if _has(q, "category", "type of risk", "by category"):
        return resp("by_category",
                    "Risk by category: " +
                    "; ".join(f"{c['category']} ({fmt_inr(c['ale_inr'])})" for c in result["by_category"]),
                    {"by_category": result["by_category"]})

    if _has(q, "recommend", "what should", "how to reduce", "mitigat", "reduce risk", "priorit", "fix"):
        if not recommendations:
            return resp("recommendations", "Generate recommendations from the Investment Optimizer first.", {})
        top = recommendations[:5]
        lines = "; ".join(f"{r['title']} (−{fmt_inr(r['expected_ale_reduction_inr'])}, ROSI {r['rosi_percent']}%)" for r in top)
        return resp("recommendations", f"Top recommendations: {lines}.", {"recommendations": top})

    if frameworks and _has(q, "framework", "iso", "nist", "cis", "rbi", "sebi", "compliance", "coverage"):
        lines = "; ".join(f"{f['name']} (index {f['assessment_index']})" for f in frameworks)
        return resp("frameworks",
                    f"Framework assessment (not certification): {lines}.", {"frameworks": frameworks})

    return {"intent": "unknown",
            "answer": ("I can answer on risk score, expected annual loss, Value-at-Risk, top "
                       "contributors, weak controls, critical assets, risk by unit/category, "
                       "recommendations, framework coverage, and budget optimization."),
            "data": {}, "numbers_source": "computed risk model (synthetic demo data)"}
