import re
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from ..utils.auth import get_user_from_request
from ..utils.parsers import parse_requirements_txt, parse_pyproject_toml
from ..services.pypi_enrich import enrich_from_pypi

bp_scanner = Blueprint("scanner", __name__)

@bp_scanner.route("/scan", methods=["POST"])
def scan():
    user_id, error_response = get_user_from_request()
    if error_response:
        return error_response

    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename or "")
    content = f.read()

    if not filename:
        return jsonify({"error": "filename is required"}), 400

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

    # Deduplicate by case-insensitive package name; keep first occurrence/spec
    unique = {}
    for it in items:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key not in unique:
            unique[key] = {"name": name, "spec": it.get("spec", "")}

    results = []
    for it in unique.values():
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
