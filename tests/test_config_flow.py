"""Regression tests for the Document Sender config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.document_sender.config_flow import DocumentSenderConfigFlow
from custom_components.document_sender.const import (
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
