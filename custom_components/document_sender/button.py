"""Buttons for Document Sender."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DocumentSenderConfigEntry
from .coordinator import DocumentSenderCoordinator


@dataclass(frozen=True, kw_only=True)
class DocumentSenderButtonDescription(ButtonEntityDescription):
    """Description for a Document Sender action button."""

    action: str


BUTTONS: tuple[DocumentSenderButtonDescription, ...] = (
    DocumentSenderButtonDescription(
        key="send", translation_key="send", action="send", icon="mdi:send"
    ),
    DocumentSenderButtonDescription(
        key="test", translation_key="test", action="test", icon="mdi:email-check"
    ),
    DocumentSenderButtonDescription(
        key="resend", translation_key="resend", action="resend", icon="mdi:email-sync"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DocumentSenderConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up action buttons for an entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        DocumentSenderButton(coordinator, description) for description in BUTTONS
    )


class DocumentSenderButton(ButtonEntity):
    """A button bound to one coordinator action."""

    entity_description: DocumentSenderButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DocumentSenderCoordinator,
        description: DocumentSenderButtonDescription,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {("document_sender", coordinator.entry.entry_id)},
            "name": f"Document Sender ({coordinator.entry.title})",
            "manufacturer": "Document Sender",
            "model": "SMTP document delivery",
        }

    async def async_press(self) -> None:
        """Run the selected delivery action."""
        if self.entity_description.action == "send":
            await self.coordinator.async_send(
                subject="Document Sender manual message",
                text="Manual send requested from Home Assistant.",
                source="button",
            )
        elif self.entity_description.action == "test":
            await self.coordinator.async_test_send()
        else:
            await self.coordinator.async_resend_last()
