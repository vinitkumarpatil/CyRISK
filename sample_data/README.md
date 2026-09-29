# Sample import data

These files match the import templates exposed at
`GET /api/imports/template/{vulnerabilities|assets}` and can be uploaded through
the **Data Sources** page (or `POST /api/imports/{kind}`) while signed in as
`ciso` or `analyst`.

| File | Kind | Format |
|------|------|--------|
| `vulnerabilities_import.csv` | vulnerabilities | CSV |
| `vulnerabilities_import.json` | vulnerabilities | JSON (`{"rows": [...]}`) |
| `assets_import.csv` | assets | CSV |
| `assets_import.json` | assets | JSON (`{"rows": [...]}`) |

Notes:
- **Vulnerability rows reference `asset_id`** — the ID must belong to an asset in
  the current organization, otherwise the row is safely skipped and reported.
  Import assets first if you need new IDs, or point at the seeded demo assets.
- All values are validated, coerced and bounded on import; enums fall back to
  safe defaults; imported rows are flagged `is_demo = false`.
- Every figure remains a **modelled estimate on synthetic data** — nothing here
  is real-world data.
