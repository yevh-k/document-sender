"""Unit tests for attachment size enforcement and HEIC conversion."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from custom_components.document_sender.image import _prepare_attachment


def test_oversized_non_image_attachment_is_rejected(tmp_path: Path) -> None:
    """Reject an attachment exceeding the configured byte limit."""
    source = tmp_path / "large.pdf"
    source.write_bytes(b"x" * 11)

    with pytest.raises(ValueError, match="exceeds the configured size limit"):
        _prepare_attachment(
            source,
            "large.pdf",
            "application/pdf",
            max_dimension=1600,
            quality=85,
            max_size_bytes=10,
        )


def test_heic_is_converted_to_jpeg_and_keeps_aspect_ratio(tmp_path: Path) -> None:
    """Convert a managed HEIC image to a correctly named JPEG attachment."""
    source = tmp_path / "portrait.heic"
    Image.new("RGB", (80, 40), "red").save(source, format="HEIF", quality=90)

    result = _prepare_attachment(
        source,
        "portrait.heic",
        "image/heic",
        max_dimension=40,
        quality=80,
        max_size_bytes=1024 * 1024,
    )

    assert result.name == "portrait.jpg"
    assert result.content_type == "image/jpeg"
    assert result.content.startswith(b"\xff\xd8")
    with Image.open(BytesIO(result.content)) as converted:
        assert converted.size == (40, 20)
