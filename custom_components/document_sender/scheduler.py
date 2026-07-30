"""Persistent daily, weekly, monthly and one-time scheduling."""

from __future__ import annotations

import calendar
import logging
from collections.abc import Awaitable, Callable
from datetime import date, datetime, time, timedelta
from uuid import uuid4

from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_ONCE,
    SCHEDULE_TYPES,
    SCHEDULE_WEEKLY,
    STORAGE_KEY_SCHEDULES,
    STORAGE_VERSION,
)
from .models import ScheduleData

_LOGGER = logging.getLogger(__name__)
ScheduleCallback = Callable[[ScheduleData], Awaitable[None]]


class SchedulerManager:
    """Persist schedules and evaluate them once a minute in local HA time."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, callback: ScheduleCallback
    ) -> None:
        """Initialize a schedule manager."""
        self._hass = hass
        self._callback = callback
        self._store: Store[dict[str, ScheduleData]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_SCHEDULES}.{entry_id}"
        )
        self._data: dict[str, ScheduleData] = {}
        self._unsub: CALLBACK_TYPE | None = None

    async def async_load(self) -> None:
        """Load schedules and start time tracking."""
        self._data = await self._store.async_load() or {}
        self._unsub = async_track_time_interval(
            self._hass, self._async_tick, timedelta(minutes=1)
        )
        await self._async_tick(dt_util.utcnow())

    async def async_close(self) -> None:
        """Stop scheduled callbacks."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def async_save(self, schedule: ScheduleData) -> ScheduleData:
        """Create or update a schedule after validating it."""
        self._validate(schedule)
        now = dt_util.utcnow().isoformat()
        identifier = schedule.get("id") or uuid4().hex
        existing = self._data.get(identifier, {})
        schedule["id"] = identifier
        schedule["created_at"] = existing.get("created_at", now)
        schedule["updated_at"] = now
        if "last_run" not in schedule and "last_run" in existing:
            schedule["last_run"] = existing["last_run"]
        schedule.setdefault("enabled", True)
        schedule.setdefault("attachment_ids", [])
        schedule.setdefault("recipients", [])
        self._data[identifier] = schedule
        await self._store.async_save(self._data)
        return schedule

    async def async_remove(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if self._data.pop(schedule_id, None) is None:
            return False
        await self._store.async_save(self._data)
        return True

    def list(self) -> list[ScheduleData]:
        """Return schedules."""
        return list(self._data.values())

    async def _async_tick(self, now_utc: datetime) -> None:
        """Dispatch due schedules, with one delivery per schedule occurrence."""
        now = dt_util.as_local(now_utc)
        changed = False
        for schedule in list(self._data.values()):
            if not schedule.get("enabled", True) or not _is_due(schedule, now):
                continue
            try:
                await self._callback(schedule)
            except Exception:
                _LOGGER.exception(
                    "Scheduled Document Sender job failed: %s", schedule["id"]
                )
            schedule["last_run"] = now.isoformat()
            if schedule["schedule_type"] == SCHEDULE_ONCE:
                schedule["enabled"] = False
            changed = True
        if changed:
            await self._store.async_save(self._data)

    @staticmethod
    def _validate(schedule: ScheduleData) -> None:
        """Validate schedule structure independently of the service schema."""
        if schedule.get("schedule_type") not in SCHEDULE_TYPES:
            raise ValueError("Unsupported schedule type")
        _parse_time(schedule.get("time", ""))
        if schedule["schedule_type"] == SCHEDULE_WEEKLY and schedule.get(
            "weekday"
        ) not in range(7):
            raise ValueError("Weekly schedules require weekday from 0 (Monday) to 6")
        if (
            schedule["schedule_type"] == SCHEDULE_MONTHLY
            and not 1 <= int(schedule.get("day", 0)) <= 31
        ):
            raise ValueError("Monthly schedules require a day from 1 to 31")
        if schedule["schedule_type"] == SCHEDULE_ONCE:
            try:
                date.fromisoformat(str(schedule.get("date", "")))
            except ValueError as err:
                raise ValueError(
                    "One-time schedules require ISO date YYYY-MM-DD"
                ) from err


def _is_due(schedule: ScheduleData, now: datetime) -> bool:
    """Return whether the local minute contains an unprocessed occurrence."""
    run_date = _due_date(schedule, now.date())
    if (
        run_date is None
        or now.date() != run_date
        or now.time() < _parse_time(schedule["time"])
    ):
        return False
    last_run = schedule.get("last_run")
    if last_run is None:
        return True
    return datetime.fromisoformat(last_run).date() != run_date


def _due_date(schedule: ScheduleData, today: date) -> date | None:
    """Calculate the date that a schedule targets today, if any."""
    schedule_type = schedule["schedule_type"]
    if schedule_type == SCHEDULE_DAILY:
        return today
    if schedule_type == SCHEDULE_WEEKLY:
        return today if today.weekday() == schedule["weekday"] else None
    if schedule_type == SCHEDULE_MONTHLY:
        day = min(schedule["day"], calendar.monthrange(today.year, today.month)[1])
        return today if today.day == day else None
    if schedule_type == SCHEDULE_ONCE:
        return date.fromisoformat(schedule["date"])
    return None


def _parse_time(value: str) -> time:
    """Parse an HH:MM string for a local schedule."""
    try:
        return time.fromisoformat(value)
    except ValueError as err:
        raise ValueError("Schedule time must use HH:MM or HH:MM:SS") from err
