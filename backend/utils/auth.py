import jwt
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from flask import request, jsonify

from .supabase import JWT_SECRET, JWT_EXP_SECONDS


def create_jwt(payload: dict) -> str:
    exp = datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    p = {**payload, "exp": exp, "iat": datetime.utcnow()}
    token = jwt.encode(p, JWT_SECRET, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")


def verify_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except Exception as e:
        logging.debug("JWT verify failed: %s", str(e))
        return None


def get_user_from_request():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, (jsonify({"error": "missing token"}), 401)
    token = auth.split(" ", 1)[1]
    data = verify_jwt(token)
    if not data or not data.get("user_id"):
        return None, (jsonify({"error": "invalid or expired token"}), 401)
    return data.get("user_id"), None


def get_identity_from_request() -> Tuple[Optional[str], Optional[str], Optional[Tuple]]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, None, (jsonify({"error": "missing token"}), 401)
    token = auth.split(" ", 1)[1]
    data = verify_jwt(token)
    if not data or not data.get("user_id"):
        return None, None, (jsonify({"error": "invalid or expired token"}), 401)
    return data.get("user_id"), data.get("role"), None


def require_roles(allowed: List[str]):
    user_id, role, err = get_identity_from_request()
    if err:
        return None, None, err
    if allowed and (role not in allowed):
        return None, None, (jsonify({"error": "forbidden", "required_roles": allowed}), 403)
    return user_id, role, None
