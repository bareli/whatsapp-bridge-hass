"""Binary sensor for WhatsApp connection state."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WhatsAppCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WhatsAppCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([WhatsAppConnectedBinarySensor(coordinator, entry.entry_id)])


class WhatsAppConnectedBinarySensor(
    CoordinatorEntity[WhatsAppCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True
    _attr_translation_key = "connected"
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: WhatsAppCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_connected"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return data.get("state") == "ready"

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
