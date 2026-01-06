# Xero Trial Balance (GL Account Balances) Extractor — Runbook

## Purpose
Extract GL account balances from Xero by calling the Trial Balance report API and saving the output as JSON.

---

## What you get
- `trial_balance_YYYY-MM-DD.json` (Trial Balance report)
- `token_store.json` and `tenant.json` (created after first login) — DO NOT COMMIT

---

## Xero Developer Portal setup (one-time)
1. Create a new Xero App
2. Redirect URI (exact): `http://localhost:8000/callback`
3. Scopes:
   - `accounting.reports.read`
   - `offline_access`
4. Copy your Client ID and Client Secret

---

## Local setup (Windows)
```powershell
git clone https://github.com/<YOUR_USERNAME>/xero-trial-balance-extractor.git
cd xero-trial-balance-extractor
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
