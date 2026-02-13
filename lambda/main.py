"""AWS Lambda handler — PagueBem API

Catch-all handler that routes requests to the appropriate controller
based on the HTTP method and path.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from controller.qrcode_controller import QrCodeController
from utils.response import build_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Main Lambda handler — routes requests to controllers."""
    logger.info("Incoming event keys=%s", list(event.keys()) if isinstance(event, dict) else type(event))

    # Extract HTTP method and path from API Gateway v2 event
    request_context = event.get("requestContext", {})
    http_info = request_context.get("http", {})
    method = http_info.get("method", "UNKNOWN").upper()
    raw_path = http_info.get("path", "/").rstrip("/") or "/"

    # Remove stage prefix (e.g., /dev/health → /health)
    stage = request_context.get("stage", "")
    if stage and raw_path.startswith(f"/{stage}"):
        path = raw_path[len(f"/{stage}"):] or "/"
    else:
        path = raw_path

    logger.info("method=%s path=%s", method, path)

    try:
        # ── QR Code routes ──
        if path == "/decode" and method == "POST":
            return QrCodeController.decode(event)

        if path == "/health" and method == "GET":
            return build_response(200, {"status": "ok", "service": "paguebem-api"})

        # ── 404 ──
        return build_response(404, {"error": f"Route not found: {method} {path}"})

    except Exception as e:
        logger.exception("Unhandled error")
        return build_response(500, {"error": "Internal server error", "details": str(e)})
