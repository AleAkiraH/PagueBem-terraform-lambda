"""QR Code DTOs — request/response validation with Pydantic."""

from pydantic import BaseModel, field_validator


class DecodeRequest(BaseModel):
    """Request DTO for QR Code decoding."""
    image_base64: str

    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("image_base64 must be a non-empty string")
        # Accept with or without data URI prefix
        return v

    # Also accept common field name aliases
    class Config:
        populate_by_name = True

    def __init__(self, **data):
        # Support alternative field names
        for alias in ("image", "img", "b64"):
            if alias in data and "image_base64" not in data:
                data["image_base64"] = data.pop(alias)
        super().__init__(**data)


class DecodeResult(BaseModel):
    """Single decoded result."""
    type: str
    data: str


class DecodeResponse(BaseModel):
    """Response DTO for QR Code decoding."""
    found: bool
    transform: str | None = None
    results: list[DecodeResult] = []
    data: str | list[str] | None = None
    message: str | None = None
