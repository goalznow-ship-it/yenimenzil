"""Media validation via Pillow."""

import logging
from io import BytesIO

from PIL import Image as PILImage

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Validation thresholds from settings
MIN_RESOLUTION = (settings.MEDIA_MIN_WIDTH, settings.MEDIA_MIN_WIDTH * 3 // 4)
MAX_FILE_SIZE = settings.MEDIA_MAX_SIZE_MB
ALLOWED_FORMATS = ["JPEG", "PNG", "WEBP"]


def validate_image_file(file_data: bytes, filename: str) -> tuple[bool, str | None]:
    """Validate an uploaded image file using Pillow.

    Returns (is_valid, error_message).
    """
    try:
        im = PILImage.open(BytesIO(file_data))
        fmt = im.format or "UNKNOWN"
        width, height = im.size

        # Check format
        if fmt not in ALLOWED_FORMATS:
            return (
                False,
                f"Format {fmt} not allowed. Allowed: {', '.join(ALLOWED_FORMATS)}",
            )

        # Check minimum resolution
        if width < MIN_RESOLUTION[0] or height < MIN_RESOLUTION[1]:
            msg = (
                f"Resolution too small: {width}x{height}. "
                f"Minimum: {MIN_RESOLUTION[0]}x{MIN_RESOLUTION[1]}"
            )
            return (False, msg)

        # Check file size
        file_size_mb = len(file_data) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE:
            return (
                False,
                f"File too large: {file_size_mb:.1f}MB. Maximum: {MAX_FILE_SIZE}MB",
            )

        # Verify image is not corrupted
        im.verify()

        return True, None
    except Exception as e:  # noqa: BLE001 - untrusted file data, any decoder failure must be rejected
        logger.warning(f"Image validation error for {filename}: {e}")
        return False, f"Invalid image file: {e!s}"


def get_image_metadata(file_data: bytes) -> dict | None:
    """Extract basic metadata from an image file."""
    try:
        im = PILImage.open(BytesIO(file_data))
        return {
            "width": im.width,
            "height": im.height,
            "format": im.format,
            "mode": im.mode,
            "size_bytes": len(file_data),
        }
    except Exception as e:  # noqa: BLE001 - untrusted file data, any decoder failure must be handled
        logger.warning(f"Could not extract image metadata: {e}")
        return None
