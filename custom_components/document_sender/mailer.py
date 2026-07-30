"""Asynchronous SMTP mail engine for Document Sender."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, make_msgid
from typing import Any, Protocol

import aiosmtplib
from aiosmtplib.errors import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPException,
    SMTPResponseException,
    SMTPServerDisconnected,
    SMTPTimeoutError,
)

from .const import (
    CONF_PASSWORD,
    CONF_SENDER_EMAIL,
    CONF_SENDER_NAME,
    CONF_SMTP_HOST,
    CONF_SMTP_PORT,
    CONF_USE_TLS,
    CONF_USERNAME,
)
from .models import Attachment, MessageRequest, PreparedAttachment, SendResult

_LOGGER = logging.getLogger(__name__)

DEFAULT_SMTP_TIMEOUT = 30.0
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_ATTEMPTS = 2
_EMAIL_PATTERN = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")


class AttachmentResolver(Protocol):
    """Resolve managed attachment IDs to stored attachment records."""

    def get_many(self, attachment_ids: list[str]) -> list[Attachment]:
        """Resolve attachment IDs."""
        ...


class AttachmentProcessor(Protocol):
    """Prepare a managed attachment for MIME serialization."""

    async def async_prepare(self, attachment: Attachment) -> PreparedAttachment:
        """Prepare one attachment."""
        ...


@dataclass(frozen=True, slots=True)
class MailConfig:
    """Validated SMTP configuration copied from a config entry."""

    host: str
    port: int
    username: str
    password: str
    sender_name: str
    sender_email: str
    use_tls: bool

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> MailConfig:
        """Create typed SMTP configuration from Home Assistant entry data."""
        return cls(
            host=str(config[CONF_SMTP_HOST]),
            port=int(config[CONF_SMTP_PORT]),
            username=str(config[CONF_USERNAME]),
            password=str(config[CONF_PASSWORD]),
            sender_name=str(config.get(CONF_SENDER_NAME, "")),
            sender_email=str(config[CONF_SENDER_EMAIL]),
            use_tls=bool(config[CONF_USE_TLS]),
        )


class Mailer:
    """Build multipart MIME messages and send them through async SMTP."""

    def __init__(
        self,
        config: MailConfig,
        attachment_manager: AttachmentResolver,
        image_processor: AttachmentProcessor,
        *,
        timeout: float = DEFAULT_SMTP_TIMEOUT,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        """Initialize the mail engine and bounded retry policy."""
        self._config = config
        self._attachments = attachment_manager
        self._images = image_processor
        self._timeout = timeout
        self._max_attempts = max(1, max_attempts)
        self._retry_delay = max(0.0, retry_delay)

    async def async_send(self, request: MessageRequest) -> SendResult:
        """Prepare and send one message without blocking Home Assistant."""
        sent_at = datetime.now(UTC)
        try:
            _validate_request(request, self._config.sender_email)
        except ValueError as err:
            return _failure_result(sent_at, str(err), [])
        attachments = self._attachments.get_many(request.attachment_ids)
        if len(attachments) != len(request.attachment_ids):
            return _failure_result(
                sent_at, "One or more managed attachment IDs do not exist", []
            )
        try:
            message, attachment_names = await self._async_build_message(
                request, attachments
            )
        except (OSError, ValueError) as err:
            _LOGGER.warning(
                "Unable to prepare SMTP message",
                extra={
                    "error_type": type(err).__name__,
                    "attachment_count": len(attachments),
                },
            )
            return _failure_result(sent_at, str(err), [])

        envelope_recipients = _unique_addresses(
            request.recipients,
            request.cc or [],
            request.bcc or [],
        )
        context = {
            "smtp_host": self._config.host,
            "smtp_port": self._config.port,
            "recipient_count": len(envelope_recipients),
            "attachment_count": len(attachment_names),
        }

        for attempt in range(1, self._max_attempts + 1):
            try:
                async with asyncio.timeout(self._timeout):
                    refused, _ = await aiosmtplib.send(
                        message,
                        sender=self._config.sender_email,
                        recipients=envelope_recipients,
                        hostname=self._config.host,
                        port=self._config.port,
                        username=self._config.username,
                        password=self._config.password,
                        start_tls=self._config.use_tls,
                        timeout=self._timeout,
                    )
                if refused:
                    _LOGGER.warning(
                        "SMTP server refused one or more recipients",
                        extra={**context, "refused_count": len(refused)},
                    )
                    return _failure_result(
                        sent_at,
                        "SMTP server refused one or more recipients",
                        attachment_names,
                    )
            except SMTPAuthenticationError:
                _LOGGER.warning("SMTP authentication failed", extra=context)
                return _failure_result(
                    sent_at,
                    "SMTP authentication failed; verify the username and password",
                    attachment_names,
                )
            except SMTPResponseException as err:
                if _is_transient_response(err) and attempt < self._max_attempts:
                    await self._async_retry_delay(attempt, context, err.code)
                    continue
                _LOGGER.warning(
                    "SMTP server rejected the message",
                    extra={**context, "smtp_code": err.code, "attempt": attempt},
                )
                return _failure_result(
                    sent_at,
                    f"SMTP server rejected the message (status {err.code})",
                    attachment_names,
                )
            except (SMTPTimeoutError, TimeoutError):
                if attempt < self._max_attempts:
                    await self._async_retry_delay(attempt, context)
                    continue
                _LOGGER.warning(
                    "SMTP delivery timed out",
                    extra={**context, "attempt": attempt},
                )
                return _failure_result(
                    sent_at, "SMTP delivery timed out", attachment_names
                )
            except (SMTPConnectError, SMTPServerDisconnected, OSError) as err:
                if attempt < self._max_attempts:
                    await self._async_retry_delay(attempt, context)
                    continue
                _LOGGER.warning(
                    "SMTP connection failed",
                    extra={
                        **context,
                        "attempt": attempt,
                        "error_type": type(err).__name__,
                    },
                )
                return _failure_result(
                    sent_at, "Unable to connect to the SMTP server", attachment_names
                )
            except SMTPException as err:
                _LOGGER.warning(
                    "SMTP delivery failed",
                    extra={**context, "error_type": type(err).__name__},
                )
                return _failure_result(
                    sent_at, "SMTP delivery failed", attachment_names
                )
            else:
                message_id = str(message["Message-ID"])
                _LOGGER.info(
                    "SMTP message accepted for delivery",
                    extra={**context, "message_id": message_id},
                )
                return SendResult(
                    success=True,
                    message_id=message_id,
                    error=None,
                    sent_at=sent_at,
                    attachment_names=attachment_names,
                )

        raise RuntimeError("Unreachable SMTP retry state")

    async def _async_build_message(
        self, request: MessageRequest, attachments: Sequence[Attachment]
    ) -> tuple[EmailMessage, list[str]]:
        """Create multipart content and prepare every managed attachment."""
        message = EmailMessage()
        message["Subject"] = request.subject
        message["From"] = formataddr(
            (self._config.sender_name, self._config.sender_email)
        )
        if request.recipients:
            message["To"] = ", ".join(request.recipients)
        if request.cc:
            message["Cc"] = ", ".join(request.cc)
        message["Date"] = format_datetime(datetime.now(UTC))
        message["Message-ID"] = make_msgid()
        message.set_content(request.text or _html_to_text(request.html) or " ")
        if request.html:
            message.add_alternative(request.html, subtype="html")

        processed_names: list[str] = []
        for attachment in attachments:
            prepared = await self._images.async_prepare(attachment)
            try:
                main_type, sub_type = prepared.content_type.split("/", maxsplit=1)
            except ValueError as err:
                raise ValueError(
                    f"Invalid MIME type for attachment '{prepared.name}'"
                ) from err
            message.add_attachment(
                prepared.content,
                maintype=main_type,
                subtype=sub_type,
                filename=prepared.name,
            )
            processed_names.append(prepared.name)
        return message, processed_names

    async def _async_retry_delay(
        self,
        attempt: int,
        context: dict[str, object],
        smtp_code: int | None = None,
    ) -> None:
        """Log and wait before one bounded transient-failure retry."""
        _LOGGER.warning(
            "Transient SMTP failure; retrying",
            extra={**context, "attempt": attempt, "smtp_code": smtp_code},
        )
        if self._retry_delay:
            await asyncio.sleep(self._retry_delay)


def _is_transient_response(error: SMTPResponseException) -> bool:
    """Return whether an SMTP response is in the transient 4xx class."""
    code = int(error.code)
    return 400 <= code < 500


def _validate_request(request: MessageRequest, sender_email: str) -> None:
    """Validate all headers and envelope addresses before MIME construction."""
    if not request.subject.strip():
        raise ValueError("Subject is required")
    if "\r" in request.subject or "\n" in request.subject:
        raise ValueError("Subject must not contain line breaks")
    if not request.text and not request.html:
        raise ValueError("Plain text or HTML content is required")

    address_groups = (
        [sender_email],
        request.recipients,
        request.cc or [],
        request.bcc or [],
    )
    if not any(address_groups[1:]):
        raise ValueError("At least one To, CC, or BCC recipient is required")
    for address in (item for group in address_groups for item in group):
        if not _EMAIL_PATTERN.fullmatch(address):
            raise ValueError(f"Invalid email address: {address}")


def _unique_addresses(*groups: Sequence[str]) -> list[str]:
    """Deduplicate envelope recipients case-insensitively, preserving order."""
    result: list[str] = []
    seen: set[str] = set()
    for address in (item for group in groups for item in group):
        key = address.casefold()
        if key not in seen:
            seen.add(key)
            result.append(address)
    return result


def _failure_result(
    sent_at: datetime, error: str, attachment_names: list[str]
) -> SendResult:
    """Build a consistent failure result."""
    return SendResult(
        success=False,
        message_id=None,
        error=error,
        sent_at=sent_at,
        attachment_names=attachment_names,
    )


def _html_to_text(html: str) -> str:
    """Give HTML-only messages a minimal standards-compliant text fallback."""
    return html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
