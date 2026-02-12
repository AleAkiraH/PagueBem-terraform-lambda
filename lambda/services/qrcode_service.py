"""QR Code Service — business logic for decoding QR/barcodes from images."""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, List, Optional

from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger()

# Optional backends
HAS_PYZBAR = False
HAS_CV2 = False

try:
    from pyzbar.pyzbar import decode as zbar_decode
    HAS_PYZBAR = True
except Exception:
    zbar_decode = None

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except Exception:
    cv2 = None
    np = None


# Preprocessing transforms for image enhancement
TRANSFORMS = [
    ("orig", lambda im: im),
    ("gray", lambda im: im.convert("L")),
    (
        "gray_resize_x2",
        lambda im: im.convert("L").resize(
            (im.size[0] * 2, im.size[1] * 2), Image.BICUBIC
        ),
    ),
    (
        "gray_resize_x3",
        lambda im: im.convert("L").resize(
            (im.size[0] * 3, im.size[1] * 3), Image.BICUBIC
        ),
    ),
    ("contrast_x2", lambda im: ImageEnhance.Contrast(im.convert("L")).enhance(2.0)),
    ("sharp_x2", lambda im: ImageEnhance.Sharpness(im).enhance(2.0)),
    (
        "contrast_gray_thresh",
        lambda im: ImageEnhance.Contrast(im.convert("L"))
        .enhance(2.0)
        .point(lambda p: 255 if p > 120 else 0),
    ),
    ("binary", lambda im: im.convert("L").point(lambda p: 255 if p > 128 else 0)),
    ("invert", lambda im: ImageOps.invert(im.convert("L"))),
]


class QrCodeService:
    """Service for QR/barcode decoding from images."""

    @staticmethod
    def decode_image(b64_string: str) -> Dict[str, Any]:
        """Decode QR/barcodes from a base64-encoded image string.

        Returns a dict with:
            found (bool), results (list), transform (str|None), data (str|list|None)
        """
        img = QrCodeService._decode_base64_to_image(b64_string)
        w, h = img.size
        logger.info("Input image size=%dx%d, mode=%s", w, h, img.mode)

        found = False
        results: List[Dict[str, str]] = []
        used_transform: Optional[str] = None

        for angle in (0, 90, 180, 270):
            for name, fn in TRANSFORMS:
                tname = f"{name}_rot{angle}"
                try:
                    img_t = fn(img.rotate(angle, expand=True))
                except Exception:
                    logger.exception("Transform error for %s", tname)
                    continue

                decoded = QrCodeService._try_decode(img_t)
                if decoded:
                    found = True
                    results = decoded
                    used_transform = tname
                    break
            if found:
                break

        if not found:
            return {
                "found": False,
                "message": "No QR/barcode detected with tried preprocessing steps",
            }

        response: Dict[str, Any] = {
            "found": True,
            "transform": used_transform,
            "results": results,
        }

        # Convenience: top-level data field
        if len(results) == 1:
            response["data"] = results[0].get("data")
        else:
            response["data"] = [r.get("data") for r in results]

        return response

    # ── Private helpers ──

    @staticmethod
    def _clean_b64(b64: str) -> str:
        """Remove data URI prefix and whitespace from base64 string."""
        if not isinstance(b64, str):
            raise ValueError("image must be a base64 string")
        if b64.startswith("data:"):
            parts = b64.split(",", 1)
            if len(parts) == 2:
                b64 = parts[1]
        return "".join(b64.split())

    @staticmethod
    def _decode_base64_to_image(b64: str) -> Image.Image:
        """Convert base64 string to PIL Image."""
        b64 = QrCodeService._clean_b64(b64)
        raw = base64.b64decode(b64)
        img = Image.open(io.BytesIO(raw))
        img.load()
        return img

    @staticmethod
    def _try_decode_pyzbar(img: Image.Image) -> List[Dict[str, str]]:
        """Try decoding with pyzbar."""
        try:
            decoded = zbar_decode(img)
            out = []
            for d in decoded:
                try:
                    data_str = d.data.decode("utf-8")
                except Exception:
                    data_str = d.data.decode("latin-1", errors="replace")
                out.append({"type": d.type, "data": data_str})
            return out
        except Exception:
            logger.exception("pyzbar decode error")
            return []

    @staticmethod
    def _try_decode_cv2(img: Image.Image) -> List[Dict[str, str]]:
        """Try decoding with OpenCV QRCodeDetector."""
        try:
            arr = np.array(img.convert("RGB"))
            bgr = arr[:, :, ::-1].copy()
            detector = cv2.QRCodeDetector()
            out = []

            if hasattr(detector, "detectAndDecodeMulti"):
                try:
                    retval, decoded_info, points, _ = detector.detectAndDecodeMulti(bgr)
                except Exception:
                    decoded_info = []
                if decoded_info is None:
                    decoded_info = []
                for info in decoded_info:
                    if info:
                        out.append({"type": "QRCODE", "data": info})
            else:
                try:
                    info, points, _ = detector.detectAndDecode(bgr)
                    if info:
                        out.append({"type": "QRCODE", "data": info})
                except Exception:
                    pass
            return out
        except Exception:
            logger.exception("cv2 decode error")
            return []

    @staticmethod
    def _try_decode(img: Image.Image) -> List[Dict[str, str]]:
        """Try pyzbar first, then fall back to cv2."""
        if HAS_PYZBAR:
            res = QrCodeService._try_decode_pyzbar(img)
            if res:
                return res
        if HAS_CV2:
            res = QrCodeService._try_decode_cv2(img)
            if res:
                return res
        return []
