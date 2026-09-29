"""Seed the fictional demo enterprise into the database (idempotent).

`seed_demo(db)` wipes prior demo rows and rebuilds the full Meghdoot Financial
Services Ltd instance, then creates demo login users. All data is synthetic.

Pattern: entities are declared with string "ref" keys in the seed modules;
here we insert + flush to get real ids, then resolve foreign keys via ref→id
maps. Nothing here is hardcoded into the risk numbers — the engine computes
those from this state.
"""
from __future__ import annotations
from datetime import datetime, timedelta

from .. import models
from ..auth import hash_password
from . import catalog, enterprise, investments, frameworks_catalog, vulns

# FK-safe deletion order for a full demo reset.
_RESET_ORDER = [
    models.RiskContribution, models.RiskFinding, models.RiskSnapshot,
    models.FrameworkMapping, models.FrameworkControl, models.Framework,
    models.Recommendation, models.Scenario, models.InvestmentOption,
    models.MitigationAction, models.Report,
    models.ControlAssessment, models.Control,
    models.Incident, models.Vulnerability, models.AssetDependency, models.Asset,
    models.TelemetrySource, models.Threat, models.FinancialAssumption,
    models.BusinessService, models.BusinessUnit, models.Organization,
]


def reset_demo(db) -> None:
    for model in _RESET_ORDER:
        db.query(model).delete()
    db.commit()


def seed_demo(db) -> dict:
    """Rebuild the demo enterprise. Returns a small summary dict."""
    reset_demo(db)

    org = models.Organization(
        name=enterprise.ORG["name"], sector=enterprise.ORG["sector"],
        description=enterprise.ORG["description"], is_demo=True,
    )
    db.add(org)
    db.flush()
    oid = org.id

    # --- Business units --------------------------------------------------
    bu_id: dict[str, int] = {}
    for ref, name, head in enterprise.BUSINESS_UNITS:
        bu = models.BusinessUnit(org_id=oid, name=name, head=head)
        db.add(bu)
        db.flush()
        bu_id[ref] = bu.id

    # --- Business services -----------------------------------------------
    svc_id: dict[str, int] = {}
    for ref, name, bu_ref, tier in enterprise.SERVICES:
        svc = models.BusinessService(org_id=oid, bu_id=bu_id.get(bu_ref), name=name,
                                     criticality_tier=tier)
        db.add(svc)
        db.flush()
        svc_id[ref] = svc.id

    # --- Assets ----------------------------------------------------------
    asset_id: dict[str, int] = {}
    for a in enterprise.ASSETS:
        row = models.Asset(
            org_id=oid, bu_id=bu_id.get(a["bu"]), service_id=svc_id.get(a["svc"]),
            name=a["name"], asset_type=a["type"], environment=a["env"],
            internet_facing=a["net"], business_value_inr=a["bv"],
            revenue_impact_per_day_inr=a["rev"], data_sensitivity=a["ds"],
            operational_criticality=a["oc"], regulatory_importance=a["ri"],
            records_count=a["rec"], owner=a["owner"], is_demo=True,
        )
        db.add(row)
        db.flush()
        asset_id[a["ref"]] = row.id

    # --- Asset dependencies ----------------------------------------------
    for src, dst, dtype in enterprise.DEPENDENCIES:
        if src in asset_id and dst in asset_id:
            db.add(models.AssetDependency(asset_id=asset_id[src],
                                          depends_on_id=asset_id[dst], dependency_type=dtype))

    # --- Vulnerabilities -------------------------------------------------
    now = datetime.utcnow()
    src_label = {
        "vuln_scanner": "Nessus / OpenVAS (simulated)", "iam": "Keycloak / AD (simulated)",
        "cspm": "Prowler (simulated)", "siem": "Wazuh / ELK (simulated)",
        "edr": "OpenEDR / Wazuh (simulated)", "threat_intel": "MISP (simulated)",
    }
    n_vulns = 0
    for v in vulns.VULNERABILITIES:
        if v["asset"] not in asset_id:
            continue
        db.add(models.Vulnerability(
            org_id=oid, asset_id=asset_id[v["asset"]], cve_id=v["cve"], title=v["title"],
            cvss=v["cvss"], severity=v["severity"], exploit_available=v["exploit"],
            internet_exposed=v["net"], status=v["status"], category=v["category"],
            patch_available=v["patch"], age_days=v["age"], remediation_cost_inr=v["cost"],
            source=src_label.get(v["source"], v["source"]),
            discovered_at=now - timedelta(days=v["age"]), is_demo=True,
        ))
        n_vulns += 1

    # --- Historical incidents --------------------------------------------
    for i in vulns.INCIDENTS:
        db.add(models.Incident(
            org_id=oid, asset_id=asset_id.get(i["asset"]), title=i["title"],
            category=i["category"], occurred_at=now - timedelta(days=i["days_ago"]),
            financial_impact_inr=i["fin"], downtime_hours=i["downtime"],
            records_affected=i["records"], root_cause=i["root_cause"], is_demo=True,
        ))

    # --- Controls --------------------------------------------------------
    for key, name, cat, cfg, cov, comp, mat, mon, desc in catalog.CONTROLS:
        db.add(models.Control(
            org_id=oid, key=key, name=name, category=cat, config_strength=cfg,
            coverage=cov, compliance_status=comp, maturity=mat, monitored=mon,
            description=desc, is_demo=True,
        ))

    # --- Threats ---------------------------------------------------------
    for name, actor, cat, ttp, lw, rel, desc in catalog.THREATS:
        db.add(models.Threat(
            org_id=oid, name=name, threat_actor=actor, category=cat, ttp=ttp,
            likelihood_weight=lw, relevance=rel, description=desc, is_demo=True,
        ))

    # --- Telemetry sources (counts wired to seeded volume) ---------------
    n_assets = len(asset_id)
    for stype, name, vendor, status, rec, desc in catalog.TELEMETRY:
        count = n_vulns if stype == "vuln_scanner" else n_assets if stype == "asset_inventory" else rec
        db.add(models.TelemetrySource(
            org_id=oid, source_type=stype, name=name, vendor=vendor, status=status,
            record_count=count, description=desc, is_demo=True,
        ))

    # --- Financial assumptions (editable, transparent) -------------------
    for key, label, value, unit, cat, desc in catalog.ASSUMPTIONS:
        db.add(models.FinancialAssumption(
            org_id=oid, key=key, label=label, value=value, unit=unit,
            category=cat, description=desc, editable=True,
        ))

    # --- Investment options ----------------------------------------------
    for o in investments.INVESTMENT_OPTIONS:
        db.add(models.InvestmentOption(
            org_id=oid, key=o["key"], name=o["name"], category=o["category"],
            control_key=o["control_key"], action=o["action"], cost_inr=o["cost"],
            effort=o["effort"], params=o["params"], is_demo=True,
        ))

    # --- Frameworks + controls + mapping stubs ---------------------------
    # Mapping status is COMPUTED live from control effectiveness by the
    # frameworks engine; seeded rows start at the neutral "Review Required".
    for fw in frameworks_catalog.FRAMEWORKS:
        f = models.Framework(key=fw["key"], name=fw["name"],
                             full_name=fw["full_name"], version=fw["version"])
        db.add(f)
        db.flush()
        for ref, cat, title, internal_key in fw["controls"]:
            fc = models.FrameworkControl(
                framework_id=f.id, control_ref=ref, category=cat, title=title,
                internal_control_key=internal_key,
            )
            db.add(fc)
            db.flush()
            db.add(models.FrameworkMapping(
                org_id=oid, framework_control_id=fc.id, internal_control_key=internal_key,
                status="Review Required", editable=True,
            ))

    # __APPEND_LOADER__

    db.commit()
    _ensure_users(db, oid)
    return _summary(db, oid)


