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
    logger.info("✅ pyzbar loaded successfully")
except Exception as e:
    logger.warning(f"❌ pyzbar not available: {e}")
    zbar_decode = None

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
    logger.info("✅ OpenCV loaded successfully")
except Exception as e:
    logger.warning(f"❌ OpenCV not available: {e}")
    cv2 = None
    np = None


# Preprocessing transforms for image enhancement (BALANCED - works with most QR codes)
# Based on working script QrReader.py, but optimized for Lambda timeout
TRANSFORMS = [
    ("orig", lambda im: im),
    ("gray", lambda im: im.convert("L")),
    ("gray_resize_x2", lambda im: im.convert("L").resize((im.size[0]*2, im.size[1]*2), Image.BICUBIC)),
    ("contrast_x2", lambda im: ImageEnhance.Contrast(im.convert("L")).enhance(2.0)),
    ("sharp_x2", lambda im: ImageEnhance.Sharpness(im).enhance(2.0)),
    ("contrast_gray_thresh", lambda im: ImageEnhance.Contrast(im.convert("L")).enhance(2.0).point(lambda p: 255 if p > 120 else 0)),
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

        # OPTIMIZATION: If image is very large and we DON'T have pyzbar, downsample
        # (pyzbar works better with original size)
        max_dim = max(w, h)
        if max_dim > 1000 and not HAS_PYZBAR:
            scale = 1000 / max_dim
            new_w, new_h = int(w * scale), int(h * scale)
            logger.info("Downsampling large image to %dx%d (no pyzbar)", new_w, new_h)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        elif HAS_PYZBAR and max_dim > 1000:
            logger.info("Keeping original size (pyzbar available)")


        found = False
        results: List[Dict[str, str]] = []
        used_transform: Optional[str] = None

        # Try all 4 rotations (0, 90, 180, 270) to handle any orientation
        for angle in (0, 90, 180, 270):
            for name, fn in TRANSFORMS:
                tname = f"{name}_rot{angle}"
                try:
                    rotated = img.rotate(angle, expand=True) if angle != 0 else img
                    img_t = fn(rotated)
                except Exception:
                    logger.exception("Transform error for %s", tname)
                    continue

                decoded = QrCodeService._try_decode(img_t)
                if decoded:
                    found = True
                    results = decoded
                    used_transform = tname
                    logger.info("QR found with transform: %s", tname)
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
            if not HAS_PYZBAR:
                logger.warning("pyzbar not available")
                return []
            decoded = zbar_decode(img)
            logger.info(f"pyzbar found {len(decoded)} results")
            out = []
            for d in decoded:
                try:
                    data_str = d.data.decode("utf-8")
                except Exception:
                    data_str = d.data.decode("latin-1", errors="replace")
                out.append({"type": d.type, "data": data_str})
            return out
        except Exception as e:
            logger.exception(f"pyzbar decode error: {e}")
            return []

    @staticmethod
    def _try_decode_cv2(img: Image.Image) -> List[Dict[str, str]]:
        """Try decoding with OpenCV QRCodeDetector."""
        try:
            if not HAS_CV2:
                logger.warning("cv2 not available")
                return []
            arr = np.array(img.convert("RGB"))
            bgr = arr[:, :, ::-1].copy()
            detector = cv2.QRCodeDetector()
            out = []

            if hasattr(detector, "detectAndDecodeMulti"):
                try:
                    retval, decoded_info, points, _ = detector.detectAndDecodeMulti(bgr)
                    logger.info(f"cv2 detectAndDecodeMulti found {len(decoded_info) if decoded_info else 0}")
                except Exception as e:
                    logger.warning(f"cv2 detectAndDecodeMulti failed: {e}")
                    decoded_info = []
                if decoded_info is None:
                    decoded_info = []
                for info in decoded_info:
                    if info:
                        out.append({"type": "QRCODE", "data": info})
            else:
                try:
                    info, points, _ = detector.detectAndDecode(bgr)
                    logger.info(f"cv2 detectAndDecode found {'1' if info else '0'}")
                    if info:
                        out.append({"type": "QRCODE", "data": info})
                except Exception as e:
                    logger.warning(f"cv2 detectAndDecode failed: {e}")
            return out
        except Exception as e:
            logger.exception(f"cv2 decode error: {e}")
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
