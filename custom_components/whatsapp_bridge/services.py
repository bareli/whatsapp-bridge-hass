"""Custom services for WhatsApp Bridge."""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WhatsAppApiClient, WhatsAppError
from .const import (
    DOMAIN,
    SERVICE_CONTACT_ADD,
    SERVICE_CONTACT_DELETE,
    SERVICE_CONTACT_UPDATE,
    SERVICE_SEND_LOCATION,
    SERVICE_SEND_MEDIA,
    SERVICE_SEND_TEXT,
    SERVICE_SESSION_LOGOUT,
    SERVICE_SESSION_RESTART,
)
from .store import PhonebookStore

_LOGGER = logging.getLogger(__name__)

SCHEMA_SEND_TEXT = vol.Schema(
    {
        vol.Required("target"): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("quoted_msg_id"): cv.string,
    }
)

SCHEMA_SEND_MEDIA = vol.Schema(
    {
        vol.Required("target"): cv.string,
        vol.Optional("caption"): cv.string,
        vol.Exclusive("media_url", "src"): cv.string,
        vol.Exclusive("media_path", "src"): cv.string,
        vol.Optional("as_document", default=False): cv.boolean,
        vol.Optional("as_voice", default=False): cv.boolean,
    }
)

SCHEMA_SEND_LOCATION = vol.Schema(
    {
        vol.Required("target"): cv.string,
        vol.Required("latitude"): vol.Coerce(float),
        vol.Required("longitude"): vol.Coerce(float),
        vol.Optional("name"): cv.string,
    }
)

SCHEMA_CONTACT_ADD = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("phone"): cv.string,
        vol.Optional("tags"): [cv.string],
        vol.Optional("notes"): cv.string,
    }
)

SCHEMA_CONTACT_UPDATE = vol.Schema(
    {
        vol.Required("contact_id"): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional("phone"): cv.string,
        vol.Optional("tags"): [cv.string],
        vol.Optional("notes"): cv.string,
    }
)

SCHEMA_CONTACT_DELETE = vol.Schema({vol.Required("contact_id"): cv.string})


def _bucket(hass: HomeAssistant) -> dict[str, Any]:
    entries = hass.data[DOMAIN]
    for key, val in entries.items():
        if key in ("store",):
            continue
        if isinstance(val, dict) and "client" in val:
            return val
    raise HomeAssistantError("No active WhatsApp Bridge config entry")


def _client(hass: HomeAssistant) -> WhatsAppApiClient:
    return _bucket(hass)["client"]


def _store(hass: HomeAssistant) -> PhonebookStore:
    return hass.data[DOMAIN]["store"]


async def _resolve(hass: HomeAssistant, target: str) -> str:
    return await _store(hass).async_resolve(str(target))


async def _load_media(
    hass: HomeAssistant, media_url: str | None, media_path: str | None
) -> tuple[bytes, str, str]:
    if media_path:
        path = Path(media_path)
        if not path.is_absolute():
            path = Path(hass.config.path()) / media_path
        if not hass.config.is_allowed_path(str(path)):
            raise HomeAssistantError(f"path_not_allowed: {path}")
        data = await hass.async_add_executor_job(path.read_bytes)
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return data, path.name, ctype

    if media_url:
        session = async_get_clientsession(hass)
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

    raise HomeAssistantError("no_media_source")


def async_register_services(hass: HomeAssistant) -> None:
    async def handle_send_text(call: ServiceCall) -> None:
        client = _client(hass)
        phone = await _resolve(hass, call.data["target"])
        try:
            await client.send_text(
                phone, call.data["message"], call.data.get("quoted_msg_id")
            )
        except WhatsAppError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_send_media(call: ServiceCall) -> None:
        client = _client(hass)
        phone = await _resolve(hass, call.data["target"])
        data, filename, ctype = await _load_media(
            hass, call.data.get("media_url"), call.data.get("media_path")
        )
        try:
            await client.send_media(
                phone,
                data,
                filename,
                ctype,
                caption=call.data.get("caption"),
                as_document=call.data.get("as_document", False),
                as_voice=call.data.get("as_voice", False),
            )
        except WhatsAppError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_send_location(call: ServiceCall) -> None:
        client = _client(hass)
        phone = await _resolve(hass, call.data["target"])
        try:
            await client.send_location(
                phone,
                call.data["latitude"],
                call.data["longitude"],
                call.data.get("name"),
            )
        except WhatsAppError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_contact_add(call: ServiceCall) -> None:
        await _store(hass).async_create(
            call.data["name"],
            call.data["phone"],
            call.data.get("tags"),
            call.data.get("notes"),
        )

    async def handle_contact_update(call: ServiceCall) -> None:
        try:
            await _store(hass).async_update(
                call.data["contact_id"],
                name=call.data.get("name"),
                phone=call.data.get("phone"),
                tags=call.data.get("tags"),
                notes=call.data.get("notes"),
            )
        except KeyError as err:
            raise HomeAssistantError("contact_not_found") from err

    async def handle_contact_delete(call: ServiceCall) -> None:
        try:
            await _store(hass).async_delete(call.data["contact_id"])
        except KeyError as err:
            raise HomeAssistantError("contact_not_found") from err

    async def handle_session_logout(_call: ServiceCall) -> None:
        try:
            await _client(hass).session_logout()
        except WhatsAppError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_session_restart(_call: ServiceCall) -> None:
        try:
            await _client(hass).session_restart()
        except WhatsAppError as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, SCHEMA_SEND_TEXT)
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_MEDIA, handle_send_media, SCHEMA_SEND_MEDIA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_LOCATION, handle_send_location, SCHEMA_SEND_LOCATION
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CONTACT_ADD, handle_contact_add, SCHEMA_CONTACT_ADD
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CONTACT_UPDATE, handle_contact_update, SCHEMA_CONTACT_UPDATE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CONTACT_DELETE, handle_contact_delete, SCHEMA_CONTACT_DELETE
    )
    hass.services.async_register(DOMAIN, SERVICE_SESSION_LOGOUT, handle_session_logout)
    hass.services.async_register(DOMAIN, SERVICE_SESSION_RESTART, handle_session_restart)


def async_unregister_services(hass: HomeAssistant) -> None:
    for svc in (
        SERVICE_SEND_TEXT,
        SERVICE_SEND_MEDIA,
        SERVICE_SEND_LOCATION,
        SERVICE_CONTACT_ADD,
        SERVICE_CONTACT_UPDATE,
        SERVICE_CONTACT_DELETE,
        SERVICE_SESSION_LOGOUT,
        SERVICE_SESSION_RESTART,
    ):
        hass.services.async_remove(DOMAIN, svc)