DEMO_USERS = [
    ("exec", "exec123", "Executive Demo", "executive"),
    ("ciso", "ciso123", "CISO Demo", "ciso"),
    ("analyst", "analyst123", "Analyst Demo", "analyst"),
]


def _ensure_users(db, org_id: int | None = None) -> None:
    """Create demo login users if absent and link them to the demo organization.

    Passwords are stored hashed. When org_id is not supplied (e.g. called at
    startup), the demo organization is resolved from the database, and any
    pre-existing demo user missing an org link is back-filled.
    """
    if org_id is None:
        demo_org = (db.query(models.Organization).filter_by(is_demo=True)
                    .order_by(models.Organization.id.asc()).first()
                    or db.query(models.Organization)
                    .order_by(models.Organization.id.asc()).first())
        org_id = demo_org.id if demo_org else None

    for username, pw, name, role in DEMO_USERS:
        existing = db.query(models.User).filter_by(username=username).first()
        if existing:
            if existing.org_id is None and org_id is not None:
                existing.org_id = org_id  # back-fill legacy demo user
            continue
        db.add(models.User(org_id=org_id, username=username,
                           password_hash=hash_password(pw), name=name, role=role))
    db.commit()


def _summary(db, oid: int) -> dict:
    q = lambda m: db.query(m).filter_by(org_id=oid).count()  # noqa: E731
    return {
        "org_id": oid,
        "business_units": q(models.BusinessUnit),
        "services": q(models.BusinessService),
        "assets": q(models.Asset),
        "vulnerabilities": q(models.Vulnerability),
        "incidents": q(models.Incident),
        "controls": q(models.Control),
        "threats": q(models.Threat),
        "telemetry_sources": q(models.TelemetrySource),
        "investment_options": q(models.InvestmentOption),
        "frameworks": db.query(models.Framework).count(),
    }
