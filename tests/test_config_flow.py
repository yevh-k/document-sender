"""Regression tests for the Document Sender config flow."""

from __future__ import annotations

import sys
from enum import StrEnum
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


def _install_home_assistant_flow_stubs() -> None:
    """Install the narrow Home Assistant API surface required by this unit test."""
    homeassistant = ModuleType("homeassistant")
    config_entries = ModuleType("homeassistant.config_entries")
    const = ModuleType("homeassistant.const")
    helpers = ModuleType("homeassistant.helpers")
    selector = ModuleType("homeassistant.helpers.selector")
    voluptuous = ModuleType("voluptuous")

    class ConfigEntry:
        @classmethod
        def __class_getitem__(cls, item: object) -> type[ConfigEntry]:
            return cls

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__()

    class OptionsFlowWithReload:
        pass

    class TextSelectorType(StrEnum):
        EMAIL = "email"
        PASSWORD = "password"
        TEXT = "text"

    class TextSelectorConfig(dict[str, object]):
        pass

    class TextSelector:
        def __init__(self, config: TextSelectorConfig) -> None:
            self.config = config

    class BooleanSelector:
        pass

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.ConfigFlowResult = dict[str, Any]
    config_entries.OptionsFlowWithReload = OptionsFlowWithReload
    const.CONF_PASSWORD = "password"
    const.CONF_USERNAME = "username"
    selector.BooleanSelector = BooleanSelector
    selector.TextSelector = TextSelector
    selector.TextSelectorConfig = TextSelectorConfig
    selector.TextSelectorType = TextSelectorType
    helpers.selector = selector
    voluptuous.Schema = dict
    voluptuous.All = lambda *args: args
    voluptuous.Coerce = lambda value: value
    voluptuous.Optional = lambda value, **kwargs: value
    voluptuous.Range = lambda **kwargs: kwargs
    voluptuous.Required = lambda value, **kwargs: value

    sys.modules.update(
        {
            "homeassistant": homeassistant,
            "homeassistant.config_entries": config_entries,
            "homeassistant.const": const,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.selector": selector,
            "voluptuous": voluptuous,
        }
    )


_install_home_assistant_flow_stubs()

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME  # noqa: E402

from custom_components.document_sender.config_flow import (  # noqa: E402
    DocumentSenderConfigFlow,
)
from custom_components.document_sender.const import (  # noqa: E402
    CONF_RECIPIENTS,
    CONF_SENDER_EMAIL,
    CONF_SENDER_NAME,
    CONF_SMTP_HOST,
    CONF_SMTP_PORT,
    CONF_USE_TLS,
)


@pytest.mark.asyncio
async def test_test_connection_accepts_menu_user_input_and_creates_entry() -> None:
    """Menu dispatch passes user_input and must retain the pending SMTP values."""
    pending_input = {
        CONF_SMTP_HOST: "smtp.example.com",
        CONF_SMTP_PORT: 587,
        CONF_USERNAME: "sender@example.com",
        CONF_PASSWORD: "application-password",
        CONF_SENDER_NAME: "Document Sender",
        CONF_SENDER_EMAIL: "sender@example.com",
        CONF_RECIPIENTS: ["recipient@example.com"],
        CONF_USE_TLS: True,
    }
    flow = DocumentSenderConfigFlow()
    flow._connection_data = pending_input
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock()
    flow.async_create_entry = Mock(
        return_value={"type": "create_entry", "data": pending_input}
    )

    with patch(
        "custom_components.document_sender.config_flow._async_connection_error",
        new=AsyncMock(return_value=None),
    ) as connection_error:
        result = await flow.async_step_test_connection({})

    connection_error.assert_awaited_once_with(pending_input)
    flow.async_set_unique_id.assert_awaited_once_with("sender@example.com")
    flow._abort_if_unique_id_configured.assert_called_once_with()
    flow.async_create_entry.assert_called_once_with(
        title="Document Sender", data=pending_input
    )
    assert result["type"] == "create_entry"
