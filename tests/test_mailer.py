"""Unit tests for the asynchronous Document Sender mail engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiosmtplib.errors import SMTPAuthenticationError, SMTPTimeoutError

from custom_components.document_sender.mailer import MailConfig, Mailer
from custom_components.document_sender.models import (
    Attachment,
    MessageRequest,
    PreparedAttachment,
)


class FakeAttachmentManager:
    """Minimal managed-attachment resolver used by mailer unit tests."""

    def __init__(self, attachments: list[Attachment] | None = None) -> None:
        """Initialize test attachments."""
        self._attachments = attachments or []

    def get_many(self, attachment_ids: list[str]) -> list[Attachment]:
        """Return configured attachments."""
        return self._attachments if attachment_ids else []


class FakeImageProcessor:
    """Return a deterministic processed attachment."""

    async def async_prepare(self, attachment: Attachment) -> PreparedAttachment:
        """Simulate attachment processing."""
        return PreparedAttachment(
            content=b"processed",
            content_type="image/jpeg",
            name="processed-photo.jpg",
        )


@pytest.fixture
def mail_config() -> MailConfig:
    """Return SMTP settings without real credentials."""
    return MailConfig(
        host="smtp.example.com",
        port=587,
        username="sender@example.com",
        password="not-a-real-password",
        sender_name="Document Sender",
        sender_email="sender@example.com",
        use_tls=True,
    )


def _request(*, attachments: list[str] | None = None) -> MessageRequest:
    """Build a complete send request."""
    return MessageRequest(
        recipients=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Test message",
        text="Plain body",
        html="<p>HTML body</p>",
        attachment_ids=attachments or [],
        source="test",
    )


@pytest.mark.asyncio
async def test_smtp_success_builds_multipart_and_hides_bcc(
    mail_config: MailConfig,
) -> None:
    """Send multipart content with processed attachment metadata."""
    attachment = Attachment("photo.heic", Path("unused"), "image/heic")
    mailer = Mailer(
        mail_config,
        FakeAttachmentManager([attachment]),
        FakeImageProcessor(),
        retry_delay=0,
    )
    send_mock = AsyncMock(return_value=({}, "accepted"))

    with patch("custom_components.document_sender.mailer.aiosmtplib.send", send_mock):
        result = await mailer.async_send(_request(attachments=["managed-id"]))

    assert result.success is True
    assert result.attachment_names == ["processed-photo.jpg"]
    awaited = send_mock.await_args
    assert awaited is not None
    message = awaited.args[0]
    assert message["To"] == "to@example.com"
    assert message["Cc"] == "cc@example.com"
    assert message["Bcc"] is None
    assert message.get_body(preferencelist=("plain",)).get_content().strip() == (
        "Plain body"
    )
    assert message.get_body(preferencelist=("html",)).get_content().strip() == (
        "<p>HTML body</p>"
    )
    assert [part.get_filename() for part in message.iter_attachments()] == [
        "processed-photo.jpg"
    ]
    assert awaited.kwargs["recipients"] == [
        "to@example.com",
        "cc@example.com",
        "bcc@example.com",
    ]


@pytest.mark.asyncio
async def test_authentication_failure_is_not_retried(
    mail_config: MailConfig,
) -> None:
    """Return a safe authentication error after one attempt."""
    mailer = Mailer(
        mail_config,
        FakeAttachmentManager(),
        FakeImageProcessor(),
        retry_delay=0,
    )
    send_mock = AsyncMock(
        side_effect=SMTPAuthenticationError(535, "Authentication rejected")
    )

    with patch("custom_components.document_sender.mailer.aiosmtplib.send", send_mock):
        result = await mailer.async_send(_request())

    assert result.success is False
    assert result.error == (
        "SMTP authentication failed; verify the username and password"
    )
    assert send_mock.await_count == 1
    assert mail_config.password not in result.error


@pytest.mark.asyncio
async def test_timeout_is_retried_once(mail_config: MailConfig) -> None:
    """Retry a transient timeout once, then return a safe timeout error."""
    mailer = Mailer(
        mail_config,
        FakeAttachmentManager(),
        FakeImageProcessor(),
        retry_delay=0,
    )
    send_mock = AsyncMock(side_effect=SMTPTimeoutError("timed out"))

    with patch("custom_components.document_sender.mailer.aiosmtplib.send", send_mock):
        result = await mailer.async_send(_request())

    assert result.success is False
    assert result.error == "SMTP delivery timed out"
    assert send_mock.await_count == 2
