"""Attachment validation, image resizing, and HEIC conversion."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from .models import Attachment, PreparedAttachment

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

register_heif_opener(thumbnails=False)

_JPEG_FORMATS = {"JPEG", "JPG"}
_WEBP_FORMATS = {"WEBP"}
_PNG_FORMATS = {"PNG"}
_HEIF_FORMATS = {"HEIF", "HEIC"}
_MAX_RESIZE_ATTEMPTS = 8


class ImageProcessor:
    """Prepare outgoing attachments without blocking the Home Assistant loop."""

    def __init__(
        self,
        hass: HomeAssistant,
        max_dimension: int,
        quality: int,
        max_attachment_size_mb: int,
    ) -> None:
        """Initialize the image and attachment size policy."""
        self._hass = hass
        self._max_dimension = max_dimension
        self._quality = quality
        self._max_attachment_size_bytes = max_attachment_size_mb * 1024 * 1024

    async def async_prepare(self, attachment: Attachment) -> PreparedAttachment:
        """Read, validate, and resize or convert a managed attachment."""
        return cast(
            PreparedAttachment,
            await self._hass.async_add_executor_job(
                _prepare_attachment,
                attachment.path,
                attachment.name,
                attachment.content_type,
                self._max_dimension,
                self._quality,
                self._max_attachment_size_bytes,
            ),
        )


def _prepare_attachment(
    path: Path,
    name: str,
    content_type: str,
    max_dimension: int,
    quality: int,
    max_size_bytes: int,
) -> PreparedAttachment:
    """Perform filesystem and Pillow work outside Home Assistant's event loop."""
    source = path.read_bytes()
    if not content_type.startswith("image/"):
        _ensure_size(len(source), max_size_bytes, name)
        return PreparedAttachment(source, content_type, name)

    try:
        with Image.open(BytesIO(source)) as opened:
            source_format = opened.format
            opened.load()
            image = ImageOps.exif_transpose(opened)
            output_format, output_type, output_name = _output_details(
                source_format, name
            )
            payload = _resize_to_limit(
                image,
                output_format,
                max_dimension,
                quality,
                max_size_bytes,
            )
    except (OSError, UnidentifiedImageError) as err:
        raise ValueError(f"Unable to process image attachment '{name}'") from err
    return PreparedAttachment(payload, output_type, output_name)


def _output_details(image_format: str | None, name: str) -> tuple[str, str, str]:
    """Select an output format and convert HEIC/HEIF to broadly supported JPEG."""
    normalized = (image_format or "").upper()
    suffix = Path(name).suffix.casefold()
    if normalized in _HEIF_FORMATS or suffix in {".heic", ".heif"}:
        return "JPEG", "image/jpeg", f"{Path(name).stem}.jpg"
    if normalized in _PNG_FORMATS:
        return "PNG", "image/png", name
    if normalized in _WEBP_FORMATS:
        return "WEBP", "image/webp", name
    if normalized in _JPEG_FORMATS:
        return "JPEG", "image/jpeg", name
    raise ValueError(f"Unsupported image attachment format: {suffix or normalized}")


def _resize_to_limit(
    source: Image.Image,
    output_format: str,
    max_dimension: int,
    quality: int,
    max_size_bytes: int,
) -> bytes:
    """Preserve aspect ratio while fitting the image into configured constraints."""
    image = source.copy()
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    for _ in range(_MAX_RESIZE_ATTEMPTS):
        payload = _encode_image(image, output_format, quality)
        if len(payload) <= max_size_bytes:
            return payload
        image.thumbnail(
            (max(1, int(image.width * 0.85)), max(1, int(image.height * 0.85))),
            Image.Resampling.LANCZOS,
        )
    raise ValueError("Image attachment could not be reduced below the configured size")


def _encode_image(image: Image.Image, output_format: str, quality: int) -> bytes:
    """Encode an image using the configured lossy quality where supported."""
    prepared = image
    if output_format == "JPEG" and image.mode not in {"RGB", "L"}:
        prepared = image.convert("RGB")
    buffer = BytesIO()
    if output_format == "PNG":
        prepared.save(buffer, format="PNG", optimize=True, compress_level=9)
    else:
        prepared.save(
            buffer,
            format=output_format,
            quality=quality,
            optimize=True,
        )
    return buffer.getvalue()


def _ensure_size(size_bytes: int, max_size_bytes: int, name: str) -> None:
    """Reject non-image attachments above the configured hard limit."""
    if size_bytes > max_size_bytes:
        raise ValueError(f"Attachment '{name}' exceeds the configured size limit")
