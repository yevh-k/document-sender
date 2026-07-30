"""Home Assistant services for Document Sender."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_ATTACHMENT_ID,
    ATTR_ENTRY_ID,
    ATTR_SCHEDULE_ID,
    ATTR_TEMPLATE_ID,
    DOMAIN,
    SCHEDULE_MONTHLY,
    SCHEDULE_ONCE,
    SCHEDULE_WEEKLY,
)
from .coordinator import DocumentSenderCoordinator
from .models import ScheduleData

SERVICE_SEND = "send"
SERVICE_TEST_SEND = "test_send"
SERVICE_RESEND_LAST = "resend_last"
SERVICE_ADD_ATTACHMENT = "add_attachment"
SERVICE_REMOVE_ATTACHMENT = "remove_attachment"
SERVICE_LIST_ATTACHMENTS = "list_attachments"
SERVICE_SAVE_TEMPLATE = "save_template"
SERVICE_REMOVE_TEMPLATE = "remove_template"
SERVICE_LIST_TEMPLATES = "list_templates"
SERVICE_SAVE_SCHEDULE = "save_schedule"
SERVICE_REMOVE_SCHEDULE = "remove_schedule"
SERVICE_LIST_SCHEDULES = "list_schedules"

ENTRY_SCHEMA = {vol.Optional(ATTR_ENTRY_ID): cv.string}
MESSAGE_SCHEMA = vol.Schema(
    {
        **ENTRY_SCHEMA,
        vol.Optional("subject"): cv.string,
        vol.Optional("text"): cv.string,
        vol.Optional("html"): cv.string,
        vol.Optional("recipients"): vol.All(cv.ensure_list, [vol.Email()]),
        vol.Optional("cc"): vol.All(cv.ensure_list, [vol.Email()]),
        vol.Optional("bcc"): vol.All(cv.ensure_list, [vol.Email()]),
        vol.Optional("attachments"): vol.All(cv.ensure_list, [cv.string]),
        # Kept for backward compatibility with releases before 1.1.0.
        vol.Optional("attachment_ids"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_TEMPLATE_ID): cv.string,
    }
)

_REGISTERED_SERVICES = (
    SERVICE_SEND,
    SERVICE_TEST_SEND,
    SERVICE_RESEND_LAST,
    SERVICE_ADD_ATTACHMENT,
    SERVICE_REMOVE_ATTACHMENT,
    SERVICE_LIST_ATTACHMENTS,
    SERVICE_SAVE_TEMPLATE,
    SERVICE_REMOVE_TEMPLATE,
    SERVICE_LIST_TEMPLATES,
    SERVICE_SAVE_SCHEDULE,
    SERVICE_REMOVE_SCHEDULE,
    SERVICE_LIST_SCHEDULES,
)
_SERVICES_REGISTERED = f"{DOMAIN}_services_registered"


async def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services once for all configured entries."""
    if hass.data.get(_SERVICES_REGISTERED):
        return
    hass.data[_SERVICES_REGISTERED] = True

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND,
        _async_send,
        schema=MESSAGE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_SEND,
        _async_test_send,
        schema=vol.Schema(
            {
                **ENTRY_SCHEMA,
                vol.Optional("recipients"): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESEND_LAST,
        _async_resend_last,
        schema=vol.Schema(ENTRY_SCHEMA),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ATTACHMENT,
        _async_add_attachment,
        schema=vol.Schema(
            {
                **ENTRY_SCHEMA,
                vol.Required("path"): cv.string,
                vol.Optional("name"): cv.string,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_ATTACHMENT,
        _async_remove_attachment,
        schema=vol.Schema(
            {**ENTRY_SCHEMA, vol.Required(ATTR_ATTACHMENT_ID): cv.string}
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_ATTACHMENTS,
        _async_list_attachments,
        schema=vol.Schema(ENTRY_SCHEMA),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_TEMPLATE,
        _async_save_template,
        schema=vol.Schema(
            {
                **ENTRY_SCHEMA,
                vol.Optional(ATTR_TEMPLATE_ID): cv.string,
                vol.Required("name"): cv.string,
                vol.Required("subject"): cv.string,
                vol.Optional("text", default=""): cv.string,
                vol.Optional("html", default=""): cv.string,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_TEMPLATE,
        _async_remove_template,
        schema=vol.Schema({**ENTRY_SCHEMA, vol.Required(ATTR_TEMPLATE_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_TEMPLATES,
        _async_list_templates,
        schema=vol.Schema(ENTRY_SCHEMA),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_SCHEDULE,
        _async_save_schedule,
        schema=_schedule_schema(),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_SCHEDULE,
        _async_remove_schedule,
        schema=vol.Schema({**ENTRY_SCHEMA, vol.Required(ATTR_SCHEDULE_ID): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_SCHEDULES,
        _async_list_schedules,
        schema=vol.Schema(ENTRY_SCHEMA),
        supports_response=SupportsResponse.ONLY,
    )


@callback
def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove all domain services when the final entry unloads."""
    if not hass.data.pop(_SERVICES_REGISTERED, False):
        return
    for service in _REGISTERED_SERVICES:
        hass.services.async_remove(DOMAIN, service)


async def _async_send(call: ServiceCall) -> ServiceResponse | None:
    if (
        call.data.get("attachments") is not None
        and call.data.get("attachment_ids") is not None
    ):
        raise ServiceValidationError(
            "Use attachments; do not provide both attachments and attachment_ids"
        )
    coordinator = _get_coordinator(call.hass, call.data)
    result = await coordinator.async_send(
        subject=call.data.get("subject"),
        text=call.data.get("text"),
        html=call.data.get("html"),
        recipients=call.data.get("recipients"),
        cc=call.data.get("cc"),
        bcc=call.data.get("bcc"),
        attachment_ids=call.data.get("attachments", call.data.get("attachment_ids")),
        template_id=call.data.get(ATTR_TEMPLATE_ID),
    )
    return _maybe_response(
        call, _result_response(result.success, result.message_id, result.error)
    )


async def _async_test_send(call: ServiceCall) -> ServiceResponse | None:
    coordinator = _get_coordinator(call.hass, call.data)
    result = await coordinator.async_test_send(call.data.get("recipients"))
    return _maybe_response(
        call, _result_response(result.success, result.message_id, result.error)
    )


async def _async_resend_last(call: ServiceCall) -> ServiceResponse | None:
    coordinator = _get_coordinator(call.hass, call.data)
    result = await coordinator.async_resend_last()
    return _maybe_response(
        call, _result_response(result.success, result.message_id, result.error)
    )


async def _async_add_attachment(call: ServiceCall) -> ServiceResponse | None:
    coordinator = _get_coordinator(call.hass, call.data)
    attachment = await coordinator.attachments.async_add(
        call.data["path"], call.data.get("name")
    )
    await coordinator.async_refresh_state()
    return _maybe_response(call, {"attachment": attachment})


async def _async_remove_attachment(call: ServiceCall) -> None:
    coordinator = _get_coordinator(call.hass, call.data)
    if not await coordinator.attachments.async_remove(call.data[ATTR_ATTACHMENT_ID]):
        raise ServiceValidationError("Unknown attachment ID")
    await coordinator.async_refresh_state()


async def _async_list_attachments(call: ServiceCall) -> ServiceResponse:
    return {
        "attachments": _get_coordinator(
            call.hass, call.data
        ).attachments.list_metadata()
    }


async def _async_save_template(call: ServiceCall) -> ServiceResponse | None:
    coordinator = _get_coordinator(call.hass, call.data)
    if not call.data["text"] and not call.data["html"]:
        raise ServiceValidationError("A plain-text or HTML template body is required")
    template = await coordinator.templates.async_save(
        call.data["name"],
        call.data["subject"],
        call.data["text"],
        call.data["html"],
        call.data.get(ATTR_TEMPLATE_ID),
    )
    await coordinator.async_refresh_state()
    return _maybe_response(call, {"template": template})


async def _async_remove_template(call: ServiceCall) -> None:
    coordinator = _get_coordinator(call.hass, call.data)
    if not await coordinator.templates.async_remove(call.data[ATTR_TEMPLATE_ID]):
        raise ServiceValidationError("Unknown template ID")
    await coordinator.async_refresh_state()


async def _async_list_templates(call: ServiceCall) -> ServiceResponse:
    return {"templates": _get_coordinator(call.hass, call.data).templates.list()}


async def _async_save_schedule(call: ServiceCall) -> ServiceResponse | None:
    coordinator = _get_coordinator(call.hass, call.data)
    schedule: dict[str, Any] = {
        key: value
        for key, value in call.data.items()
        if key not in {ATTR_ENTRY_ID, ATTR_SCHEDULE_ID}
    }
    if ATTR_SCHEDULE_ID in call.data:
        schedule["id"] = call.data[ATTR_SCHEDULE_ID]
    if not schedule.get("template_id") and not (
        schedule.get("text") or schedule.get("html")
    ):
        raise ServiceValidationError("Schedule needs a template or a message body")
    try:
        saved = await coordinator.scheduler.async_save(cast(ScheduleData, schedule))
    except ValueError as err:
        raise ServiceValidationError(str(err)) from err
    await coordinator.async_refresh_state()
    return _maybe_response(call, {"schedule": saved})


async def _async_remove_schedule(call: ServiceCall) -> None:
    coordinator = _get_coordinator(call.hass, call.data)
    if not await coordinator.scheduler.async_remove(call.data[ATTR_SCHEDULE_ID]):
        raise ServiceValidationError("Unknown schedule ID")
    await coordinator.async_refresh_state()


async def _async_list_schedules(call: ServiceCall) -> ServiceResponse:
    return {"schedules": _get_coordinator(call.hass, call.data).scheduler.list()}


def _get_coordinator(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> DocumentSenderCoordinator:
    """Select a loaded config entry, safely handling multi-entry installations."""
    requested_entry_id = data.get(ATTR_ENTRY_ID)
    candidates: list[DocumentSenderCoordinator] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if requested_entry_id and entry.entry_id != requested_entry_id:
            continue
        coordinator = getattr(entry, "runtime_data", None)
        if isinstance(coordinator, DocumentSenderCoordinator):
            candidates.append(coordinator)
    if not candidates:
        raise ServiceValidationError("No loaded Document Sender configuration found")
    if len(candidates) > 1:
        raise ServiceValidationError("entry_id is required when multiple entries exist")
    return candidates[0]


def _result_response(
    success: bool, message_id: str | None, error: str | None
) -> ServiceResponse:
    """Normalize service output and turn SMTP failures into service errors."""
    if not success:
        raise HomeAssistantError(error or "Document Sender delivery failed")
    return {"success": True, "message_id": message_id}


def _maybe_response(
    call: ServiceCall, response: ServiceResponse
) -> ServiceResponse | None:
    """Only return optional response data when the caller requested it."""
    return response if call.return_response else None


def _schedule_schema() -> vol.Schema:
    """Return the CRUD schema shared by all schedule types."""
    return vol.Schema(
        {
            **ENTRY_SCHEMA,
            vol.Optional(ATTR_SCHEDULE_ID): cv.string,
            vol.Required("name"): cv.string,
            vol.Required("schedule_type"): vol.In(
                ["daily", SCHEDULE_WEEKLY, SCHEDULE_MONTHLY, SCHEDULE_ONCE]
            ),
            vol.Required("time"): cv.string,
            vol.Optional("weekday"): vol.All(vol.Coerce(int), vol.Range(min=0, max=6)),
            vol.Optional("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
            vol.Optional("date"): cv.string,
            vol.Optional(ATTR_TEMPLATE_ID): cv.string,
            vol.Optional("subject", default=""): cv.string,
            vol.Optional("text", default=""): cv.string,
            vol.Optional("html", default=""): cv.string,
            vol.Optional("recipients", default=[]): vol.All(
                cv.ensure_list, [cv.string]
            ),
            vol.Optional("attachment_ids", default=[]): vol.All(
                cv.ensure_list, [cv.string]
            ),
            vol.Optional("enabled", default=True): cv.boolean,
        }
    )
