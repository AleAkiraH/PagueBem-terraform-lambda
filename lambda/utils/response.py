"""Response utility — standardized API Gateway response builder."""

from __future__ import annotations

import json
from typing import Any, Dict


def build_response(status_code: int, body: Any, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    """Build a standard API Gateway v2 response."""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
