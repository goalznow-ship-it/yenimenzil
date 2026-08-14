"""Image optimization: thumbnails and WebP conversion via Pillow.

Falls back gracefully (original bytes returned unchanged) when Pillow is
unavailable or processing fails, so uploads never break.
"""

from __future__ import annotations

import io
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:  # pragma: no cover - graceful fallback
    Image = None  # type: ignore[assignment]


def make_thumbnail(
    file_data: bytes,
    filename: str,
    max_width: int | None = None,
    quality: int | None = None,
) -> bytes | None:
    """Create a resized WebP thumbnail from image bytes.

    Returns None if the image cannot be processed (non-image, too small,
    Pillow missing). Callers should fall back to the original file.
    """
    if Image is None:
        return None
    max_width = max_width or settings.MEDIA_THUMB_WIDTH
    quality = quality or settings.MEDIA_THUMB_QUALITY
    try:
        with Image.open(io.BytesIO(file_data)) as im:
            im = im.convert("RGB")
            if im.width <= max_width:
                return None
            ratio = max_width / im.width
            new_size = (max_width, max(1, int(im.height * ratio)))
            im = im.resize(new_size, Image.LANCZOS)
            out = io.BytesIO()
            im.save(out, format="WEBP", quality=quality, method=4)
            return out.getvalue()
    except Exception as exc:  # noqa: BLE001 - never break uploads
        logger.warning("Thumbnail generation skipped: %s", exc)
        return None


def webp_suffix() -> str:
    """Suffix used for generated thumbnails (kept consistent with format)."""
    return ".webp"
