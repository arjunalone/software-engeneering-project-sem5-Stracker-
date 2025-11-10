import json
import logging
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

from ..utils.supabase import REST_BASE, RELEASES_TABLE, HEADERS
from ..utils.auth import get_user_from_request, get_identity_from_request, require_roles
from ..utils.supabase import now_iso

bp_releases = Blueprint("releases", __name__)

@bp_releases.route("/releases", methods=["GET"])
def get_releases():
    user_id, role, error_response = get_identity_from_request()
    if error_response:
        return error_response

    if role == "admin":
        q = f"{REST_BASE}/{RELEASES_TABLE}?select=*&order=created_at.desc"
    else:
        q = f"{REST_BASE}/{RELEASES_TABLE}?user_id=eq.{user_id}&select=*&order=created_at.desc"
    r = requests.get(q, headers=HEADERS, timeout=8)
    if r.status_code != 200:
        logging.error("Supabase releases fetch failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to fetch releases"}), 502

    return jsonify(r.json()), 200

@bp_releases.route("/releases", methods=["POST"])
def create_release():
    admin_id, _, error_response = require_roles(["admin"])
    if error_response:
        return error_response

    data = request.get_json() or {}
    project_name = (data.get("project_name") or "").strip()
    version = (data.get("version") or "").strip()
    status = (data.get("status") or "Planned").strip()

    if not project_name or not version:
        return jsonify({"error": "project_name and version are required"}), 400

    target_user_id = (data.get("user_id") or admin_id)
    payload = {
        "user_id": target_user_id,
        "project_name": project_name,
        "version": version,
        "status": status,
        "created_at": now_iso(),
    }
    insert_url = f"{REST_BASE}/{RELEASES_TABLE}"
    r = requests.post(insert_url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps(payload), timeout=8)
    if r.status_code not in (200, 201):
        logging.error("Supabase release insert failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to create release"}), 502

    return jsonify(r.json()[0]), 201

@bp_releases.route("/releases/<int:release_id>", methods=["PATCH"])
def update_release_status(release_id):
    user_id, role, error_response = get_identity_from_request()
    if error_response:
        return error_response

    data = request.get_json() or {}
    new_status = (data.get("status") or "").strip()
    if not new_status:
        return jsonify({"error": "status is required"}), 400

    if role == "admin":
        url = f"{REST_BASE}/{RELEASES_TABLE}?id=eq.{release_id}"
    else:
        url = f"{REST_BASE}/{RELEASES_TABLE}?id=eq.{release_id}&user_id=eq.{user_id}"
    r = requests.patch(url, headers={**HEADERS, "Prefer": "return=representation"}, data=json.dumps({"status": new_status}), timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase release update failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to update release"}), 502

    try:
        updated = r.json()[0]
        return jsonify(updated), 200
    except Exception:
        return jsonify({"success": True}), 200

@bp_releases.route("/releases/<int:release_id>", methods=["DELETE"])
def delete_release(release_id):
    user_id, role, error_response = get_identity_from_request()
    if error_response:
        return error_response

    url = f"{REST_BASE}/{RELEASES_TABLE}?id=eq.{release_id}&user_id=eq.{user_id}"
    r = requests.delete(url, headers=HEADERS, timeout=8)
    if r.status_code not in (200, 204):
        logging.error("Supabase release delete failed: %s %s", r.status_code, r.text)
        return jsonify({"error": "failed to delete release"}), 502

    return ("", 204)

@bp_releases.route("/releases/import-scan", methods=["POST"])
def import_scan():
    user_id, role, error_response = get_identity_from_request()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows") or []
    default_status = (payload.get("status") or "Planned").strip() or "Planned"
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "rows[] required"}), 400

    created_or_existing = []
    for rrow in rows:
        project_name = (rrow.get("name") or "").strip()
        version = (rrow.get("latest_version") or "").strip() or "unknown"
        if not project_name:
            continue
        if role == "admin":
            check_q = (
                f"{REST_BASE}/{RELEASES_TABLE}?project_name=eq.{requests.utils.requote_uri(project_name)}"
                f"&version=eq.{requests.utils.requote_uri(version)}&select=*"
            )
        else:
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
            "created_at": now_iso(),
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
