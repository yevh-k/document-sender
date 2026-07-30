"""SQLite delivery log for Document Sender."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC
from pathlib import Path
from typing import Any, cast

from homeassistant.core import HomeAssistant

from .const import DATABASE_FILE
from .models import MessageRequest, SendResult


class DeliveryDatabase:
    """Execute short SQLite transactions in Home Assistant's executor."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Set up a log database path per config entry."""
        self._hass = hass
        self._path = Path(hass.config.path(".storage", f"{entry_id}_{DATABASE_FILE}"))

    async def async_initialize(self) -> None:
        """Create the delivery log table."""
        await self._hass.async_add_executor_job(self._initialize)

    async def async_log(self, request: MessageRequest, result: SendResult) -> None:
        """Write a delivery outcome."""
        await self._hass.async_add_executor_job(self._log, request, result)

    async def async_last_successful(self) -> dict[str, Any] | None:
        """Return the most recent successfully sent request."""
        return cast(
            dict[str, Any] | None,
            await self._hass.async_add_executor_job(self._last_successful),
        )

    async def async_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent outcomes for diagnostics or a future UI."""
        return cast(
            list[dict[str, Any]],
            await self._hass.async_add_executor_job(self._recent, limit),
        )

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    cc TEXT NOT NULL DEFAULT '[]',
                    bcc TEXT NOT NULL DEFAULT '[]',
                    subject TEXT NOT NULL,
                    text_body TEXT NOT NULL,
                    html_body TEXT NOT NULL,
                    attachment_ids TEXT NOT NULL,
                    attachment_names TEXT NOT NULL,
                    source TEXT NOT NULL,
                    schedule_id TEXT,
                    template_id TEXT,
                    success INTEGER NOT NULL,
                    message_id TEXT,
                    error TEXT
                )
                """)
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(deliveries)"
                ).fetchall()
            }
            if "cc" not in columns:
                connection.execute(
                    "ALTER TABLE deliveries ADD COLUMN cc TEXT NOT NULL DEFAULT '[]'"
                )
            if "bcc" not in columns:
                connection.execute(
                    "ALTER TABLE deliveries ADD COLUMN bcc TEXT NOT NULL DEFAULT '[]'"
                )

    def _log(self, request: MessageRequest, result: SendResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO deliveries (
                    created_at, recipients, cc, bcc, subject, text_body, html_body,
                    attachment_ids, attachment_names, source, schedule_id,
                    template_id, success, message_id, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.sent_at.astimezone(UTC).isoformat(),
                    json.dumps(request.recipients),
                    json.dumps(request.cc or []),
                    json.dumps(request.bcc or []),
                    request.subject,
                    request.text,
                    request.html,
                    json.dumps(request.attachment_ids),
                    json.dumps(result.attachment_names),
                    request.source,
                    request.schedule_id,
                    request.template_id,
                    int(result.success),
                    result.message_id,
                    result.error,
                ),
            )

    def _last_successful(self) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT recipients, cc, bcc, subject, text_body, html_body,
                attachment_ids, source, schedule_id, template_id FROM deliveries
                WHERE success = 1 ORDER BY id DESC LIMIT 1"""
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["recipients"] = json.loads(result["recipients"])
        result["cc"] = json.loads(result["cc"])
        result["bcc"] = json.loads(result["bcc"])
        result["attachment_ids"] = json.loads(result["attachment_ids"])
        return result

    def _recent(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM deliveries ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]
