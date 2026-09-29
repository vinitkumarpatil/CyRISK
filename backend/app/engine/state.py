"""Build an in-memory, JSON-friendly enterprise state from the database.

The engine operates purely on this state dict so scenarios can deep-copy and
mutate it without ever touching the database.
"""
from __future__ import annotations
import copy
from collections import defaultdict

from .. import models
from .financial import DEFAULT_ASSUMPTIONS


def build_state(db, org_id: int) -> dict:
    org = db.query(models.Organization).get(org_id)
    if org is None:
        raise ValueError(f"Organization {org_id} not found")

    bus = db.query(models.BusinessUnit).filter_by(org_id=org_id).all()
    services = db.query(models.BusinessService).filter_by(org_id=org_id).all()
    assets = db.query(models.Asset).filter_by(org_id=org_id).all()
    vulns = db.query(models.Vulnerability).filter_by(org_id=org_id).all()
    controls = db.query(models.Control).filter_by(org_id=org_id).all()
    threats = db.query(models.Threat).filter_by(org_id=org_id).all()
    incidents = db.query(models.Incident).filter_by(org_id=org_id).all()
    deps = db.query(models.AssetDependency).all()
    assumptions_rows = db.query(models.FinancialAssumption).filter_by(org_id=org_id).all()

    bu_name = {b.id: b.name for b in bus}
    svc_name = {s.id: s.name for s in services}
    dependents = defaultdict(int)
    for d in deps:
        dependents[d.depends_on_id] += 1

    assumptions = dict(DEFAULT_ASSUMPTIONS)
    for a in assumptions_rows:
        assumptions[a.key] = a.value

    def asset_dict(a):
        return {
            "id": a.id, "name": a.name, "asset_type": a.asset_type, "environment": a.environment,
            "bu_id": a.bu_id, "bu_name": bu_name.get(a.bu_id, "—"),
            "service_id": a.service_id, "service_name": svc_name.get(a.service_id, "—"),
            "internet_facing": bool(a.internet_facing),
            "business_value_inr": a.business_value_inr,
            "revenue_impact_per_day_inr": a.revenue_impact_per_day_inr,
            "data_sensitivity": a.data_sensitivity, "operational_criticality": a.operational_criticality,
            "regulatory_importance": a.regulatory_importance, "records_count": a.records_count,
            "owner": a.owner, "dep_count": dependents.get(a.id, 0),
        }

    def vuln_dict(v):
        return {
            "id": v.id, "asset_id": v.asset_id, "cve_id": v.cve_id, "title": v.title,
            "cvss": v.cvss, "severity": v.severity, "exploit_available": bool(v.exploit_available),
            "internet_exposed": bool(v.internet_exposed), "status": v.status, "category": v.category,
            "patch_available": bool(v.patch_available), "age_days": v.age_days,
            "remediation_cost_inr": v.remediation_cost_inr, "source": v.source,
        }

    def control_dict(c):
        return {
            "id": c.id, "key": c.key, "name": c.name, "category": c.category,
            "config_strength": c.config_strength, "coverage": c.coverage,
            "compliance_status": c.compliance_status, "maturity": c.maturity,
            "monitored": bool(c.monitored), "description": c.description,
        }

    return {
        "org": {"id": org.id, "name": org.name, "sector": org.sector, "is_demo": bool(org.is_demo)},
        "business_units": [{"id": b.id, "name": b.name} for b in bus],
        "assets": [asset_dict(a) for a in assets],
        "vulns": [vuln_dict(v) for v in vulns],
        "controls": [control_dict(c) for c in controls],
        "threats": [{"id": t.id, "name": t.name, "category": t.category,
                     "relevance": t.relevance, "likelihood_weight": t.likelihood_weight} for t in threats],
        "incidents": [{"id": i.id, "asset_id": i.asset_id, "title": i.title, "category": i.category,
                       "root_cause": i.root_cause, "financial_impact_inr": i.financial_impact_inr,
                       "records_affected": i.records_affected} for i in incidents],
        "assumptions": assumptions,
    }


def clone_state(state: dict) -> dict:
    return copy.deepcopy(state)
