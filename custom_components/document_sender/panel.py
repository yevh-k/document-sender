"""Native sidebar panel and secure WebSocket API for Document Sender."""

from __future__ import annotations

import base64
import binascii
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import voluptuous as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import (
    CONF_MAX_ATTACHMENT_SIZE_MB,
    CONF_SENDER_EMAIL,
    CONF_SENDER_NAME,
    DOMAIN,
    PANEL_COMPONENT,
    PANEL_MAX_UPLOAD_BYTES,
    PANEL_STATIC_ROOT,
    PANEL_STATIC_URL,
    PANEL_URL_PATH,
    STORAGE_KEY_PANEL_DRAFTS,
    STORAGE_VERSION,
)
from .coordinator import DocumentSenderCoordinator
from .models import ScheduleData

_LOGGER = logging.getLogger(__name__)
_PANEL_REGISTERED = f"{DOMAIN}_panel_registered"
_PANEL_API_REGISTERED = f"{DOMAIN}_panel_api_registered"
_PANEL_STATIC_REGISTERED = f"{DOMAIN}_panel_static_registered"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register static module and WebSocket commands once per Home Assistant."""
    if not hass.data.get(_PANEL_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_STATIC_ROOT,
                    str(Path(__file__).parent / "frontend"),
                    False,
                )
            ]
        )
        hass.data[_PANEL_STATIC_REGISTERED] = True
    if hass.data.get(_PANEL_API_REGISTERED):
        return
    for command in _COMMANDS:
        websocket_api.async_register_command(hass, command)
    hass.data[_PANEL_API_REGISTERED] = True


@callback
def async_register_panel(hass: HomeAssistant) -> None:
    """Show the panel once the first config entry has loaded."""
    if hass.data.get(_PANEL_REGISTERED):
        return
    # Built-in panel registration exposes the route; custom integration modules
    # must also be added to the frontend module registry so the browser defines
    # the ``document-sender-panel`` custom element.
    frontend.add_extra_js_url(hass, PANEL_STATIC_URL)
    frontend.async_register_built_in_panel(
        hass,
        PANEL_COMPONENT,
        sidebar_title="Document Sender",
        sidebar_icon="mdi:file-send-outline",
        frontend_url_path=PANEL_URL_PATH,
        require_admin=True,
    )
    hass.data[_PANEL_REGISTERED] = True


@callback
def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar item after the last entry unloads."""
    if not hass.data.pop(_PANEL_REGISTERED, False):
        return
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
    frontend.remove_extra_js_url(hass, PANEL_STATIC_URL)


def _coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> DocumentSenderCoordinator:
    """Resolve one loaded entry without ever exposing config-entry data."""
    candidates: list[DocumentSenderCoordinator] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry_id and entry.entry_id != entry_id:
            continue
        runtime_data = getattr(entry, "runtime_data", None)
        if isinstance(runtime_data, DocumentSenderCoordinator):
            candidates.append(runtime_data)
    if len(candidates) != 1:
        raise HomeAssistantError(
            "Select a Document Sender account" if candidates else "No loaded account"
        )
    return candidates[0]


def _entries(hass: HomeAssistant) -> list[dict[str, str]]:
    """Return public, non-secret sender metadata for the account picker."""
    entries: list[dict[str, str]] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if not isinstance(coordinator, DocumentSenderCoordinator):
            continue
        entries.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "sender_name": str(coordinator.config.get(CONF_SENDER_NAME, "")),
                "sender_email": str(coordinator.config.get(CONF_SENDER_EMAIL, "")),
            }
        )
    return entries


def _draft_store(hass: HomeAssistant) -> Store[dict[str, dict[str, object]]]:
    """Return the integration-private per-entry panel draft store."""
    return Store(hass, STORAGE_VERSION, STORAGE_KEY_PANEL_DRAFTS)


def _mask_addresses(values: object) -> list[str]:
    """Mask recipient addresses before sending delivery history to a browser."""
    if not isinstance(values, list):
        return []
    masked: list[str] = []
    for value in values:
        address = str(value)
        local, separator, domain = address.partition("@")
        masked.append(f"{local[:1]}***@{domain}" if separator else "***")
    return masked


