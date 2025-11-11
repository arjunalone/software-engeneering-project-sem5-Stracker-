import os
import json
import logging
from datetime import datetime, timedelta
import re

import requests
import bcrypt
import jwt
from werkzeug.utils import secure_filename
from utils.parsers import parse_requirements_txt, parse_pyproject_toml
from services.pypi_enrich import enrich_from_pypi

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXP_SECONDS = int(os.environ.get("JWT_EXP_SECONDS", "86400"))

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL in backend/.env")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY in backend/.env")
if not JWT_SECRET:
    raise RuntimeError("Missing JWT_SECRET in backend/.env (run 'openssl rand -base64 32' to create one)")

REST_BASE = f"{SUPABASE_URL}/rest/v1"

# Allow overriding table names via env; default to the observed schema
USERS_TABLE = os.environ.get("USERS_TABLE", "user_details")
RELEASES_TABLE = os.environ.get("RELEASES_TABLE", "releases")
# Column name for stored password hash (some schemas use password_hash)
USER_PASSWORD_COL = os.environ.get("USER_PASSWORD_COL", "password_hash")

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

app = Flask(__name__)
# CORS is now configured in __init__.py
logging.basicConfig(level=logging.INFO)


def create_jwt(payload: dict):
    exp = datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    payload_copy = payload.copy()
    payload_copy["exp"] = exp
    payload_copy["iat"] = datetime.utcnow()
    token = jwt.encode(payload_copy, JWT_SECRET, algorithm="HS256")
    # PyJWT >= 2 returns str, older returns bytes
    return token if isinstance(token, str) else token.decode("utf-8")


def verify_jwt(token: str):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return data
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    q = f"{REST_BASE}/{USERS_TABLE}?email=eq.{requests.utils.requote_uri(email)}&select=id"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200:
        logging.error("Supabase users lookup failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to check existing users"}), 502
    if r.json():
        return jsonify({"error": "email already registered"}), 400

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    payload = {
        "name": name,
        "email": email,
        USER_PASSWORD_COL: pw_hash,
    }
    insert_url = f"{REST_BASE}/{USERS_TABLE}"
    r2 = requests.post(insert_url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps(payload), timeout=8)
    if r2.status_code not in (200, 201):
        logging.error("Supabase user insert failed: %s %s", r2.status_code, r2.text)
        return jsonify({"error": "failed to create user"}), 502

    user_row = r2.json()[0]
    user_id = user_row.get("id")
    token = create_jwt({"user_id": user_id, "email": email})
    return jsonify({"user": {"id": user_id, "name": user_row.get("name"), "email": user_row.get("email")}, "token": token}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    q = f"{REST_BASE}/{USERS_TABLE}?email=eq.{requests.utils.requote_uri(email)}&select=id,name,email,{USER_PASSWORD_COL}"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200:
        logging.error("Supabase users fetch failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch user"}), 502

    rows = r.json()
    if not rows:
        return jsonify({"error": "invalid email or password"}), 401

    user = rows[0]
    stored_hash = user.get(USER_PASSWORD_COL)
    if not stored_hash:
        return jsonify({"error": "invalid email or password"}), 401

    try:
        matches = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError) as e:
        # Stored value isn't a valid bcrypt hash — log for inspection and return auth failure
        logging.warning("Invalid password hash format for user %s: %s", user.get("email"), str(e))
        return jsonify({"error": "invalid email or password"}), 401

    if not matches:
        return jsonify({"error": "invalid email or password"}), 401

    token = create_jwt({"user_id": user.get("id"), "email": user.get("email")})
    return jsonify({"user": {"id": user.get("id"), "name": user.get("name"), "email": user.get("email")}, "token": token}), 200


def get_user_from_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, (jsonify({"error": "missing token"}), 401)
    token = auth.split(" ", 1)[1]
    data = verify_jwt(token)
    if not data or not data.get("user_id"):
        return None, (jsonify({"error": "invalid or expired token"}), 401)
    return data.get("user_id"), None


@app.route("/me", methods=["GET"])
def me():
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    q = f"{REST_BASE}/{USERS_TABLE}?id=eq.{user_id}&select=id,name,email,created_at"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200 or not r.json():
        logging.error("Supabase /me fetch failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch user"}), 502

    user = r.json()[0]
    return jsonify({"user": user}), 200


@app.route("/releases", methods=["GET"])
def get_releases():
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    q = f"{REST_BASE}/{RELEASES_TABLE}?user_id=eq.{user_id}&select=*&order=created_at.desc"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200:
        logging.error("Supabase releases fetch failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch releases"}), 502

    return jsonify(r.json()), 200


