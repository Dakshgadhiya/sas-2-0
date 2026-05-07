import json
import urllib.parse
from typing import Any, Dict, Optional

import jwt
from backend.auth_utils import decode_token
from backend import config


def get_request_body(request: Any) -> bytes:
    if hasattr(request, "json") and request.json is not None:
        return request.json
    if hasattr(request, "body"):
        return request.body
    if hasattr(request, "data"):
        return request.data
    if hasattr(request, "get_data"):
        return request.get_data()
    return b""


def parse_json(request: Any) -> Dict[str, Any]:
    body = get_request_body(request)
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    if isinstance(body, bytes):
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return {}
    if isinstance(body, str):
        try:
            return json.loads(body)
        except Exception:
            return {}
    return {}


def get_header(request: Any, name: str) -> Optional[str]:
    name_lower = name.lower()
    if hasattr(request, "headers"):
        try:
            headers = request.headers
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == name_lower:
                        return value
            elif hasattr(headers, "get"):
                return headers.get(name)
        except Exception:
            pass
    if hasattr(request, "environ"):
        environ = request.environ
        if isinstance(environ, dict):
            return environ.get(f"HTTP_{name_upper(name)}")
    return None


def name_upper(name: str) -> str:
    return name.replace("-", "_").upper()


def parse_query_params(request: Any) -> Dict[str, str]:
    if hasattr(request, "args") and request.args is not None:
        try:
            return {k: request.args.get(k) for k in request.args.keys()}
        except Exception:
            pass
    if hasattr(request, "query") and request.query is not None:
        if isinstance(request.query, dict):
            return {k: v for k, v in request.query.items()}
    if hasattr(request, "url"):
        try:
            parsed = urllib.parse.urlparse(request.url)
            return {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        except Exception:
            pass
    return {}


def get_query_param(request: Any, key: str, default: Optional[str] = None) -> Optional[str]:
    params = parse_query_params(request)
    return params.get(key, default)


def get_path(request: Any) -> str:
    path = None
    if hasattr(request, "path"):
        path = request.path
    if not path and hasattr(request, "url"):
        try:
            path = urllib.parse.urlparse(request.url).path
        except Exception:
            path = None
    if not path and hasattr(request, "environ"):
        environ = request.environ
        if isinstance(environ, dict):
            path = environ.get("PATH_INFO")
    if not path:
        return "/"
    return path


def json_response(body: Any, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    return {
        "statusCode": status,
        "headers": response_headers,
        "body": json.dumps(body, default=str),
    }


def error_response(message: str, status: int = 400) -> Dict[str, Any]:
    return json_response({"error": message}, status=status)


def auth_required(request: Any, role: str = None):
    authorization = get_header(request, "Authorization") or ""
    if not authorization.startswith("Bearer "):
        return None, error_response("Unauthorized", 401)

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        return None, error_response("Token expired", 401)
    except jwt.InvalidTokenError:
        return None, error_response("Invalid token", 401)
    except Exception:
        return None, error_response("Invalid token", 401)

    role_name = (payload.get("role") or "").lower()
    if role and role_name != role.lower():
        return None, error_response("Forbidden", 403)
    return payload, None
