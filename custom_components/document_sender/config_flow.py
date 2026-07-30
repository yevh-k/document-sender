"""Config and options flow for Document Sender."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import aiosmtplib
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector

from .const import (
    CONF_IMAGE_QUALITY,
    CONF_MAX_ATTACHMENT_SIZE_MB,
    CONF_MAX_IMAGE_DIMENSION,
    CONF_NOTIFY_MOBILE,
    CONF_NOTIFY_PERSISTENT,
    CONF_RECIPIENTS,
    CONF_SENDER_EMAIL,
    CONF_SENDER_NAME,
    CONF_SMTP_HOST,
    CONF_SMTP_PORT,
    CONF_USE_TLS,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_MAX_ATTACHMENT_SIZE_MB,
    DEFAULT_MAX_IMAGE_DIMENSION,
    DEFAULT_NOTIFY_MOBILE,
    DEFAULT_NOTIFY_PERSISTENT,
    DEFAULT_RECIPIENTS,
    DEFAULT_SMTP_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _connection_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Build the schema for SMTP connection data."""
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_SMTP_HOST, default=values.get(CONF_SMTP_HOST, "smtp.gmail.com")
            ): selector.TextSelector(selector.TextSelectorConfig(type="text")),
            vol.Required(
                CONF_SMTP_PORT,
                default=values.get(CONF_SMTP_PORT, DEFAULT_SMTP_PORT),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(
                CONF_USERNAME, default=values.get(CONF_USERNAME, "")
            ): selector.TextSelector(selector.TextSelectorConfig(type="email")),
            vol.Required(
                CONF_PASSWORD, default=values.get(CONF_PASSWORD, "")
            ): selector.TextSelector(selector.TextSelectorConfig(type="password")),
            vol.Required(
                CONF_SENDER_NAME, default=values.get(CONF_SENDER_NAME, "")
            ): selector.TextSelector(selector.TextSelectorConfig(type="text")),
            vol.Required(
                CONF_SENDER_EMAIL, default=values.get(CONF_SENDER_EMAIL, "")
            ): selector.TextSelector(selector.TextSelectorConfig(type="email")),
            vol.Required(
                CONF_RECIPIENTS,
                default=values.get(CONF_RECIPIENTS, DEFAULT_RECIPIENTS),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type="email", multiple=True)
            ),
            vol.Required(
                CONF_USE_TLS, default=values.get(CONF_USE_TLS, True)
            ): selector.BooleanSelector(),
        }
    )


def _options_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Build the schema for non-secret, user-adjustable delivery options."""
    values = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_RECIPIENTS,
                default=values.get(CONF_RECIPIENTS, DEFAULT_RECIPIENTS),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type="email", multiple=True)
            ),
            vol.Required(
                CONF_MAX_IMAGE_DIMENSION,
                default=values.get(
                    CONF_MAX_IMAGE_DIMENSION, DEFAULT_MAX_IMAGE_DIMENSION
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=100, max=8000)),
            vol.Required(
                CONF_IMAGE_QUALITY,
                default=values.get(CONF_IMAGE_QUALITY, DEFAULT_IMAGE_QUALITY),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(
                CONF_MAX_ATTACHMENT_SIZE_MB,
                default=values.get(
                    CONF_MAX_ATTACHMENT_SIZE_MB,
                    DEFAULT_MAX_ATTACHMENT_SIZE_MB,
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(
                CONF_NOTIFY_PERSISTENT,
                default=values.get(CONF_NOTIFY_PERSISTENT, DEFAULT_NOTIFY_PERSISTENT),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_NOTIFY_MOBILE,
                default=values.get(CONF_NOTIFY_MOBILE, DEFAULT_NOTIFY_MOBILE),
            ): selector.BooleanSelector(),
        }
    )


class DocumentSenderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle UI configuration and secure SMTP validation."""

    VERSION = 2
    _connection_data: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect connection details without persisting them yet."""
        if user_input is not None:
            self._connection_data = dict(user_input)
            return await self.async_step_connection_actions()
        return self.async_show_form(step_id="user", data_schema=_connection_schema())

    async def async_step_connection_actions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the explicit test-connection action before entry creation."""
        del user_input
        return self.async_show_menu(
            step_id="connection_actions",
            menu_options=["test_connection", "edit_connection"],
        )

    async def async_step_edit_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Return to the SMTP form while retaining entered values."""
        del user_input
        return self.async_show_form(
            step_id="user", data_schema=_connection_schema(self._connection_data)
        )

    async def async_step_test_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Test the pending SMTP details selected from the action menu.

        Home Assistant passes ``user_input`` to every config-flow step, including
        menu actions. The value is intentionally ignored: the SMTP form state is
        retained in ``_connection_data`` until its connection test succeeds.
        """
        del user_input
        if self._connection_data is None:
            return await self.async_step_user()
        error = await _async_connection_error(self._connection_data)
        if error is not None:
            return self.async_show_form(
                step_id="user",
                data_schema=_connection_schema(self._connection_data),
                errors={"base": error},
            )

        await self.async_set_unique_id(
            self._connection_data[CONF_SENDER_EMAIL].casefold()
        )
        self._abort_if_unique_id_configured()
        title = (
            self._connection_data[CONF_SENDER_NAME]
            or self._connection_data[CONF_SENDER_EMAIL]
        )
        return self.async_create_entry(title=title, data=self._connection_data)

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Persist only a successfully tested configuration."""
        if self._connection_data is None:
            return await self.async_step_user()
        if user_input is not None:
            title = (
                self._connection_data[CONF_SENDER_NAME]
                or self._connection_data[CONF_SENDER_EMAIL]
            )
            return self.async_create_entry(title=title, data=self._connection_data)
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update required SMTP configuration and validate it before reloading."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            error = await _async_connection_error(user_input)
            if error is None:
                await self.async_set_unique_id(user_input[CONF_SENDER_EMAIL].casefold())
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=_connection_schema(user_input),
                errors={"base": error},
            )
        return self.async_show_form(
            step_id="reconfigure", data_schema=_connection_schema(entry.data)
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return options for non-secret delivery behavior."""
        return DocumentSenderOptionsFlow()


class DocumentSenderOptionsFlow(OptionsFlowWithReload):
    """Handle mutable, non-secret Document Sender options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update delivery defaults and notification preferences."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(defaults)
        )


async def _async_connection_error(data: Mapping[str, Any]) -> str | None:
    """Authenticate with SMTP without sending mail and map failures for the UI."""
    client = aiosmtplib.SMTP(
        hostname=data[CONF_SMTP_HOST],
        port=data[CONF_SMTP_PORT],
        start_tls=data[CONF_USE_TLS],
        timeout=20,
    )
    try:
        async with asyncio.timeout(25):
            await client.connect()
            await client.login(data[CONF_USERNAME], data[CONF_PASSWORD])
    except aiosmtplib.SMTPAuthenticationError:
        return "invalid_auth"
    except (aiosmtplib.SMTPException, OSError, TimeoutError):
        return "cannot_connect"
    except Exception as err:
        _LOGGER.warning(
            "Unexpected SMTP connection validation error",
            extra={"error_type": type(err).__name__},
        )
        return "unknown"
    finally:
        if client.is_connected:
            try:
                await client.quit()
            except (aiosmtplib.SMTPException, OSError):
                _LOGGER.debug(
                    "SMTP server closed before quit during configuration test"
                )
    return None
