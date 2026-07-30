"""Constants for the Document Sender integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "document_sender"
PLATFORMS: Final = ["button"]

CONF_SMTP_HOST: Final = "smtp_host"
CONF_SMTP_PORT: Final = "smtp_port"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SENDER: Final = "sender"  # Legacy v1 config-entry key.
CONF_SENDER_EMAIL: Final = "sender_email"
CONF_SENDER_NAME: Final = "sender_name"
CONF_RECIPIENTS: Final = "recipients"
CONF_USE_TLS: Final = "use_tls"
CONF_MAX_IMAGE_DIMENSION: Final = "max_image_dimension"
CONF_IMAGE_QUALITY: Final = "image_quality"
CONF_MAX_ATTACHMENT_SIZE_MB: Final = "max_attachment_size_mb"
CONF_NOTIFY_MOBILE: Final = "notify_mobile"
CONF_NOTIFY_PERSISTENT: Final = "notify_persistent"

DEFAULT_SMTP_PORT: Final = 587
DEFAULT_MAX_IMAGE_DIMENSION: Final = 1600
DEFAULT_IMAGE_QUALITY: Final = 85
DEFAULT_MAX_ATTACHMENT_SIZE_MB: Final = 25
DEFAULT_RECIPIENTS: Final[list[str]] = []
DEFAULT_NOTIFY_MOBILE: Final = True
DEFAULT_NOTIFY_PERSISTENT: Final = True

STORAGE_VERSION: Final = 1
STORAGE_KEY_ATTACHMENTS: Final = f"{DOMAIN}.attachments"
STORAGE_KEY_TEMPLATES: Final = f"{DOMAIN}.templates"
STORAGE_KEY_SCHEDULES: Final = f"{DOMAIN}.schedules"
STORAGE_KEY_PANEL_DRAFTS: Final = f"{DOMAIN}.panel_drafts"
ATTACHMENTS_DIRECTORY: Final = DOMAIN
DATABASE_FILE: Final = f"{DOMAIN}.sqlite"
PANEL_URL_PATH: Final = DOMAIN.replace("_", "-")
PANEL_COMPONENT: Final = "document-sender-panel"
PANEL_STATIC_URL: Final = f"/{DOMAIN}/document-sender-panel.js"
PANEL_MAX_UPLOAD_BYTES: Final = 25 * 1024 * 1024

ATTR_ENTRY_ID: Final = "entry_id"
ATTR_TEMPLATE_ID: Final = "template_id"
ATTR_SCHEDULE_ID: Final = "schedule_id"
ATTR_ATTACHMENT_ID: Final = "attachment_id"

SIGNAL_SCHEDULES_CHANGED: Final = f"{DOMAIN}_schedules_changed"

SCHEDULE_DAILY: Final = "daily"
SCHEDULE_WEEKLY: Final = "weekly"
SCHEDULE_MONTHLY: Final = "monthly"
SCHEDULE_ONCE: Final = "once"
SCHEDULE_TYPES: Final = {
    SCHEDULE_DAILY,
    SCHEDULE_WEEKLY,
    SCHEDULE_MONTHLY,
    SCHEDULE_ONCE,
}
