"""Tests for reusable Document Sender templates."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest


def _install_storage_stubs() -> None:
    """Provide the narrow storage imports when HA is unavailable or stubbed."""
    try:
        __import__("homeassistant.helpers.storage")
        return
    except ImportError:
        pass
    homeassistant = sys.modules.setdefault("homeassistant", ModuleType("homeassistant"))
    helpers = sys.modules.setdefault(
        "homeassistant.helpers", ModuleType("homeassistant.helpers")
    )
    core = ModuleType("homeassistant.core")
    storage = ModuleType("homeassistant.helpers.storage")

    class HomeAssistant:
        pass

    class Store:
        @classmethod
        def __class_getitem__(cls, item: object) -> type[Store]:
            return cls

    core.HomeAssistant = HomeAssistant
    storage.Store = Store
    homeassistant.core = core
    helpers.storage = storage
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers.storage"] = storage


_install_storage_stubs()

from custom_components.document_sender.templates import TemplateManager  # noqa: E402


class FakeStore:
    """Minimal asynchronous Home Assistant Store replacement."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = data

    async def async_load(self) -> dict[str, Any] | None:
        """Return stored data."""
        return self.data

    async def async_save(self, data: dict[str, Any]) -> None:
        """Persist a detached top-level mapping."""
        self.data = dict(data)


def manager_with_store(store: FakeStore) -> TemplateManager:
    """Build a manager without a Home Assistant instance."""
    manager = object.__new__(TemplateManager)
    manager._store = store  # type: ignore[assignment]
    manager._data = {}
    return manager


@pytest.mark.asyncio
async def test_template_save_and_edit() -> None:
    """Edit a template in place while retaining its identity."""
    manager = manager_with_store(FakeStore())
    created = await manager.async_save(
        "Monthly documents",
        "Documents",
        "First body",
        "",
        recipients=["recipient@example.com"],
        attachment_ids=["attachment-one"],
    )
    edited = await manager.async_save(
        "Monthly documents",
        "Documents for {{ previous_month_name }}",
        "Updated body",
        "",
        created["id"],
        recipients=["recipient@example.com"],
        attachment_ids=["attachment-one"],
    )

    assert edited["id"] == created["id"]
    assert edited["created_at"] == created["created_at"]
    assert edited["subject"] == "Documents for {{ previous_month_name }}"
    assert manager.list() == [edited]


@pytest.mark.asyncio
async def test_template_attachment_ids_persist_across_loads_and_edits() -> None:
    """Never recreate or remove template attachments during monthly use."""
    store = FakeStore()
    manager = manager_with_store(store)
    created = await manager.async_save(
        "Monthly",
        "Subject",
        "Body",
        "",
        recipients=["recipient@example.com"],
        attachment_ids=["invoice", "terms"],
    )

    restored = manager_with_store(store)
    await restored.async_load()
    first_month = list(restored.get(created["id"])["attachment_ids"])  # type: ignore[index]
    second_month = list(restored.get(created["id"])["attachment_ids"])  # type: ignore[index]

    assert first_month == ["invoice", "terms"]
    assert second_month == first_month
    assert restored.get(created["id"])["attachment_ids"] == [  # type: ignore[index]
        "invoice",
        "terms",
    ]


@pytest.mark.asyncio
async def test_old_template_is_migrated_with_new_fields() -> None:
    """Load templates stored by versions before recipient persistence."""
    old = {
        "legacy": {
            "id": "legacy",
            "name": "Legacy",
            "subject": "Subject",
            "text": "Body",
            "html": "",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    }
    manager = manager_with_store(FakeStore(old))

    await manager.async_load()

    assert manager.get("legacy")["recipients"] == []  # type: ignore[index]
    assert manager.get("legacy")["attachment_ids"] == []  # type: ignore[index]
