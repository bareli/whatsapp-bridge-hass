"""Data coordinator for the WhatsApp Bridge integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhatsAppApiClient, WhatsAppError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WhatsAppCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """60s heartbeat poll fallback when WS dies."""

    def __init__(self, hass: HomeAssistant, client: WhatsAppApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.client = client
        self.qr_png: bytes | None = None
        self.qr_generated_at: datetime | None = None
        self.last_message_at: datetime | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.status()
        except WhatsAppError as err:
            raise UpdateFailed(str(err)) from err

    def apply_state_event(self, payload: dict[str, Any]) -> None:
        self.async_set_updated_data(payload)

    def apply_qr_event(self, qr_png: bytes | None) -> None:
        self.qr_png = qr_png
        self.qr_generated_at = datetime.now(timezone.utc)
        self.async_update_listeners()

    def note_message(self) -> None:
        self.last_message_at = datetime.now(timezone.utc)
        self.async_update_listeners()
