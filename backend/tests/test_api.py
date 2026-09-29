"""API integration tests over the seeded demo enterprise (isolated temp DB).

Verifies auth gating, that every read endpoint returns computed data, and that
the interactive engines (optimizer, scenarios, assistant, telemetry, reports)
genuinely react to their inputs rather than returning canned responses.
"""


def test_health_is_public(client):
    assert client.get("/api/health").json()["status"] == "healthy"


def test_login_and_bad_login(client):
    assert client.post("/api/auth/login",
                       json={"username": "analyst", "password": "analyst123"}).status_code == 200
    assert client.post("/api/auth/login",
                       json={"username": "analyst", "password": "nope"}).status_code == 401


def test_protected_endpoint_requires_token(client):
    assert client.get("/api/dashboard").status_code == 401


def test_read_endpoints_ok(client, analyst_headers):
    for path in ["/api/dashboard", "/api/risk", "/api/risk/enterprise", "/api/assets",
                 "/api/vulnerabilities", "/api/controls", "/api/telemetry",
                 "/api/frameworks", "/api/recommendations", "/api/investments",
                 "/api/model", "/api/assumptions", "/api/risk/trend",
                 "/api/assistant/suggestions"]:
        assert client.get(path, headers=analyst_headers).status_code == 200, path


def test_dashboard_has_monetary_risk(client, analyst_headers):
    dash = client.get("/api/dashboard", headers=analyst_headers).json()
    assert dash["enterprise"]["total_ale_inr"] > 0
    assert "₹" in dash["headline_inr"]["total_ale"]
    assert len(dash["top_contributors"]) >= 1


def test_optimizer_is_deterministic_and_budget_sensitive(client, analyst_headers):
    big1 = client.post("/api/optimizer/run", json={"budget_inr": 20_000_000},
                       headers=analyst_headers).json()
    big2 = client.post("/api/optimizer/run", json={"budget_inr": 20_000_000},
                       headers=analyst_headers).json()
    small = client.post("/api/optimizer/run", json={"budget_inr": 3_000_000},
                        headers=analyst_headers).json()
    # deterministic
    assert big1["total_cost_inr"] == big2["total_cost_inr"]
    assert big1["joint_ale_reduction_inr"] == big2["joint_ale_reduction_inr"]
    # within budget + reacts to the constraint
    assert big1["total_cost_inr"] <= 20_000_000
    assert small["total_cost_inr"] <= 3_000_000
    assert small["total_cost_inr"] != big1["total_cost_inr"]
    assert isinstance(big1["curve"], list) and len(big1["curve"]) >= 1


def test_scenario_recomputes_before_after(client, analyst_headers):
    sc = client.post("/api/scenarios/simulate", headers=analyst_headers, json={
        "name": "Patch critical", "mutations": [
            {"op": "patch_vulns", "filter": {"severity": "Critical"},
             "set": {"status": "closed"}}]}).json()
    assert {"before", "after", "delta"} <= set(sc)
    assert sc["delta"]["ale_reduction_inr"] >= 0


def test_assistant_is_deterministic_and_sourced(client, analyst_headers):
    a = client.post("/api/assistant/query", headers=analyst_headers,
                    json={"question": "What is our expected annual loss?"}).json()
    assert a["numbers_source"].startswith("computed")
    b = client.post("/api/assistant/query", headers=analyst_headers,
                    json={"question": "How should I spend a budget of 2 crore?"}).json()
    assert b["action_required"] == "run_optimizer"
    assert b["budget_inr"] == 20_000_000


def test_telemetry_simulation_writes_snapshot(client, analyst_headers):
    before = len(client.get("/api/risk/snapshots", headers=analyst_headers)
                 .json()["snapshots"])
    tl = client.post("/api/demo/simulate-telemetry", headers=analyst_headers).json()
    after = len(client.get("/api/risk/snapshots", headers=analyst_headers)
                .json()["snapshots"])
    assert len(tl["events"]) >= 1
    assert after == before + 1


def test_report_json_and_pdf(client, analyst_headers):
    rj = client.post("/api/reports/generate", headers=analyst_headers,
                     json={"kind": "executive", "fmt": "json",
                           "budget_inr": 15_000_000}).json()
    assert rj["status"] == "generated" and rj["payload"]["optimization"] is not None
    rp = client.post("/api/reports/generate", headers=analyst_headers,
                     json={"kind": "technical", "fmt": "pdf"})
    assert rp.status_code == 200
    dl = client.get(rp.json()["download_url"], headers=analyst_headers)
    assert dl.status_code == 200 and dl.content[:4] == b"%PDF"


def test_import_template_available(client, analyst_headers):
    r = client.get("/api/imports/template/vulnerabilities", headers=analyst_headers)
    assert r.status_code == 200 and "required" in r.json()


def test_role_gating_on_scenarios(client, exec_headers, analyst_headers):
    # exec (read-only executive) may not run what-if mutations
    assert client.post("/api/scenarios/simulate", headers=exec_headers,
                       json={"mutations": [{"op": "patch_vulns"}]}).status_code == 403
    # analyst may
    assert client.post("/api/scenarios/simulate", headers=analyst_headers, json={
        "mutations": [{"op": "patch_vulns", "filter": {"severity": "Low"},
                       "set": {"status": "closed"}}]}).status_code == 200
