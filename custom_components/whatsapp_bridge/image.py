"""QR image entity for WhatsApp Bridge."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
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
    async_add_entities([WhatsAppQrImage(hass, coordinator, entry.entry_id)])


class WhatsAppQrImage(CoordinatorEntity[WhatsAppCoordinator], ImageEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "qr"
    _attr_name = "QR code"
    _attr_content_type = "image/png"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: WhatsAppCoordinator,
        entry_id: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = f"{entry_id}_qr"

    @property
    def available(self) -> bool:
        data = self.coordinator.data or {}
        return data.get("state") == "qr" and self.coordinator.qr_png is not None

    async def async_image(self) -> bytes | None:
        return self.coordinator.qr_png

    @property
    def image_last_updated(self) -> datetime | None:
        return self.coordinator.qr_generated_at

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.qr_generated_at:
            self._attr_image_last_updated = self.coordinator.qr_generated_at
        self.async_write_ha_state()
