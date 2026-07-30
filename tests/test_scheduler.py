"""Tests for persistent monthly scheduling."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import ModuleType
from typing import Any

import pytest


def _install_scheduler_stubs() -> None:
    """Provide the narrow scheduling imports when HA is unavailable or stubbed."""
    try:
        __import__("homeassistant.helpers.event")
        __import__("homeassistant.helpers.storage")
        __import__("homeassistant.util.dt")
        return
    except ImportError:
        pass
    homeassistant = sys.modules.setdefault("homeassistant", ModuleType("homeassistant"))
    helpers = sys.modules.setdefault(
        "homeassistant.helpers", ModuleType("homeassistant.helpers")
    )
    core = ModuleType("homeassistant.core")
    event = ModuleType("homeassistant.helpers.event")
    storage = ModuleType("homeassistant.helpers.storage")
    util = ModuleType("homeassistant.util")
    dt = ModuleType("homeassistant.util.dt")

    class HomeAssistant:
        pass

    class Store:
        @classmethod
        def __class_getitem__(cls, item: object) -> type[Store]:
            return cls

    core.CALLBACK_TYPE = Any
    core.HomeAssistant = HomeAssistant
    event.async_track_time_interval = lambda *args: lambda: None
    storage.Store = Store
    dt.as_local = lambda value: value
    dt.now = lambda: datetime.now(UTC)
    dt.utcnow = lambda: datetime.now(UTC)
    homeassistant.core = core
    homeassistant.util = util
    helpers.event = event
    helpers.storage = storage
    util.dt = dt
    sys.modules.update(
        {
            "homeassistant.core": core,
            "homeassistant.helpers.event": event,
            "homeassistant.helpers.storage": storage,
            "homeassistant.util": util,
            "homeassistant.util.dt": dt,
        }
    )


_install_scheduler_stubs()

from custom_components.document_sender.models import ScheduleData  # noqa: E402
from custom_components.document_sender.scheduler import SchedulerManager  # noqa: E402


class FakeStore:
    """Minimal persistent store."""

    def __init__(self, data: dict[str, ScheduleData] | None = None) -> None:
        self.data = data
        self.saves = 0

    async def async_load(self) -> dict[str, ScheduleData] | None:
        """Load schedules."""
        return self.data

    async def async_save(self, data: dict[str, ScheduleData]) -> None:
        """Save schedules."""
        self.data = data
        self.saves += 1


def scheduler_with_store(store: FakeStore, callback: Any) -> SchedulerManager:
    """Build a scheduler without registering a real HA timer."""
    manager = object.__new__(SchedulerManager)
    manager._hass = object()  # type: ignore[assignment]
    manager._callback = callback
    manager._store = store  # type: ignore[assignment]
    manager._data = {}
    manager._unsub = None
    return manager


def monthly_schedule() -> ScheduleData:
    """Return a due monthly schedule."""
    return {
        "id": "monthly",
        "name": "Monthly documents",
        "schedule_type": "monthly",
        "template_id": "template",
        "day": 15,
        "time": "09:00",
        "enabled": True,
    }


@pytest.mark.asyncio
async def test_monthly_schedule_restores_after_restart(monkeypatch: Any) -> None:
    """Restore stored definitions and register the async time helper."""
    schedule = monthly_schedule()
    schedule["enabled"] = False
    store = FakeStore({"monthly": schedule})
    manager = scheduler_with_store(store, _noop_callback)
    registered: list[object] = []
    monkeypatch.setattr(
        "custom_components.document_sender.scheduler.async_track_time_interval",
        lambda hass, callback, interval: registered.append(callback) or (lambda: None),
    )

    await manager.async_load()

    assert manager.get("monthly") == schedule
    assert registered
    await manager.async_close()


@pytest.mark.asyncio
async def test_duplicate_monthly_send_is_prevented() -> None:
    """Claim a monthly occurrence before delivery and send it only once."""
    calls: list[str] = []

    async def callback(schedule: ScheduleData) -> None:
        calls.append(schedule["id"])

    schedule = monthly_schedule()
    store = FakeStore({"monthly": schedule})
    manager = scheduler_with_store(store, callback)
    manager._data = {"monthly": schedule}
    now = datetime(2026, 7, 15, 9, 5, tzinfo=UTC)

    await manager._async_tick(now)
    await manager._async_tick(now)

    assert calls == ["monthly"]
    assert schedule["last_scheduled_occurrence"] == "2026-07-15"
    assert schedule["last_status"] == "success"
    assert store.saves >= 2


@pytest.mark.asyncio
async def test_run_now_does_not_consume_scheduled_occurrence() -> None:
    """Run immediately while leaving the next monthly occurrence eligible."""
    calls: list[str] = []

    async def callback(schedule: ScheduleData) -> None:
        calls.append(schedule["id"])

    schedule = monthly_schedule()
    store = FakeStore({"monthly": schedule})
    manager = scheduler_with_store(store, callback)
    manager._data = {"monthly": schedule}

    result = await manager.async_run_now("monthly")

    assert calls == ["monthly"]
    assert result["last_status"] == "success"
    assert "last_scheduled_occurrence" not in result


async def _noop_callback(schedule: ScheduleData) -> None:
    """Do nothing."""
