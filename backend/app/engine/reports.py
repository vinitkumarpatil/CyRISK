"""Evidence-based risk reporting: structured JSON + optional PDF.

Reports are assembled purely from the computed engine result / recommendations /
framework assessment / optimizer output. Every figure is traceable to the model
and carries a "modelled estimate on synthetic demo data" disclaimer. The PDF is
rendered with reportlab (open-source); if reportlab is unavailable the JSON
report is still produced.
"""
from __future__ import annotations
from datetime import datetime, timezone

from . import fmt_inr

DISCLAIMER = ("All figures are MODELLED ESTIMATES computed from synthetic demo data. "
              "This report is not a compliance certification, audit attestation, or a "
              "statement of actual/booked losses.")

METHODOLOGY = {
    "criticality": "criticality = 100 × Σ(weight_i × normalised_factor_i)",
    "control_effectiveness": "effectiveness = (Σ weight×factor) × (1 − incident_penalty)",
    "sle": "SLE = Σ impact components (asset, downtime, data-breach, recovery, regulatory, reputation)",
    "ale": "ALE = SLE × ARO (annual rate of occurrence, control- and ML-adjusted)",
    "var": "Value-at-Risk via Monte-Carlo: Poisson(frequency) × lognormal(severity)",
    "risk_score": "risk score = weighted blend of ALE, control-gap and critical-vuln components",
    "rosi": "ROSI = (annual ALE reduction − cost) / cost",
}


def build_report(result: dict, recommendations: list | None = None,
                 frameworks: list | None = None, optimizer: dict | None = None,
                 kind: str = "executive") -> dict:
    """Assemble a structured, traceable report payload."""
    ent = result["enterprise"]
    org = result.get("org", {})
    headline = (f"Enterprise cyber risk is {ent['risk_band']} "
                f"({ent['risk_score']}/100). Modelled Expected Annual Loss is "
                f"{fmt_inr(ent['total_ale_inr'])}, with 95% Value-at-Risk of "
                f"{fmt_inr(ent['var95_inr'])}.")

    payload = {
        "kind": kind,
        "title": f"{'Executive' if kind == 'executive' else 'Technical'} Cyber Risk Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organization": org,
        "disclaimer": DISCLAIMER,
        "executive_summary": {
            "risk_score": ent["risk_score"], "risk_band": ent["risk_band"],
            "total_ale_inr": ent["total_ale_inr"], "total_ale_display": fmt_inr(ent["total_ale_inr"]),
            "total_exposure_inr": ent["total_exposure_inr"],
            "total_exposure_display": fmt_inr(ent["total_exposure_inr"]),
            "var95_inr": ent["var95_inr"], "var95_display": fmt_inr(ent["var95_inr"]),
            "var99_inr": ent["var99_inr"], "var99_display": fmt_inr(ent["var99_inr"]),
            "avg_control_effectiveness": ent["avg_control_effectiveness"],
            "open_vulns": ent["open_vulns"], "critical_vulns": ent["critical_vulns"],
            "headline": headline,
        },
        "top_contributors": [
            {"label": c["label"], "ale_inr": c["ale_inr"], "ale_display": fmt_inr(c["ale_inr"]),
             "share": c["share"], "severity": c["severity"], "category": c["category"],
             "control_weakness": c.get("control_weakness", ""),
             "recommended_action": c.get("recommended_action", "")}
            for c in result.get("contributors", [])[:10]
        ],
        "risk_by_business_unit": [
            {"business_unit": b["business_unit"], "ale_inr": b["ale_inr"],
             "ale_display": fmt_inr(b["ale_inr"]), "share": b["share"]}
            for b in result.get("by_business_unit", [])
        ],
        "risk_by_category": [
            {"category": c["category"], "ale_inr": c["ale_inr"],
             "ale_display": fmt_inr(c["ale_inr"]), "share": c["share"]}
            for c in result.get("by_category", [])
        ],
        "weakest_controls": [
            {"key": c["key"], "name": c["name"], "effectiveness": c["effectiveness"],
             "rating": c["rating"]} for c in result.get("controls", [])[:5]
        ],
        "recommendations": [
            {"title": r["title"], "priority": r["priority"], "cost_inr": r["cost_inr"],
             "cost_display": fmt_inr(r["cost_inr"]),
             "expected_ale_reduction_inr": r["expected_ale_reduction_inr"],
             "expected_ale_reduction_display": fmt_inr(r["expected_ale_reduction_inr"]),
             "rosi_percent": r["rosi_percent"], "why": r.get("rationale", {}).get("why", "")}
            for r in (recommendations or [])[:8]
        ],
        "framework_assessment": [
            {"key": f["key"], "name": f["name"], "assessment_index": f["assessment_index"],
             "coverage_pct": f["coverage_pct"], "counts": f["counts"],
             "disclaimer": f.get("disclaimer", "")} for f in (frameworks or [])
        ],
        "optimization": ({
            "budget_inr": optimizer["budget_inr"], "budget_display": fmt_inr(optimizer["budget_inr"]),
            "selected_count": optimizer["selected_count"],
            "total_cost_inr": optimizer["total_cost_inr"],
            "total_cost_display": fmt_inr(optimizer["total_cost_inr"]),
            "joint_ale_reduction_inr": optimizer["joint_ale_reduction_inr"],
            "joint_ale_reduction_display": fmt_inr(optimizer["joint_ale_reduction_inr"]),
            "portfolio_rosi_percent": optimizer["portfolio_rosi_percent"],
            "selected": [{"name": s["name"], "cost_display": fmt_inr(s["cost_inr"])}
                         for s in optimizer.get("selected", [])],
        } if optimizer else None),
        "methodology": METHODOLOGY,
    }
    return payload


