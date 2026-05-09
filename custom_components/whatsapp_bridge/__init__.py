"""WhatsApp Bridge integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WhatsAppApiClient, WhatsAppAuthError, WhatsAppOfflineError
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    DOMAIN,
    EVENT_MESSAGE_RECEIVED,
    PLATFORMS,
)
from .coordinator import WhatsAppCoordinator
from .panel import async_register_panel, async_unregister_panel
from .services import async_register_services, async_unregister_services
from .store import PhonebookStore
from .ws_api import async_register_ws
from .ws_client import WhatsAppWsClient

_LOGGER = logging.getLogger(__name__)

PLATFORM_LIST = [Platform(p) for p in PLATFORMS]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: dict[str, Any]) -> bool:
    """Set up shared resources."""
    bucket = hass.data.setdefault(DOMAIN, {})
    if "store" not in bucket:
        bucket["store"] = PhonebookStore(hass)
        await bucket["store"].async_load()
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    bucket = hass.data.setdefault(DOMAIN, {})
    if "store" not in bucket:
        bucket["store"] = PhonebookStore(hass)
        await bucket["store"].async_load()

    session = async_get_clientsession(hass)
    client = WhatsAppApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_TOKEN) or None,
    )

    try:
        initial = await client.status()
    except WhatsAppAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except WhatsAppOfflineError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = WhatsAppCoordinator(hass, client)
    coordinator.async_set_updated_data(initial)

    async def _handle_event(evt: dict[str, Any]) -> None:
        kind = evt.get("type")
        payload = evt.get("payload") or {}
        if kind == "state":
            coordinator.apply_state_event(payload)
            if payload.get("state") == "qr":
                qr_png = await client.get_qr_png()
                coordinator.apply_qr_event(qr_png)
        elif kind == "qr":
            qr_png = await client.get_qr_png()
            coordinator.apply_qr_event(qr_png)
        elif kind == "message":
            coordinator.note_message()
            hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, payload)

    ws = WhatsAppWsClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_TOKEN) or None,
        _handle_event,
    )
    ws.start()

    if initial.get("state") == "qr":
        qr_png = await client.get_qr_png()
        coordinator.apply_qr_event(qr_png)

    bucket[entry.entry_id] = {
        "client": client,
        "store": bucket["store"],
        "coordinator": coordinator,
        "ws": ws,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM_LIST)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {"entry_id": entry.entry_id, "name": "whatsapp"},
            {},
        )
    )

    if not bucket.get("services_registered"):
        async_register_services(hass)
        async_register_ws(hass)
        bucket["services_registered"] = True

    await async_register_panel(hass, version=entry.version_string if hasattr(entry, "version_string") else "1")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Tear down a config entry."""
    bucket = hass.data.get(DOMAIN, {})
    entry_data = bucket.pop(entry.entry_id, None)
    if entry_data and entry_data.get("ws"):
        await entry_data["ws"].stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORM_LIST)

    remaining = [
        v for k, v in bucket.items()
        if k not in ("store", "services_registered") and isinstance(v, dict) and "client" in v
    ]
    if not remaining:
        async_unregister_services(hass)
        await async_unregister_panel(hass)
        bucket["services_registered"] = False

    return unload_ok
