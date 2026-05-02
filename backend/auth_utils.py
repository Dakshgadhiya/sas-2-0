import hashlib
import hmac
import time
import secrets
from functools import wraps

import jwt
from flask import request, jsonify, g

from backend import config

PBKDF2_ITERATIONS = 200_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password, hashed):
    try:
        if hashed.startswith("pbkdf2_sha256$"):
            _, iterations_str, salt_hex, hash_hex = hashed.split("$", 3)
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False

    # Legacy fallback (static salt) for existing users
    legacy_salt = config.SECRET_KEY.encode("utf-8")
    legacy_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), legacy_salt, 100000).hex()
    return hmac.compare_digest(legacy_hash, hashed)


def generate_token(user_id, role):
    normalized_role = (role or "").lower()
    payload = {
        "sub": user_id,
        "role": normalized_role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60 * 24,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGO)


def decode_token(token):
    return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGO])


def auth_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized"}), 401
            token = header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            g.user_id = payload.get("sub")
            g.role = (payload.get("role") or "").lower()
            required_role = role.lower() if role else None
            if required_role and g.role != required_role:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
