
# Xero Trial Balance (GL Account Balances) Extractor – Runbook

## Purpose
This runbook explains how to extract **General Ledger (GL) account balances** from :contentReference[oaicite:0]{index=0} using the **Trial Balance API**.

The Trial Balance provides a snapshot of all GL account balances **as of a specific date** and is the correct source for:
- Month-end balances
- Year-end balances
- Financial reporting
- Integration with other software

---

## What this process does
1. Authenticates to Xero using **OAuth 2.0**
2. Retrieves the **Xero tenant (organisation) ID**
3. Calls the **Trial Balance report API**
4. Saves the result as a JSON file

---

## Output files
- `trial_balance_YYYY-MM-DD.json` → Trial Balance report
- `token_store.json` → OAuth tokens (**do not commit**)
- `tenant.json` → Xero organisation ID (**do not commit**)

---

## Prerequisites
- Windows 10/11
- Python 3.10+
- Access to the target Xero organisation
- A Xero Developer App

---

## Step 1 — Create a Xero Developer App (one-time)
1. Go to the Xero Developer Portal
2. Create a new app
3. Set Redirect URI **exactly** to:
http://localhost:8000/callback

yaml
Copy code
4. Enable scopes:
- `accounting.reports.read`
- `offline_access`
5. Copy:
- Client ID
- Client Secret

---

## Step 2 — Clone the repository
```powershell
git clone https://github.com/<YOUR_GITHUB_USERNAME>/xero-trial-balance-extractor.git
cd xero-trial-balance-extractor
```
## Step 3 — Create and activate a virtual environment
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
## Step 4 — Install dependencies
```powershell

pip install -r requirements.txt
```
## Step 5 — Configure environment variables
```powershell

copy .env.example .env
notepad .env
```
Fill in:

env
```
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
XERO_REDIRECT_URI=http://localhost:8000/callback
XERO_SCOPES=accounting.reports.read offline_access
```
⚠️ Never commit .env, token files, or output files.

## Step 6 — Run the extractor
```powershell
Copy code
python .\xero_trial_balance.py
```
### First run
- Browser opens to Xero login
- Approve access
- Script creates:
  - `token_store.json`
  - `tenant.json`

### Next runs
- Tokens refresh automatically
- No login required

## Step 7 — Change the extraction date
Edit this line in xero_trial_balance.py:

```python

as_of = date(2025, 12, 31)
```
Accounting basis
```python

payments_only = False
```
False → Accrual basis (recommended)

True → Cash basis

## Troubleshooting
Redirect URI error
Ensure Redirect URI matches exactly:

```bash
http://localhost:8000/callback
```
401 / Unauthorized
Delete:

token_store.json

tenant.json

Then run the script again.

API endpoint used
```sql
GET /Reports/TrialBalance
```
## Official Xero resources

Xero Trial Balance API
https://developer.xero.com/documentation/api/accounting/reports#get-reports-trialbalance

Xero OAuth 2.0 Guide
https://developer.xero.com/documentation/guides/oauth2/overview

Xero Python SDK
https://github.com/XeroAPI/xero-python
https://pypi.org/project/xero-python/

Why Trial Balance?
One API call

Xero-calculated balances

Accurate for audits and reporting

No manual aggregation needed

## Owner
Runbook owner: Ibram Ghali








