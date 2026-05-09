"""notify.whatsapp platform."""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any

import aiohttp
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import WhatsAppApiClient, WhatsAppError
from .const import DOMAIN
from .store import PhonebookStore

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> WhatsAppNotificationService | None:
    """Return the notify service. Loaded by __init__ via async_load_platform."""
    if discovery_info is None or "entry_id" not in discovery_info:
        return None
    bucket = hass.data[DOMAIN][discovery_info["entry_id"]]
    return WhatsAppNotificationService(hass, bucket["client"], bucket["store"])


class WhatsAppNotificationService(BaseNotificationService):
    """Send a message via the WhatsApp Bridge."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WhatsAppApiClient,
        store: PhonebookStore,
    ) -> None:
        self._hass = hass
        self._client = client
        self._store = store

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        targets = kwargs.get(ATTR_TARGET) or []
        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            _LOGGER.warning("notify.whatsapp called without target; ignoring")
            return

        data: dict[str, Any] = kwargs.get(ATTR_DATA) or {}
        media_url: str | None = data.get("media_url")
        media_path: str | None = data.get("media_path")
        as_document: bool = bool(data.get("as_document"))
        as_voice: bool = bool(data.get("as_voice"))
        caption: str | None = data.get("caption") or message or None

        for target in targets:
            try:
                phone = await self._store.async_resolve(str(target))
            except ValueError:
                _LOGGER.warning("Skipping invalid target: %s", target)
                continue

            try:
                if media_url or media_path:
                    payload, filename, ctype = await self._load_media(
                        media_url, media_path
                    )
                    await self._client.send_media(
                        phone,
                        payload,
                        filename,
                        ctype,
                        caption=caption,
                        as_document=as_document,
                        as_voice=as_voice,
                    )
                else:
                    await self._client.send_text(phone, message)
            except WhatsAppError as err:
                _LOGGER.error("notify.whatsapp send to %s failed: %s", phone, err)

    async def _load_media(
        self, media_url: str | None, media_path: str | None
    ) -> tuple[bytes, str, str]:
        if media_path:
            path = Path(media_path)
            if not path.is_absolute():
                path = Path(self._hass.config.path()) / media_path
            if not self._hass.config.is_allowed_path(str(path)):
                raise WhatsAppError(f"path_not_allowed: {path}")
            data = await self._hass.async_add_executor_job(path.read_bytes)
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            return data, path.name, ctype

        if media_url:
            session = async_get_clientsession(self._hass)
            async with session.get(media_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.read()
                ctype = (
                    resp.headers.get("Content-Type", "").split(";")[0].strip()
                    or mimetypes.guess_type(media_url)[0]
                    or "application/octet-stream"
                )
                filename = media_url.rsplit("/", 1)[-1].split("?")[0] or "file.bin"
                return data, filename, ctype

        raise WhatsAppError("no_media_source")