def render_pdf(payload: dict, path: str) -> str:
    """Render the report payload to a PDF at `path` using reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Disc", parent=styles["Normal"], fontSize=7.5,
                              textColor=colors.grey, leading=10))
    styles.add(ParagraphStyle(name="H1c", parent=styles["Title"], fontSize=18,
                              textColor=colors.HexColor("#0b3d91")))
    es = payload["executive_summary"]
    org = payload.get("organization", {})
    story = []

    def h(text, size=13):
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(text, ParagraphStyle(
            name="h", parent=styles["Heading2"], fontSize=size,
            textColor=colors.HexColor("#0b3d91"))))

    def table(rows, widths, header=True):
        t = Table(rows, colWidths=widths, hAlign="LEFT")
        st = [("FONTSIZE", (0, 0), (-1, -1), 8.5),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6fc")])]
        if header:
            st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3d91")),
                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        t.setStyle(TableStyle(st))
        story.append(t)

    story.append(Paragraph(payload["title"], styles["H1c"]))
    story.append(Paragraph(f"{org.get('name', 'Organization')} — {org.get('sector', '')}",
                           styles["Normal"]))
    story.append(Paragraph(f"Generated: {payload['generated_at']}", styles["Disc"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(es["headline"], styles["Normal"]))
    # __APPEND_REPORT_PDF2__
    h("Key Risk Metrics")
    table([
        ["Metric", "Value"],
        ["Enterprise Risk Score", f"{es['risk_score']}/100 ({es['risk_band']})"],
        ["Expected Annual Loss (ALE)", es["total_ale_display"]],
        ["Aggregate Single-Event Exposure", es["total_exposure_display"]],
        ["Value-at-Risk (95%)", es["var95_display"]],
        ["Value-at-Risk (99%)", es["var99_display"]],
        ["Avg Control Effectiveness", f"{es['avg_control_effectiveness']:.0%}"],
        ["Open / Critical Vulnerabilities", f"{es['open_vulns']} / {es['critical_vulns']}"],
    ], [70 * mm, 90 * mm])

    if payload.get("top_contributors"):
        h("Top Risk Contributors")
        rows = [["Risk Driver", "Modelled ALE", "Share"]]
        rows += [[c["label"][:60], c["ale_display"], f"{c['share']:.1%}"]
                 for c in payload["top_contributors"][:8]]
        table(rows, [110 * mm, 35 * mm, 20 * mm])

    if payload.get("recommendations"):
        h("Prioritised Recommendations")
        rows = [["Action", "Cost", "ALE Reduction", "ROSI"]]
        rows += [[r["title"][:48], r["cost_display"], r["expected_ale_reduction_display"],
                  f"{r['rosi_percent']}%" if r.get("rosi_percent") is not None else "—"]
                 for r in payload["recommendations"][:6]]
        table(rows, [78 * mm, 28 * mm, 40 * mm, 20 * mm])

    if payload.get("optimization"):
        o = payload["optimization"]
        h("Budget-Constrained Optimization")
        table([
            ["Parameter", "Value"],
            ["Budget", o["budget_display"]],
            ["Selected investments", str(o["selected_count"])],
            ["Total cost", o["total_cost_display"]],
            ["Joint ALE reduction", o["joint_ale_reduction_display"]],
            ["Portfolio ROSI", f"{o['portfolio_rosi_percent']}%"
             if o.get("portfolio_rosi_percent") is not None else "—"],
        ], [70 * mm, 90 * mm])

    if payload.get("framework_assessment"):
        h("Framework Assessment (mapping, not certification)")
        rows = [["Framework", "Assessment Index", "Coverage"]]
        rows += [[f["name"][:46], f"{f['assessment_index']}/100", f"{f['coverage_pct']}%"]
                 for f in payload["framework_assessment"]]
        table(rows, [110 * mm, 35 * mm, 25 * mm])

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(payload["disclaimer"], styles["Disc"]))
    SimpleDocTemplate(path, pagesize=A4, title=payload["title"],
                      topMargin=16 * mm, bottomMargin=16 * mm).build(story)
    return path

