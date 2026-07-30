"""Persistent attachment manager."""

from __future__ import annotations

import mimetypes
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import ATTACHMENTS_DIRECTORY, STORAGE_KEY_ATTACHMENTS, STORAGE_VERSION
from .models import Attachment, AttachmentMetadata


class AttachmentManager:
    """Copy and track attachments owned by this integration."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the attachment store."""
        self._hass = hass
        self._entry_id = entry_id
        self._store: Store[dict[str, AttachmentMetadata]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_ATTACHMENTS}.{entry_id}"
        )
        self._data: dict[str, AttachmentMetadata] = {}
        self._directory = Path(hass.config.path(ATTACHMENTS_DIRECTORY, entry_id))

    async def async_load(self) -> None:
        """Load metadata and create the managed directory."""
        stored = await self._store.async_load()
        self._data = stored or {}
        await self._hass.async_add_executor_job(
            self._directory.mkdir, 0o700, True, True
        )

    async def async_add(
        self, source: str, name: str | None = None
    ) -> AttachmentMetadata:
        """Copy a readable source file into managed storage."""
        source_path = await self._hass.async_add_executor_job(
            _validated_source_path, source
        )
        if not self._hass.config.is_allowed_path(str(source_path)):
            raise ValueError(
                "Attachment path is outside Home Assistant's allowed paths"
            )

        attachment_id = uuid4().hex
        display_name = Path(name or source_path.name).name
        if not display_name:
            raise ValueError("Attachment name must not be empty")
        target = self._directory / f"{attachment_id}_{display_name}"
        await self._hass.async_add_executor_job(_copy_file, source_path, target)
        content_type = _content_type_for_name(display_name)
        metadata: AttachmentMetadata = {
            "id": attachment_id,
            "name": display_name,
            "path": str(target),
            "content_type": content_type,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._data[attachment_id] = metadata
        await self._store.async_save(self._data)
        return metadata

    async def async_add_bytes(
        self, name: str, content_type: str, content: bytes
    ) -> AttachmentMetadata:
        """Store a browser-uploaded attachment in private managed storage."""
        display_name = Path(name).name
        if not display_name or display_name != name or len(display_name) > 255:
            raise ValueError("Attachment filename is invalid")
        if not content_type or "/" not in content_type or len(content_type) > 128:
            raise ValueError("Attachment MIME type is invalid")
        attachment_id = uuid4().hex
        target = self._directory / f"{attachment_id}_{display_name}"
        await self._hass.async_add_executor_job(_write_file, target, content)
        metadata: AttachmentMetadata = {
            "id": attachment_id,
            "name": display_name,
            "path": str(target),
            "content_type": content_type.casefold(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._data[attachment_id] = metadata
        await self._store.async_save(self._data)
        return metadata

    async def async_remove(self, attachment_id: str) -> bool:
        """Remove an attachment and its managed file."""
        metadata = self._data.pop(attachment_id, None)
        if metadata is None:
            return False
        await self._hass.async_add_executor_job(_unlink_file, Path(metadata["path"]))
        await self._store.async_save(self._data)
        return True

    def get(self, attachment_id: str) -> Attachment | None:
        """Get a single attachment ready for a mail message."""
        metadata = self._data.get(attachment_id)
        if metadata is None:
            return None
        return Attachment(
            name=metadata["name"],
            path=Path(metadata["path"]),
            content_type=metadata["content_type"],
        )

    def list_metadata(self) -> list[AttachmentMetadata]:
        """Return metadata without exposing mutable internal state."""
        return list(self._data.values())

    def get_many(self, attachment_ids: list[str]) -> list[Attachment]:
        """Resolve available attachment IDs."""
        return [attachment for item in attachment_ids if (attachment := self.get(item))]

    def list(self) -> list[AttachmentMetadata]:
        """Return metadata using the legacy manager API."""
        return self.list_metadata()


def _copy_file(source: Path, target: Path) -> None:
    """Copy safely in the executor."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _validated_source_path(source: str) -> Path:
    """Resolve a source file outside the event loop."""
    source_path = Path(source).expanduser().resolve(strict=True)
    if not source_path.is_file():
        raise ValueError("Attachment path must point to a file")
    return source_path


def _unlink_file(path: Path) -> None:
    """Delete a managed file if it exists."""
    path.unlink(missing_ok=True)


def _write_file(target: Path, content: bytes) -> None:
    """Write one upload atomically enough for private managed storage."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _content_type_for_name(name: str) -> str:
    """Resolve common image content types consistently across host platforms."""
    extension = Path(name).suffix.casefold()
    if extension in {".heic", ".heif"}:
        return "image/heic"
    return mimetypes.guess_type(name)[0] or "application/octet-stream"
