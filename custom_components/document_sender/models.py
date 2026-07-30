"""Typed models used by Document Sender."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class AttachmentMetadata(TypedDict):
    """Stored attachment metadata."""

    id: str
    name: str
    path: str
    content_type: str
    created_at: str


class TemplateData(TypedDict):
    """Stored message template."""

    id: str
    name: str
    subject: str
    text: str
    html: str
    recipients: list[str]
    cc: list[str]
    bcc: list[str]
    attachment_ids: list[str]
    created_at: str
    updated_at: str


class ScheduleData(TypedDict, total=False):
    """Stored schedule definition."""

    id: str
    name: str
    schedule_type: str
    time: str
    weekday: int
    day: int
    date: str
    template_id: str
    subject: str
    text: str
    html: str
    recipients: list[str]
    cc: list[str]
    bcc: list[str]
    attachment_ids: list[str]
    enabled: bool
    last_run: str
    last_status: str
    last_error: str
    last_scheduled_occurrence: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Attachment:
    """A message attachment ready to send."""

    name: str
    path: Path
    content_type: str


@dataclass(frozen=True, slots=True)
class PreparedAttachment:
    """Attachment content after validation and optional image processing."""

    content: bytes
    content_type: str
    name: str


@dataclass(frozen=True, slots=True)
class MessageRequest:
    """Normalized request to send a message."""

    recipients: list[str]
    subject: str
    text: str
    html: str
    attachment_ids: list[str]
    source: str
    cc: list[str] | None = None
    bcc: list[str] | None = None
    schedule_id: str | None = None
    template_id: str | None = None


@dataclass(frozen=True, slots=True)
class SendResult:
    """Result returned after an SMTP attempt."""

    success: bool
    message_id: str | None
    error: str | None
    sent_at: datetime
    attachment_names: list[str]
