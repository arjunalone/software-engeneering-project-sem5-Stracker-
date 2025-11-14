import json
import logging
import bcrypt
import requests
from flask import Blueprint, request, jsonify

from ..utils.supabase import REST_BASE, USERS_TABLE, USER_PASSWORD_COL, HEADERS, ADMIN_SIGNUP_SECRET
from ..utils.auth import create_jwt, get_user_from_request, require_roles

bp_auth = Blueprint("auth", __name__)

@bp_auth.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    requested_role = (data.get("role") or "user").strip()
    admin_secret = (data.get("admin_secret") or "").strip()

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

    if requested_role == "admin":
        return jsonify({"error": "admin signup is disabled"}), 403
    role_value = "user"

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    payload = {"name": name, "email": email, USER_PASSWORD_COL: pw_hash, "role": role_value}

    insert_url = f"{REST_BASE}/{USERS_TABLE}"
    r2 = requests.post(insert_url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps(payload), timeout=8)
    if r2.status_code not in (200, 201):
        logging.error("Supabase user insert failed: %s %s", r2.status_code, r2.text)
        return jsonify({"error": "failed to create user"}), 502

    user_row = r2.json()[0]
    user_id = user_row.get("id")
    role = user_row.get("role")
    token = create_jwt({"user_id": user_id, "email": email, "role": role})
    return jsonify({"user": {"id": user_id, "name": user_row.get("name"), "email": user_row.get("email"), "role": role}, "token": token}), 201

@bp_auth.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    requested_role = (data.get("as_role") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    q = f"{REST_BASE}/{USERS_TABLE}?email=eq.{requests.utils.requote_uri(email)}&select=id,name,email,role,{USER_PASSWORD_COL}"
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
    except Exception:
        return jsonify({"error": "invalid email or password"}), 401

    if not matches:
        return jsonify({"error": "invalid email or password"}), 401

    # If client asks to login as a specific role, enforce it
    actual_role = user.get("role")
    if requested_role and requested_role != actual_role:
        return jsonify({"error": "role mismatch", "actual_role": actual_role}), 403

    token = create_jwt({"user_id": user.get("id"), "email": user.get("email"), "role": actual_role})
    return jsonify({"user": {"id": user.get("id"), "name": user.get("name"), "email": user.get("email"), "role": actual_role}, "token": token}), 200

@bp_auth.route("/me", methods=["GET"])
def me():
    user_id, error_response = get_user_from_request()
    if error_response:
        return error_response

    q = f"{REST_BASE}/{USERS_TABLE}?id=eq.{user_id}&select=id,name,email,role,created_at"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200 or not r.json():
        logging.error("Supabase /me fetch failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch user"}), 502

    user = r.json()[0]
    return jsonify({"user": user}), 200


# Admin endpoints
@bp_auth.route("/admin/users", methods=["GET"])
def admin_list_users():
    _, _, error_response = require_roles(["admin"])
    if error_response:
        return error_response

    q = f"{REST_BASE}/{USERS_TABLE}?select=id,name,email,role,created_at&order=created_at.desc"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200:
        logging.error("Supabase list users failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch users"}), 502
    return jsonify({"users": r.json()}), 200


@bp_auth.route("/admin/users/<user_id>", methods=["DELETE"])
def admin_delete_user(user_id: str):
    _, _, error_response = require_roles(["admin"])
    if error_response:
        return error_response

    url = f"{REST_BASE}/{USERS_TABLE}?id=eq.{requests.utils.requote_uri(user_id)}"
    r = requests.delete(url, headers=HEADERS, timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase delete user failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to delete user"}), 502
    return jsonify({"deleted": True, "id": user_id}), 200


@bp_auth.route("/admin/users/<user_id>/role", methods=["PATCH"])
def admin_set_user_role(user_id: str):
    _, _, error_response = require_roles(["admin"])
    if error_response:
        return error_response

    data = request.get_json() or {}
    new_role = (data.get("role") or "").strip()
    if new_role not in ("admin", "user"):
        return jsonify({"error": "invalid role"}), 400
    if new_role == "admin":
        return jsonify({"error": "promoting to admin is disabled"}), 403

    url = f"{REST_BASE}/{USERS_TABLE}?id=eq.{requests.utils.requote_uri(user_id)}"
    payload = json.dumps({"role": new_role})
    r = requests.patch(url, headers={**HEADERS, "Prefer": "return=representation"}, data=payload, timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase update user role failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to update role"}), 502

    rows = r.json() if r.text else []
    updated = rows[0] if rows else {"id": user_id, "role": new_role}
    return jsonify({"user": updated}), 200