async def _attachment_response(
    coordinator: DocumentSenderCoordinator,
) -> list[dict[str, object]]:
    """Return managed attachment metadata including a filesystem-derived size."""
    result: list[dict[str, object]] = []
    for item in coordinator.attachments.list_metadata():
        path = Path(item["path"])
        try:
            size = await coordinator.hass.async_add_executor_job(path.stat)
            byte_size = size.st_size
        except OSError:
            byte_size = 0
        result.append(
            {
                "id": item["id"],
                "name": item["name"],
                "content_type": item["content_type"],
                "created_at": item["created_at"],
                "size": byte_size,
                "preview": item["content_type"].startswith("image/"),
            }
        )
    return result


def _decode_upload(name: str, content_type: str, encoded: str, limit: int) -> bytes:
    """Validate and decode a bounded browser upload without accepting paths."""
    if Path(name).name != name or not name or "\x00" in name:
        raise HomeAssistantError("Invalid upload filename")
    if not content_type or "/" not in content_type:
        raise HomeAssistantError("Invalid upload MIME type")
    if len(encoded) > ((limit + 2) // 3) * 4 + 4:
        raise HomeAssistantError("Upload exceeds the configured size limit")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as err:
        raise HomeAssistantError("Upload content is invalid") from err
    if not payload or len(payload) > limit:
        raise HomeAssistantError("Upload exceeds the configured size limit")
    return payload


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/config"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_config(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return public panel configuration only."""
    connection.send_result(msg["id"], {"entries": _entries(hass)})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/template/get", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def ws_template_get(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Get the saved panel draft for one entry."""
    _coordinator(hass, msg["entry_id"])
    data = await _draft_store(hass).async_load() or {}
    connection.send_result(msg["id"], data.get(msg["entry_id"], {}))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/template/save",
        vol.Required("entry_id"): str,
        vol.Required("template"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_template_save(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Save non-secret editor defaults per config entry."""
    _coordinator(hass, msg["entry_id"])
    raw = cast(Mapping[str, object], msg["template"])
    template = {
        key: (
            raw.get(key, []) if key in {"recipients", "cc", "bcc"} else raw.get(key, "")
        )
        for key in ("recipients", "cc", "bcc", "subject", "text", "html")
    }
    if not all(
        isinstance(value, list)
        for key, value in template.items()
        if key in {"recipients", "cc", "bcc"}
    ):
        connection.send_error(msg["id"], "invalid_template", "Recipients must be lists")
        return
    store = _draft_store(hass)
    data = await store.async_load() or {}
    data[msg["entry_id"]] = template
    await store.async_save(data)
    connection.send_result(msg["id"], template)


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/templates/list", vol.Required("entry_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_templates_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List reusable message templates for one SMTP account."""
    coordinator = _coordinator(hass, msg["entry_id"])
    connection.send_result(
        msg["id"], [dict(template) for template in coordinator.templates.list()]
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/templates/save",
        vol.Required("entry_id"): str,
        vol.Required("template"): {
            vol.Optional("id"): str,
            vol.Required("name"): str,
            vol.Required("recipients"): [vol.Email()],
            vol.Optional("cc", default=[]): [vol.Email()],
            vol.Optional("bcc", default=[]): [vol.Email()],
            vol.Required("subject"): str,
            vol.Optional("text", default=""): str,
            vol.Optional("html", default=""): str,
            vol.Optional("attachment_ids", default=[]): [str],
        },
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_templates_save(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create or update a reusable message template."""
    coordinator = _coordinator(hass, msg["entry_id"])
    raw = cast(Mapping[str, Any], msg["template"])
    if not raw["name"].strip() or not raw["subject"].strip():
        connection.send_error(
            msg["id"], "invalid_template", "Template name and subject are required"
        )
        return
    if not raw["text"].strip() and not raw["html"].strip():
        connection.send_error(
            msg["id"],
            "invalid_template",
            "A plain-text or HTML message body is required",
        )
        return
    if not raw["recipients"] and not raw["cc"] and not raw["bcc"]:
        connection.send_error(
            msg["id"], "invalid_template", "At least one recipient is required"
        )
        return
    attachment_ids = list(raw["attachment_ids"])
    missing = [
        identifier
        for identifier in attachment_ids
        if coordinator.attachments.get(identifier) is None
    ]
    if missing:
        connection.send_error(
            msg["id"],
            "invalid_template",
            f"Unknown attachment IDs: {', '.join(missing)}",
        )
        return
    template = await coordinator.templates.async_save(
        raw["name"].strip(),
        raw["subject"],
        raw["text"],
        raw["html"],
        raw.get("id"),
        recipients=list(raw["recipients"]),
        cc=list(raw["cc"]),
        bcc=list(raw["bcc"]),
        attachment_ids=attachment_ids,
    )
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], dict(template))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/templates/delete",
        vol.Required("entry_id"): str,
        vol.Required("template_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_templates_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a template unless a monthly automation still uses it."""
    coordinator = _coordinator(hass, msg["entry_id"])
    if any(
        schedule.get("template_id") == msg["template_id"]
        for schedule in coordinator.scheduler.list()
    ):
        connection.send_error(
            msg["id"],
            "template_in_use",
            "Delete automations that use this template first",
        )
        return
    if not await coordinator.templates.async_remove(msg["template_id"]):
        connection.send_error(msg["id"], "not_found", "Unknown template")
        return
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/automations/list", vol.Required("entry_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_automations_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List monthly Document Sender automations."""
    coordinator = _coordinator(hass, msg["entry_id"])
    result: list[dict[str, object]] = []
    for schedule in coordinator.scheduler.list():
        if schedule.get("schedule_type") != "monthly":
            continue
        item: dict[str, object] = dict(schedule)
        item["next_run"] = coordinator.scheduler.next_run(schedule)
        result.append(item)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/automations/save",
        vol.Required("entry_id"): str,
        vol.Required("automation"): {
            vol.Optional("id"): str,
            vol.Required("name"): str,
            vol.Required("template_id"): str,
            vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
            vol.Required("time"): vol.Match(
                r"^(?:[01]\d|2[0-3]):[0-5]\d(?:\:[0-5]\d)?$"
            ),
            vol.Optional("enabled", default=True): bool,
        },
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_automations_save(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create or update a monthly automation."""
    coordinator = _coordinator(hass, msg["entry_id"])
    raw = cast(Mapping[str, Any], msg["automation"])
    if not raw["name"].strip():
        connection.send_error(
            msg["id"], "invalid_automation", "Automation name is required"
        )
        return
    if coordinator.templates.get(raw["template_id"]) is None:
        connection.send_error(msg["id"], "not_found", "Unknown template")
        return
    schedule: ScheduleData = {
        "name": raw["name"].strip(),
        "schedule_type": "monthly",
        "template_id": raw["template_id"],
        "day": raw["day"],
        "time": raw["time"],
        "enabled": raw["enabled"],
    }
    if raw.get("id"):
        schedule["id"] = raw["id"]
    try:
        saved = await coordinator.scheduler.async_save(schedule)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_automation", str(err))
        return
    await coordinator.async_refresh_state()
    result: dict[str, object] = dict(saved)
    result["next_run"] = coordinator.scheduler.next_run(saved)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/automations/delete",
        vol.Required("entry_id"): str,
        vol.Required("automation_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_automations_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a monthly automation."""
    coordinator = _coordinator(hass, msg["entry_id"])
    if not await coordinator.scheduler.async_remove(msg["automation_id"]):
        connection.send_error(msg["id"], "not_found", "Unknown automation")
        return
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/automations/run",
        vol.Required("entry_id"): str,
        vol.Required("automation_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_automations_run(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Run a monthly automation immediately."""
    coordinator = _coordinator(hass, msg["entry_id"])
    try:
        schedule = await coordinator.scheduler.async_run_now(msg["automation_id"])
    except ValueError as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return
    await coordinator.async_refresh_state()
    result: dict[str, object] = dict(schedule)
    result["next_run"] = coordinator.scheduler.next_run(schedule)
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/attachments/list", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def ws_attachments_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List private managed attachments."""
    connection.send_result(
        msg["id"], await _attachment_response(_coordinator(hass, msg["entry_id"]))
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/attachments/upload",
        vol.Required("entry_id"): str,
        vol.Required("name"): str,
        vol.Required("content_type"): str,
        vol.Required("content"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_attachments_upload(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Import a bounded browser upload into managed attachment storage."""
    coordinator = _coordinator(hass, msg["entry_id"])
    limit = min(
        PANEL_MAX_UPLOAD_BYTES,
        int(coordinator.config[CONF_MAX_ATTACHMENT_SIZE_MB]) * 1024 * 1024,
    )
    try:
        payload = _decode_upload(
            msg["name"], msg["content_type"], msg["content"], limit
        )
        item = await coordinator.attachments.async_add_bytes(
            msg["name"], msg["content_type"], payload
        )
    except (HomeAssistantError, ValueError) as err:
        connection.send_error(msg["id"], "invalid_upload", str(err))
        return
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], {"attachment": item})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/attachments/delete",
        vol.Required("entry_id"): str,
        vol.Required("attachment_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_attachments_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete one managed attachment."""
    coordinator = _coordinator(hass, msg["entry_id"])
    if not await coordinator.attachments.async_remove(msg["attachment_id"]):
        connection.send_error(msg["id"], "not_found", "Unknown attachment")
        return
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/camera/list"})
@websocket_api.async_response
async def ws_camera_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List camera entities without exposing camera data."""
    connection.send_result(
        msg["id"],
        [
            {"entity_id": state.entity_id, "name": state.name}
            for state in hass.states.async_all("camera")
        ],
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/camera/snapshot",
        vol.Required("entry_id"): str,
        vol.Required("entity_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_camera_snapshot(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Capture a camera image to managed private storage, then remove the temp file."""
    coordinator = _coordinator(hass, msg["entry_id"])
    entity_id = msg["entity_id"]
    if not entity_id.startswith("camera.") or hass.states.get(entity_id) is None:
        connection.send_error(msg["id"], "invalid_camera", "Unknown camera entity")
        return
    snapshots = Path(hass.config.path(".storage", DOMAIN, "snapshots"))
    temporary = snapshots / f"{msg['entry_id']}_{entity_id.replace('.', '_')}.jpg"
    try:
        await hass.async_add_executor_job(snapshots.mkdir, 0o700, True, True)
        await hass.services.async_call(
            "camera",
            "snapshot",
            {"entity_id": entity_id, "filename": str(temporary)},
            blocking=True,
        )
        content = await hass.async_add_executor_job(temporary.read_bytes)
        item = await coordinator.attachments.async_add_bytes(
            f"{entity_id.replace('.', '_')}.jpg", "image/jpeg", content
        )
    except (HomeAssistantError, OSError, ValueError) as err:
        _LOGGER.warning(
            "Camera snapshot import failed", extra={"error_type": type(err).__name__}
        )
        connection.send_error(
            msg["id"], "snapshot_failed", "Camera snapshot could not be imported"
        )
        return
    finally:
        await hass.async_add_executor_job(temporary.unlink, True)
    await coordinator.async_refresh_state()
    connection.send_result(msg["id"], {"attachment": item})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/history/list",
        vol.Required("entry_id"): str,
        vol.Optional("limit", default=50): vol.All(int, vol.Range(min=1, max=100)),
    }
)
@websocket_api.async_response
async def ws_history_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return a privacy-preserving delivery history."""
    rows = await _coordinator(hass, msg["entry_id"]).database.async_recent(msg["limit"])
    history = []
    for row in rows:
        history.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "subject": row["subject"],
                "success": bool(row["success"]),
                "attachment_count": len(
                    cast(list[object], __import__("json").loads(row["attachment_ids"]))
                ),
                "error": (row["error"] or "")[:200],
                "recipients": _mask_addresses(
                    __import__("json").loads(row["recipients"])
                ),
            }
        )
    connection.send_result(msg["id"], history)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/send",
        vol.Required("entry_id"): str,
        vol.Required("message"): dict,
    }
)
@websocket_api.async_response
async def ws_send(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send a panel-composed message through the existing coordinator."""
    coordinator = _coordinator(hass, msg["entry_id"])
    message = cast(Mapping[str, Any], msg["message"])
    try:
        result = await coordinator.async_send(
            subject=message.get("subject"),
            text=message.get("text"),
            html=message.get("html"),
            recipients=message.get("recipients"),
            cc=message.get("cc"),
            bcc=message.get("bcc"),
            attachment_ids=message.get("attachments"),
            source="panel",
        )
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "send_failed", str(err))
        return
    connection.send_result(
        msg["id"],
        {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/resend", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def ws_resend(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Resend the most recent successful delivery for one entry."""
    try:
        result = await _coordinator(hass, msg["entry_id"]).async_resend_last()
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "resend_failed", str(err))
        return
    connection.send_result(
        msg["id"],
        {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error,
        },
    )


_COMMANDS = (
    ws_config,
    ws_template_get,
    ws_template_save,
    ws_templates_list,
    ws_templates_save,
    ws_templates_delete,
    ws_automations_list,
    ws_automations_save,
    ws_automations_delete,
    ws_automations_run,
    ws_attachments_list,
    ws_attachments_upload,
    ws_attachments_delete,
    ws_camera_list,
    ws_camera_snapshot,
    ws_history_list,
    ws_send,
    ws_resend,
)
