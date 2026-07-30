"""Coordinator that owns Document Sender's runtime services."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .attachments import AttachmentManager
from .const import (
    CONF_IMAGE_QUALITY,
    CONF_MAX_ATTACHMENT_SIZE_MB,
    CONF_MAX_IMAGE_DIMENSION,
    CONF_NOTIFY_MOBILE,
    CONF_NOTIFY_PERSISTENT,
    CONF_RECIPIENTS,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_MAX_ATTACHMENT_SIZE_MB,
    DEFAULT_MAX_IMAGE_DIMENSION,
    DEFAULT_NOTIFY_MOBILE,
    DEFAULT_NOTIFY_PERSISTENT,
    DOMAIN,
)
from .database import DeliveryDatabase
from .image import ImageProcessor
from .mailer import MailConfig, Mailer
from .models import MessageRequest, ScheduleData, SendResult
from .scheduler import SchedulerManager
from .templates import TemplateManager
from .variables import monthly_variables

_LOGGER = logging.getLogger(__name__)


class DocumentSenderCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate storage, delivery, controls and scheduler jobs for one entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[Any]) -> None:
        """Construct runtime managers."""
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{entry.entry_id}")
        self.entry = entry
        self.config: dict[str, Any] = {
            CONF_MAX_IMAGE_DIMENSION: DEFAULT_MAX_IMAGE_DIMENSION,
            CONF_IMAGE_QUALITY: DEFAULT_IMAGE_QUALITY,
            CONF_MAX_ATTACHMENT_SIZE_MB: DEFAULT_MAX_ATTACHMENT_SIZE_MB,
            CONF_NOTIFY_MOBILE: DEFAULT_NOTIFY_MOBILE,
            CONF_NOTIFY_PERSISTENT: DEFAULT_NOTIFY_PERSISTENT,
            **entry.data,
            **entry.options,
        }
        self.attachments = AttachmentManager(hass, entry.entry_id)
        self.templates = TemplateManager(hass, entry.entry_id)
        self.database = DeliveryDatabase(hass, entry.entry_id)
        self.images = ImageProcessor(
            hass,
            self.config[CONF_MAX_IMAGE_DIMENSION],
            self.config[CONF_IMAGE_QUALITY],
            self.config[CONF_MAX_ATTACHMENT_SIZE_MB],
        )
        self.mailer = Mailer(
            MailConfig.from_mapping(self.config), self.attachments, self.images
        )
        self.scheduler = SchedulerManager(
            hass, entry.entry_id, self._async_send_scheduled
        )
        self._last_result: SendResult | None = None

    async def async_setup(self) -> None:
        """Initialize all persistent managers."""
        await self.database.async_initialize()
        await self.attachments.async_load()
        await self.templates.async_load()
        await self.scheduler.async_load()
        self.async_set_updated_data(await self._async_update_data())

    async def async_close(self) -> None:
        """Release scheduled callbacks."""
        await self.scheduler.async_close()

    async def async_refresh_state(self) -> None:
        """Publish updated manager counts to entities and diagnostics."""
        self.async_set_updated_data(await self._async_update_data())

    async def _async_update_data(self) -> dict[str, object]:
        """Build state consumed by button entities and diagnostics."""
        return {
            "attachments": len(self.attachments.list_metadata()),
            "templates": len(self.templates.list()),
            "schedules": len(self.scheduler.list()),
            "last_success": self._last_result.success if self._last_result else None,
            "last_sent_at": (
                self._last_result.sent_at.isoformat() if self._last_result else None
            ),
        }

    async def async_send(
        self,
        *,
        subject: str | None = None,
        text: str | None = None,
        html: str | None = None,
        recipients: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachment_ids: list[str] | None = None,
        template_id: str | None = None,
        source: str = "manual",
        schedule_id: str | None = None,
    ) -> SendResult:
        """Resolve a request and send it via SMTP."""
        request = self._build_request(
            subject=subject,
            text=text,
            html=html,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            attachment_ids=attachment_ids,
            template_id=template_id,
            source=source,
            schedule_id=schedule_id,
        )
        result = await self.mailer.async_send(request)
        self._last_result = result
        await self.database.async_log(request, result)
        await self._async_notify(request, result)
        self.async_set_updated_data(await self._async_update_data())
        return result

    async def async_test_send(self, recipients: list[str] | None = None) -> SendResult:
        """Send a small verification email without attachments."""
        return await self.async_send(
            subject="Document Sender test message",
            text="Your Document Sender SMTP configuration is working.",
            html=(
                "<p>Your <strong>Document Sender</strong> SMTP configuration is "
                "working.</p>"
            ),
            recipients=recipients,
            source="test",
        )

    async def async_resend_last(self) -> SendResult:
        """Resend the last successful delivery exactly as recorded."""
        last = await self.database.async_last_successful()
        if last is None:
            raise HomeAssistantError(
                "No successful Document Sender delivery exists yet"
            )
        return await self.async_send(
            subject=last["subject"],
            text=last["text_body"],
            html=last["html_body"],
            recipients=last["recipients"],
            cc=last["cc"],
            bcc=last["bcc"],
            attachment_ids=last["attachment_ids"],
            template_id=last["template_id"],
            source="resend",
            schedule_id=last["schedule_id"],
        )

    async def _async_send_scheduled(self, schedule: ScheduleData) -> None:
        """Create and send a scheduled message."""
        uses_template = bool(schedule.get("template_id"))
        result = await self.async_send(
            subject=None if uses_template else schedule.get("subject"),
            text=None if uses_template else schedule.get("text"),
            html=None if uses_template else schedule.get("html"),
            recipients=None if uses_template else schedule.get("recipients"),
            cc=None if uses_template else schedule.get("cc"),
            bcc=None if uses_template else schedule.get("bcc"),
            attachment_ids=None if uses_template else schedule.get("attachment_ids"),
            template_id=schedule.get("template_id"),
            source="schedule",
            schedule_id=schedule["id"],
        )
        if not result.success:
            raise HomeAssistantError(result.error or "Scheduled delivery failed")

    def _build_request(
        self,
        *,
        subject: str | None,
        text: str | None,
        html: str | None,
        recipients: list[str] | None,
        cc: list[str] | None,
        bcc: list[str] | None,
        attachment_ids: list[str] | None,
        template_id: str | None,
        source: str,
        schedule_id: str | None,
    ) -> MessageRequest:
        """Merge request overrides with an optional saved template."""
        template = self.templates.get(template_id) if template_id else None
        if template_id and template is None:
            raise HomeAssistantError(f"Unknown template ID: {template_id}")
        if recipients is not None:
            final_recipients = recipients
        elif template is not None:
            final_recipients = list(template["recipients"])
        else:
            final_recipients = list(self.config[CONF_RECIPIENTS])
        final_cc = (
            cc
            if cc is not None
            else (list(template["cc"]) if template is not None else [])
        )
        final_bcc = (
            bcc
            if bcc is not None
            else (list(template["bcc"]) if template is not None else [])
        )
        if not final_recipients and not final_cc and not final_bcc:
            raise HomeAssistantError(
                "At least one To, CC, or BCC recipient is required"
            )
        final_subject = (
            subject
            if subject is not None
            else (template["subject"] if template else "")
        )
        final_text = (
            text if text is not None else (template["text"] if template else "")
        )
        final_html = (
            html if html is not None else (template["html"] if template else "")
        )
        if not final_subject:
            raise HomeAssistantError("A message subject is required")
        if not final_text and not final_html:
            raise HomeAssistantError("A plain-text or HTML message body is required")
        final_attachment_ids = (
            attachment_ids
            if attachment_ids is not None
            else (list(template["attachment_ids"]) if template is not None else [])
        )
        missing_attachment_ids = [
            attachment_id
            for attachment_id in final_attachment_ids
            if self.attachments.get(attachment_id) is None
        ]
        if missing_attachment_ids:
            raise HomeAssistantError(
                f"Unknown attachment IDs: {', '.join(missing_attachment_ids)}"
            )
        local_now = dt_util.now()
        variables: dict[str, object] = {
            **monthly_variables(self.hass.config.language, local_now),
            "now": local_now,
            "recipients": final_recipients,
            "source": source,
        }
        return MessageRequest(
            recipients=final_recipients,
            subject=self._render(final_subject, variables),
            text=self._render(final_text, variables),
            html=self._render(final_html, variables),
            attachment_ids=final_attachment_ids,
            source=source,
            cc=final_cc,
            bcc=final_bcc,
            schedule_id=schedule_id,
            template_id=template_id,
        )

    def _render(self, source: str, variables: dict[str, object]) -> str:
        """Render a Home Assistant template at the moment of delivery."""
        return cast(
            str,
            Template(source, self.hass).async_render(variables, parse_result=False),
        )

    async def _async_notify(self, request: MessageRequest, result: SendResult) -> None:
        """Publish delivery outcomes via persistent and mobile app notifications."""
        status = "sent" if result.success else "failed"
        title = f"Document Sender: message {status}"
        message = (
            f"{request.subject} → {', '.join(request.recipients)}"
            if result.success
            else f"{request.subject}: {result.error}"
        )
        notification_id = f"{DOMAIN}_{self.entry.entry_id}_{status}"
        if self.config.get(CONF_NOTIFY_PERSISTENT, True):
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=notification_id
            )
        if self.config.get(CONF_NOTIFY_MOBILE, True):
            for service in self.hass.services.async_services().get("notify", {}):
                if service.startswith("mobile_app_"):
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "notify",
                            service,
                            {"title": title, "message": message},
                            blocking=False,
                        )
                    )