@app.route("/releases", methods=["POST"])
def create_release():
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    data = request.get_json() or {}
    project_name = data.get("project_name", "").strip()
    version = data.get("version", "").strip()
    status = data.get("status", "Planned").strip()

    if not project_name or not version:
        return jsonify({"error": "project_name and version are required"}), 400

    payload = {
        "user_id": user_id,
        "project_name": project_name,
        "version": version,
        "status": status,
        "created_at": datetime.utcnow().isoformat()
    }
    insert_url = f"{REST_BASE}/{RELEASES_TABLE}"
    r = requests.post(insert_url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps(payload), timeout=8)
    if r.status_code not in (200, 201):
        logging.error("Supabase release insert failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to create release"}), 502

    return jsonify(r.json()[0]), 201


@app.route("/releases/<int:release_id>", methods=["PATCH"])
def update_release_status(release_id):
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    data = request.get_json() or {}
    new_status = data.get("status", "").strip()
    if not new_status:
        return jsonify({"error": "status is required"}), 400

    url = f"{REST_BASE}/{RELEASES_TABLE}?id=eq.{release_id}&user_id=eq.{user_id}"
    r = requests.patch(url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps({"status": new_status}), timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase release update failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to update release"}), 502

    # return updated row if present
    try:
        updated = r.json()[0]
        return jsonify(updated), 200
    except Exception:
        return jsonify({"success": True}), 200


@app.route("/releases/<int:release_id>", methods=["DELETE"])
def delete_release(release_id):
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    url = f"{REST_BASE}/{RELEASES_TABLE}?id=eq.{release_id}&user_id=eq.{user_id}"
    r = requests.delete(url, headers=HEADERS, timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase release delete failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to delete release"}), 502

    return ("", 204)


# -------------------- Scanner Endpoints --------------------

@app.route("/", methods=["GET"])
def root_index():
    return jsonify({"ok": True, "service": "release-tracker-api"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/scan", methods=["POST"])
def scan_dependencies():
    # Auth optional? Keep consistent with app: require auth
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    f = request.files["file"]
    filename = secure_filename(f.filename or "")
    content = f.read()

    if not filename:
        return jsonify({"error": "filename is required"}), 400

    items = []
    if filename.endswith(".txt"):
        try:
            items = parse_requirements_txt(content.decode("utf-8", errors="ignore"))
        except Exception:
            return jsonify({"error": "failed to parse requirements.txt"}), 400
    elif filename.endswith(".toml"):
        try:
            items = parse_pyproject_toml(content)
        except Exception:
            return jsonify({"error": "failed to parse pyproject.toml (install tomli for Python 3.10)"}), 400
    else:
        return jsonify({"error": "Only requirements.txt or pyproject.toml are supported"}), 400

    results = []
    for it in items:
        name = it.get("name")
        if not name:
            continue
        meta = enrich_from_pypi(name)
        results.append({
            "name": name,
            "spec": it.get("spec", ""),
            "latest_version": meta.get("latest_version"),
            "release_date": meta.get("release_date"),
            "homepage": meta.get("homepage"),
            "repo_url": meta.get("repo_url"),
            "pypi_url": meta.get("pypi_url"),
        })

    return jsonify(results), 200


@app.route("/releases/import-scan", methods=["POST"])
def import_scan_results():
    user_id, error_response = get_user_from_token()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows") or []
    default_status = (payload.get("status") or "Planned").strip() or "Planned"
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "rows[] required"}), 400

    created_or_existing = []
    for r in rows:
        project_name = (r.get("name") or "").strip()
        version = (r.get("latest_version") or "").strip() or "unknown"
        if not project_name:
            continue

        # Check if release already exists for this user/project/version
        check_q = (
            f"{REST_BASE}/{RELEASES_TABLE}?user_id=eq.{user_id}"
            f"&project_name=eq.{requests.utils.requote_uri(project_name)}"
            f"&version=eq.{requests.utils.requote_uri(version)}&select=*"
        )
        cr = requests.get(check_q, headers=HEADERS, timeout=8)
        if cr.status_code != 200:
            logging.warning("Supabase check existing failed: %s %s", cr.status_code, cr.text)
            return jsonify({"error": "failed to check existing releases"}), 502

        if cr.json():
            created_or_existing.append(cr.json()[0])
            continue

        payload_row = {
            "user_id": user_id,
            "project_name": project_name,
            "version": version,
            "status": default_status,
            "created_at": datetime.utcnow().isoformat(),
        }
        ins = requests.post(
            f"{REST_BASE}/{RELEASES_TABLE}",
            headers={**HEADERS, "Prefer": "return=representation"},
            data=json.dumps(payload_row),
            timeout=8,
        )
        if ins.status_code not in (200, 201):
            logging.warning("Supabase insert release failed: %s %s", ins.status_code, ins.text)
            return jsonify({"error": "failed to insert release"}), 502
        created_or_existing.append(ins.json()[0])

    return jsonify(created_or_existing), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)