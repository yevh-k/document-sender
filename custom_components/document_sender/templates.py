"""Persistent template manager."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY_TEMPLATES, STORAGE_VERSION
from .models import TemplateData


class TemplateManager:
    """Store reusable plain-text and HTML message templates."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize storage."""
        self._store: Store[dict[str, TemplateData]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_TEMPLATES}.{entry_id}"
        )
        self._data: dict[str, TemplateData] = {}

    async def async_load(self) -> None:
        """Load template data."""
        self._data = await self._store.async_load() or {}

    async def async_save(
        self,
        name: str,
        subject: str,
        text: str,
        html: str,
        template_id: str | None = None,
    ) -> TemplateData:
        """Create or update a reusable template."""
        now = datetime.now(UTC).isoformat()
        identifier = template_id or uuid4().hex
        existing = self._data.get(identifier)
        template: TemplateData = {
            "id": identifier,
            "name": name,
            "subject": subject,
            "text": text,
            "html": html,
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }
        self._data[identifier] = template
        await self._store.async_save(self._data)
        return template

    async def async_remove(self, template_id: str) -> bool:
        """Delete a template."""
        if self._data.pop(template_id, None) is None:
            return False
        await self._store.async_save(self._data)
        return True

    def get(self, template_id: str) -> TemplateData | None:
        """Get a template by ID."""
        return self._data.get(template_id)

    def list(self) -> list[TemplateData]:
        """Return all stored templates."""
        return list(self._data.values())
