"""QR Code Controller — handles HTTP request/response for QR Code decoding."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from dtos.qrcode_dto import DecodeRequest
from services.qrcode_service import QrCodeService
from utils.response import build_response

logger = logging.getLogger()


class QrCodeController:
    """Controller for QR Code related endpoints."""

    @staticmethod
    def decode(event: Dict[str, Any]) -> Dict[str, Any]:
        """POST /decode — Decode a QR/barcode from a base64 image."""
        try:
            # Parse body
            body = event.get("body", "")
            logger.info("Raw body type: %s, content length: %d", type(body), len(str(body)))
            
            if event.get("isBase64Encoded"):
                # Raw base64 body from API Gateway
                logger.info("Processing as base64 encoded body")
                dto = DecodeRequest(image_base64=body)
            else:
                if isinstance(body, str):
                    logger.info("Parsing body as JSON string")
                    body = json.loads(body)
                logger.info("Creating DecodeRequest from body: %s", list(body.keys()) if isinstance(body, dict) else type(body))
                dto = DecodeRequest(**body)

            # Call service
            logger.info("Calling QrCodeService.decode_image")
            result = QrCodeService.decode_image(dto.image_base64)

            return build_response(200, result)

        except ValueError as e:
            logger.warning("Validation error: %s", e)
            return build_response(400, {"error": str(e)})
        except Exception as e:
            logger.exception("Error in decode")
            return build_response(500, {"error": "Failed to decode image", "details": str(e)})
