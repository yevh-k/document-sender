"""Document Sender integration setup."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import CONF_SENDER, CONF_SENDER_EMAIL, CONF_SENDER_NAME, DOMAIN, PLATFORMS
from .coordinator import DocumentSenderCoordinator
from .services import async_register_services, async_unregister_services

type DocumentSenderConfigEntry = ConfigEntry[DocumentSenderCoordinator]


async def async_setup(hass: HomeAssistant, config: dict[str, object]) -> bool:
    """Set up Document Sender service registration."""
    await async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: DocumentSenderConfigEntry
) -> bool:
    """Set up Document Sender from a config entry."""
    await async_register_services(hass)
    coordinator = DocumentSenderCoordinator(hass, entry)
    await coordinator.async_setup()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DocumentSenderConfigEntry
) -> bool:
    """Unload a Document Sender config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_close()
        other_loaded_entries = any(
            other.entry_id != entry.entry_id and other.state is ConfigEntryState.LOADED
            for other in hass.config_entries.async_entries(DOMAIN)
        )
        if not other_loaded_entries:
            async_unregister_services(hass)
    return unload_ok


async def async_migrate_entry(
    hass: HomeAssistant, entry: DocumentSenderConfigEntry
) -> bool:
    """Migrate v1 entries to separate sender name and email fields."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        data = dict(entry.data)
        legacy_sender = data.pop(CONF_SENDER, "")
        data[CONF_SENDER_EMAIL] = legacy_sender
        data[CONF_SENDER_NAME] = legacy_sender.partition("@")[0]
        hass.config_entries.async_update_entry(entry, data=data, version=2)
    return True
