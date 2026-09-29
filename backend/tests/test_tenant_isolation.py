"""Multi-tenant isolation tests.

Proves that (a) the seeded demo org + demo logins still work, (b) a freshly
registered company starts empty (no demo data), and (c) one tenant can never
read another tenant's rows — including by supplying a foreign id or an
org_id override the client controls.
"""
import uuid


def _register(client, company: str):
    """Register a new company and return (auth_headers, user_dict)."""
    uname = f"admin_{uuid.uuid4().hex[:10]}"
    r = client.post("/api/auth/register", json={
        "company_name": company, "admin_name": "Admin", "username": uname,
        "password": "secret123", "sector": "Testing",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    return {"Authorization": f"Bearer {body['token']}"}, body["user"], uname


# --- Demo org preserved ------------------------------------------------------
def test_demo_login_reports_demo_org(client, analyst_headers):
    me = client.get("/api/auth/me", headers=analyst_headers).json()
    assert me["org_id"] is not None
    assert me["is_demo"] is True
    assert me["organization"]  # e.g. "Meghdoot Financial Services Ltd (DEMO)"


def test_demo_dashboard_still_has_data(client, analyst_headers):
    dash = client.get("/api/dashboard", headers=analyst_headers).json()
    assert dash["enterprise"]["asset_count"] > 0
    assert dash["enterprise"]["total_ale_inr"] > 0


# --- New company onboarding --------------------------------------------------
def test_register_creates_empty_isolated_org(client, analyst_headers):
    headers, user, _ = _register(client, "Acme Corp")
    assert user["is_demo"] is False
    assert user["organization"] == "Acme Corp"
    assert user["role"] == "ciso"

    # Distinct tenant from the demo org.
    demo = client.get("/api/auth/me", headers=analyst_headers).json()
    assert user["org_id"] != demo["org_id"]

    # Brand-new org starts EMPTY — it never inherits Meghdoot's data.
    dash = client.get("/api/dashboard", headers=headers).json()
    assert dash["enterprise"]["asset_count"] == 0
    assert dash["enterprise"]["total_ale_inr"] == 0
    assert client.get("/api/assets", headers=headers).json()["count"] == 0


def test_duplicate_username_rejected(client):
    r1 = client.post("/api/auth/register", json={
        "company_name": "Dup Co", "admin_name": "A", "username": "dupuser",
        "password": "secret123"})
    assert r1.status_code == 201
    r2 = client.post("/api/auth/register", json={
        "company_name": "Dup Co 2", "admin_name": "B", "username": "dupuser",
        "password": "secret123"})
    assert r2.status_code == 409


# --- Cross-tenant isolation --------------------------------------------------
def test_tenant_cannot_read_foreign_asset_by_id(client, analyst_headers):
    """A demo asset id must not be readable by another tenant."""
    assets = client.get("/api/assets", headers=analyst_headers).json()["assets"]
    assert assets, "demo should have assets"
    demo_asset_id = assets[0]["id"]

    headers, _, _ = _register(client, "Beta Ltd")
    # Same id, different tenant → 404 (not another company's data).
    assert client.get(f"/api/assets/{demo_asset_id}", headers=headers).status_code == 404
    # The owner can still read it.
    assert client.get(f"/api/assets/{demo_asset_id}", headers=analyst_headers).status_code == 200


def test_org_id_query_override_is_ignored(client, analyst_headers):
    """Supplying org_id from the client must NOT switch tenants."""
    demo = client.get("/api/auth/me", headers=analyst_headers).json()
    headers, _, _ = _register(client, "Gamma Ltd")
    # Attempt to read the demo org's assets by injecting its org_id — ignored.
    r = client.get(f"/api/assets?org_id={demo['org_id']}", headers=headers).json()
    assert r["count"] == 0


def test_reports_are_tenant_scoped(client, analyst_headers):
    # Demo tenant generates a report.
    gen = client.post("/api/reports/generate", headers=analyst_headers,
                      json={"kind": "executive", "fmt": "json"}).json()
    report_id = gen["id"]

    headers, _, _ = _register(client, "Delta Ltd")
    # Foreign tenant sees an empty report list and cannot fetch the report.
    assert client.get("/api/reports", headers=headers).json()["count"] == 0
    assert client.get(f"/api/reports/{report_id}", headers=headers).status_code == 404
    assert client.get(f"/api/reports/{report_id}/download", headers=headers).status_code == 404
    # Owner can still fetch it.
    assert client.get(f"/api/reports/{report_id}", headers=analyst_headers).status_code == 200


def test_demo_load_restricted_to_demo_org(client):
    headers, _, _ = _register(client, "Epsilon Ltd")
    # A non-demo tenant must not be able to trigger the global demo reset.
    assert client.post("/api/demo/load", headers=headers).status_code == 403


def test_new_tenant_status_is_empty(client):
    headers, _, _ = _register(client, "Zeta Ltd")
    st = client.get("/api/demo/status", headers=headers).json()
    assert st["is_demo"] is False
    assert st["empty"] is True
    assert st["counts"]["assets"] == 0


# --- Add Asset (tenant-scoped creation) --------------------------------------
def test_new_tenant_can_create_isolated_asset(client, analyst_headers):
    """A registered org can add an asset; it shows up for them, updates the
    count, and stays invisible to both other tenants and the demo org."""
    headers, _, _ = _register(client, "Theta Ltd")

    created = client.post("/api/assets", headers=headers, json={
        "name": "Payments API", "asset_type": "app", "internet_facing": True,
        "business_value_inr": 5_000_000, "revenue_impact_per_day_inr": 800_000,
        "data_sensitivity": 5, "operational_criticality": 5, "regulatory_importance": 4,
    })
    assert created.status_code == 201, created.text
    new_id = created.json()["id"]

    # Appears immediately in the owner's list, count updates, risk recomputed.
    listing = client.get("/api/assets", headers=headers).json()
    assert listing["count"] == 1
    assert listing["assets"][0]["name"] == "Payments API"
    assert client.get("/api/dashboard", headers=headers).json()["enterprise"]["asset_count"] == 1

    # A different fresh tenant cannot see or fetch it.
    other, _, _ = _register(client, "Iota Ltd")
    assert client.get("/api/assets", headers=other).json()["count"] == 0
    assert client.get(f"/api/assets/{new_id}", headers=other).status_code == 404

    # The demo org is untouched — still has only its seeded assets.
    demo_assets = client.get("/api/assets", headers=analyst_headers).json()["assets"]
    assert all(a["id"] != new_id for a in demo_assets)


def test_create_asset_requires_name(client):
    headers, _, _ = _register(client, "Kappa Ltd")
    r = client.post("/api/assets", headers=headers, json={"name": "   "})
    assert r.status_code == 422


def test_client_supplied_org_id_ignored_on_create(client, analyst_headers):
    """Injecting another org's id in the create body must not cross tenants."""
    demo = client.get("/api/auth/me", headers=analyst_headers).json()
    headers, mine, _ = _register(client, "Lambda Ltd")
    client.post("/api/assets", headers=headers, json={
        "name": "Sneaky Asset", "org_id": demo["org_id"]})
    # The asset landed in MY org, not the demo org it tried to claim.
    assert client.get("/api/assets", headers=headers).json()["count"] == 1
    demo_names = [a["name"] for a in client.get("/api/assets", headers=analyst_headers).json()["assets"]]
    assert "Sneaky Asset" not in demo_names


# --- Edit / Delete (tenant-scoped CRUD) --------------------------------------
def _create_asset(client, headers, name="Widget", **extra):
    r = client.post("/api/assets", headers=headers, json={"name": name, **extra})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_owner_can_edit_asset_in_place(client):
    headers, _, _ = _register(client, "Mu Ltd")
    aid = _create_asset(client, headers, name="Old Name", business_value_inr=100000)

    r = client.put(f"/api/assets/{aid}", headers=headers, json={
        "name": "New Name", "business_value_inr": 7_500_000, "internet_facing": True})
    assert r.status_code == 200, r.text

    listing = client.get("/api/assets", headers=headers).json()
    assert listing["count"] == 1  # edited in place, NOT duplicated
    row = listing["assets"][0]
    assert row["name"] == "New Name"
    assert row["business_value_inr"] == 7_500_000
    assert row["internet_facing"] is True


def test_owner_can_delete_asset_and_counts_refresh(client):
    headers, _, _ = _register(client, "Nu Ltd")
    aid = _create_asset(client, headers, name="Doomed")
    assert client.get("/api/assets", headers=headers).json()["count"] == 1

    r = client.delete(f"/api/assets/{aid}", headers=headers)
    assert r.status_code == 200, r.text
    assert client.get("/api/assets", headers=headers).json()["count"] == 0
    assert client.get("/api/dashboard", headers=headers).json()["enterprise"]["asset_count"] == 0
    # Gone for good.
    assert client.get(f"/api/assets/{aid}", headers=headers).status_code == 404


def test_cannot_edit_or_delete_another_orgs_asset(client):
    owner, _, _ = _register(client, "Xi Ltd")
    aid = _create_asset(client, owner, name="Owned")

    intruder, _, _ = _register(client, "Omicron Ltd")
    # A foreign asset id is indistinguishable from a missing one → 404.
    assert client.put(f"/api/assets/{aid}", headers=intruder,
                      json={"name": "Hijacked"}).status_code == 404
    assert client.delete(f"/api/assets/{aid}", headers=intruder).status_code == 404
    # The owner's asset is untouched.
    row = client.get(f"/api/assets/{aid}", headers=owner).json()
    assert row["asset"]["name"] == "Owned"


def test_demo_assets_are_read_only(client, analyst_headers):
    """Meghdoot demo data must not be editable/deletable through the API."""
    demo_asset_id = client.get("/api/assets", headers=analyst_headers).json()["assets"][0]["id"]
    assert client.put(f"/api/assets/{demo_asset_id}", headers=analyst_headers,
                      json={"name": "Tampered"}).status_code == 403
    assert client.delete(f"/api/assets/{demo_asset_id}", headers=analyst_headers).status_code == 403


