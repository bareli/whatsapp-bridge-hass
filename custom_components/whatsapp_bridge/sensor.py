"""Sensors for WhatsApp Bridge."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WhatsAppCoordinator

_OPTIONS = ["init", "qr", "loading", "ready", "disconnected"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WhatsAppCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            StateSensor(coordinator, entry.entry_id),
            BatterySensor(coordinator, entry.entry_id),
            LastMessageSensor(coordinator, entry.entry_id),
        ]
    )


class _Base(CoordinatorEntity[WhatsAppCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: WhatsAppCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id


class StateSensor(_Base):
    _attr_translation_key = "state"
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = _OPTIONS

    def __init__(self, coordinator: WhatsAppCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_state"

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        v = data.get("state")
        return v if v in _OPTIONS else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "phone": data.get("phone"),
            "push_name": data.get("push_name"),
            "last_seen_at": data.get("last_seen_at"),
        }


class BatterySensor(_Base):
    _attr_translation_key = "battery"
    _attr_name = "Phone battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: WhatsAppCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_battery"

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data or {}
        v = data.get("battery")
        return int(v) if isinstance(v, (int, float)) else None


class LastMessageSensor(_Base):
    _attr_translation_key = "last_message_at"
    _attr_name = "Last message at"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: WhatsAppCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_last_message_at"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_message_at
