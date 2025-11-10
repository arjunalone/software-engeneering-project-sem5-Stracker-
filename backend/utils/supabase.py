import os
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXP_SECONDS = int(os.environ.get("JWT_EXP_SECONDS", "86400"))
ADMIN_SIGNUP_SECRET = os.environ.get("ADMIN_SIGNUP_SECRET", "")

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL in backend/.env")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY in backend/.env")
if not JWT_SECRET:
    raise RuntimeError("Missing JWT_SECRET in backend/.env (run 'openssl rand -base64 32' to create one)")

REST_BASE = f"{SUPABASE_URL}/rest/v1"

# If no separate admin secret is provided, fall back to JWT_SECRET per user preference
if not ADMIN_SIGNUP_SECRET:
    ADMIN_SIGNUP_SECRET = JWT_SECRET

USERS_TABLE = os.environ.get("USERS_TABLE", "user_details")
RELEASES_TABLE = os.environ.get("RELEASES_TABLE", "releases")
USER_PASSWORD_COL = os.environ.get("USER_PASSWORD_COL", "password_hash")

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

def now_iso() -> str:
    return datetime.utcnow().isoformat()
