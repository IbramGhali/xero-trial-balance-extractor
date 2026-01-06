import json
import os
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("XERO_REDIRECT_URI", "http://localhost:8000/callback")
SCOPES = os.getenv("XERO_SCOPES", "accounting.reports.read offline_access")

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"
TRIAL_BALANCE_URL = "https://api.xero.com/api.xro/2.0/Reports/TrialBalance"

TOKEN_FILE = "token_store.json"
TENANT_FILE = "tenant.json"

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def have_token() -> bool:
    return os.path.exists(TOKEN_FILE)

def have_tenant() -> bool:
    return os.path.exists(TENANT_FILE)

def build_auth_url() -> str:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    query = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    return f"{AUTH_URL}?{query}"

def exchange_code_for_token(code: str) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(
        TOKEN_URL,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def refresh_token(token_set: dict) -> dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": token_set["refresh_token"],
    }
    r = requests.post(
        TOKEN_URL,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def get_tenant_id(access_token: str) -> str:
    r = requests.get(
        CONNECTIONS_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    r.raise_for_status()
    connections = r.json()
    if not connections:
        raise RuntimeError("No Xero connections found. Ensure you authorised the correct organisation.")
    tenant_id = connections[0]["tenantId"]  # single-org assumption
    save_json(TENANT_FILE, {"tenantId": tenant_id})
    return tenant_id

def call_trial_balance(access_token: str, tenant_id: str, as_of: date, payments_only: bool) -> dict:
    params = {
        "date": as_of.isoformat(),
        "paymentsOnly": "true" if payments_only else "false",
    }
    r = requests.get(
        TRIAL_BALANCE_URL,
        params=params,
        headers={
            "Authorization": f"Bearer {access_token}",
            "xero-tenant-id": tenant_id,
            "Accept": "application/json",
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

class CallbackHandler(BaseHTTPRequestHandler):
    code_received = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        qs = parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code")
            return

        CallbackHandler.code_received = code
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Auth code received. You can close this tab and return to the terminal.")

def run_callback_server():
    httpd = HTTPServer(("localhost", 8000), CallbackHandler)
    httpd.handle_request()

def authenticate_once():
    t = threading.Thread(target=run_callback_server, daemon=True)
    t.start()

    url = build_auth_url()
    print("\nIf browser doesn’t open, copy/paste this URL:\n", url, "\n")
    webbrowser.open(url)

    while CallbackHandler.code_received is None:
        pass

    token_set = exchange_code_for_token(CallbackHandler.code_received)
    save_json(TOKEN_FILE, token_set)
    tenant_id = get_tenant_id(token_set["access_token"])
    print("✅ Auth complete. Saved token_store.json and tenant.json")
    print("Tenant ID:", tenant_id)

def ensure_fresh_token() -> dict:
    token_set = load_json(TOKEN_FILE)
    new_token = refresh_token(token_set)
    save_json(TOKEN_FILE, new_token)
    return new_token

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError("Missing XERO_CLIENT_ID or XERO_CLIENT_SECRET in .env")

    if not have_token():
        print("No token found. Starting first-time authentication...")
        authenticate_once()

    token_set = ensure_fresh_token()
    access_token = token_set["access_token"]

    if have_tenant():
        tenant_id = load_json(TENANT_FILE)["tenantId"]
    else:
        tenant_id = get_tenant_id(access_token)

    # CHANGE THIS DATE:
    as_of = date(2025, 12, 31)

    # payments_only=False => accrual basis (recommended for GL)
    payments_only = False

    report = call_trial_balance(access_token, tenant_id, as_of, payments_only)

    out_file = f"trial_balance_{as_of.isoformat()}.json"
    save_json(out_file, report)
    print(f"✅ Saved {out_file}")

if __name__ == "__main__":
    main()
