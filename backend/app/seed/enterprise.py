"""The fictional demo enterprise instance (SYNTHETIC / DEMO data).

'Meghdoot Financial Services Ltd' — a fictional Indian BFSI organisation.
No real company data is used. Money in INR.
"""

ORG = {
    "name": "Meghdoot Financial Services Ltd (DEMO)",
    "sector": "Banking & Financial Services",
    "description": "Fictional Indian NBFC/bank used for demonstration. All data is synthetic.",
}

# ref, name, head
BUSINESS_UNITS = [
    ("digital_banking", "Digital Banking", "Head - Digital Banking"),
    ("payments", "Payments & Settlements", "Head - Payments"),
    ("lending", "Lending & Credit", "Head - Lending"),
    ("wealth", "Wealth Management", "Head - Wealth"),
    ("core_it", "Core IT & Infrastructure", "CIO Office"),
    ("support", "Customer Support & Operations", "Head - Operations"),
]

# ref, name, bu_ref, tier
SERVICES = [
    ("ib", "Internet Banking", "digital_banking", "Tier-0"),
    ("mobile", "Mobile Banking App", "digital_banking", "Tier-0"),
    ("upi", "UPI / Payment Gateway", "payments", "Tier-0"),
    ("cbs", "Core Banking System", "core_it", "Tier-0"),
    ("loan", "Loan Origination", "lending", "Tier-1"),
    ("wealth_pf", "Wealth Portfolio Platform", "wealth", "Tier-1"),
    ("dw", "Data Warehouse & Analytics", "core_it", "Tier-1"),
    ("crm", "Customer CRM", "support", "Tier-2"),
    ("email", "Email & Collaboration", "core_it", "Tier-2"),
]

# ref,name,type,env,bu,svc,net, business_value, rev_per_day, data_sens, op_crit, reg_imp, records, owner
def _a(ref, name, typ, bu, svc, net, bv, rev, ds, oc, ri, rec, owner):
    return {"ref": ref, "name": name, "type": typ, "env": "production", "bu": bu, "svc": svc,
            "net": net, "bv": bv, "rev": rev, "ds": ds, "oc": oc, "ri": ri, "rec": rec, "owner": owner}

ASSETS = [
    _a("cbs_db", "Core Banking Database (Oracle)", "database", "core_it", "cbs", False, 250_000_000, 40_000_000, 5, 5, 5, 4_200_000, "Core Banking Team"),
    _a("cbs_app", "Core Banking Application Servers", "server", "core_it", "cbs", False, 80_000_000, 40_000_000, 4, 5, 5, 0, "Core Banking Team"),
    _a("upi_switch", "UPI Payment Switch", "server", "payments", "upi", True, 120_000_000, 60_000_000, 4, 5, 5, 0, "Payments Engineering"),
    _a("upi_db", "Payments Transaction Database", "database", "payments", "upi", False, 90_000_000, 60_000_000, 5, 5, 5, 2_800_000, "Payments Engineering"),
    _a("ib_web", "Internet Banking Web Portal", "app", "digital_banking", "ib", True, 60_000_000, 25_000_000, 4, 5, 5, 0, "Digital Channels"),
    _a("mobile_api", "Mobile Banking API Gateway", "app", "digital_banking", "mobile", True, 55_000_000, 25_000_000, 4, 5, 4, 0, "Digital Channels"),
    _a("cust_db", "Customer Data Store (PII / KYC)", "database", "digital_banking", "ib", False, 150_000_000, 20_000_000, 5, 4, 5, 3_500_000, "Data Platform"),
    _a("loan_app", "Loan Origination System", "app", "lending", "loan", True, 40_000_000, 8_000_000, 4, 4, 4, 900_000, "Lending Tech"),
    _a("credit_db", "Credit Scoring Database", "database", "lending", "loan", False, 45_000_000, 8_000_000, 5, 4, 4, 1_200_000, "Lending Tech"),
    _a("wealth_app", "Wealth Portfolio Platform", "app", "wealth", "wealth_pf", True, 35_000_000, 6_000_000, 4, 3, 4, 350_000, "Wealth Tech"),
    _a("dw_db", "Data Warehouse (Analytics)", "database", "core_it", "dw", False, 70_000_000, 5_000_000, 5, 3, 4, 5_000_000, "Data Platform"),
    _a("crm_app", "Customer CRM (SaaS)", "saas", "support", "crm", True, 20_000_000, 3_000_000, 4, 3, 3, 1_500_000, "CRM Ops"),
    _a("email_saas", "Email & Collaboration (SaaS)", "saas", "core_it", "email", True, 15_000_000, 4_000_000, 3, 3, 2, 0, "IT Services"),
    _a("ad_dc", "Active Directory Domain Controllers", "server", "core_it", "cbs", False, 60_000_000, 30_000_000, 4, 5, 4, 0, "Identity Team"),
    _a("vpn_gw", "Remote Access VPN Gateway", "network", "core_it", "cbs", True, 25_000_000, 20_000_000, 3, 4, 3, 0, "Network Security"),
    _a("web_dmz", "Public Website / DMZ Server", "server", "digital_banking", "ib", True, 12_000_000, 3_000_000, 2, 2, 2, 0, "Digital Channels"),
    _a("jump_host", "Admin Jump Host / Bastion", "server", "core_it", "cbs", False, 18_000_000, 15_000_000, 4, 5, 3, 0, "Identity Team"),
    _a("backup_srv", "Backup & Recovery Server", "server", "core_it", "cbs", False, 30_000_000, 10_000_000, 4, 4, 3, 0, "Infrastructure"),
    _a("atm_switch", "ATM Switch", "server", "payments", "upi", False, 40_000_000, 15_000_000, 4, 4, 4, 0, "Payments Engineering"),
    _a("dev_ci", "DevOps CI/CD & Source Repository", "server", "core_it", "dw", True, 22_000_000, 5_000_000, 3, 3, 3, 0, "Platform Engineering"),
    _a("endpoint_fleet", "Employee Endpoint Fleet", "endpoint", "support", "crm", False, 25_000_000, 8_000_000, 3, 3, 2, 0, "IT Services"),
    _a("hr_payroll", "HR & Payroll System", "app", "support", "crm", False, 15_000_000, 2_000_000, 4, 2, 3, 45_000, "HR Systems"),
]

# (asset_ref, depends_on_ref, type)
DEPENDENCIES = [
    ("cbs_app", "cbs_db", "uses"), ("ib_web", "cbs_app", "uses"), ("ib_web", "cust_db", "data-flow"),
    ("ib_web", "ad_dc", "authenticates"), ("mobile_api", "cbs_app", "uses"), ("mobile_api", "cust_db", "data-flow"),
    ("mobile_api", "ad_dc", "authenticates"), ("upi_switch", "upi_db", "uses"), ("upi_switch", "cbs_app", "uses"),
    ("loan_app", "credit_db", "uses"), ("loan_app", "cbs_app", "uses"), ("loan_app", "ad_dc", "authenticates"),
    ("wealth_app", "dw_db", "uses"), ("wealth_app", "ad_dc", "authenticates"), ("crm_app", "cust_db", "data-flow"),
    ("dw_db", "cbs_db", "data-flow"), ("dw_db", "cust_db", "data-flow"), ("atm_switch", "cbs_app", "uses"),
    ("jump_host", "ad_dc", "authenticates"), ("backup_srv", "cbs_db", "data-flow"), ("vpn_gw", "ad_dc", "authenticates"),
    ("endpoint_fleet", "ad_dc", "authenticates"), ("hr_payroll", "ad_dc", "authenticates"),
]
