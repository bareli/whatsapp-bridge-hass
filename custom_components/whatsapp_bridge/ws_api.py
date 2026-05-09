"""WebSocket API exposed to the panel for phonebook CRUD."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .store import PhonebookStore


def _store(hass: HomeAssistant) -> PhonebookStore:
    return hass.data[DOMAIN]["store"]


@callback
def async_register_ws(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_create)
    websocket_api.async_register_command(hass, ws_update)
    websocket_api.async_register_command(hass, ws_delete)


@websocket_api.websocket_command({vol.Required("type"): "whatsapp_bridge/contacts/list"})
@websocket_api.async_response
async def ws_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    contacts = await _store(hass).async_list()
    connection.send_result(msg["id"], {"contacts": contacts})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "whatsapp_bridge/contacts/create",
        vol.Required("name"): str,
        vol.Required("phone"): str,
        vol.Optional("tags"): [str],
        vol.Optional("notes"): str,
    }
)
@websocket_api.async_response
async def ws_create(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    try:
        contact = await _store(hass).async_create(
            msg["name"], msg["phone"], msg.get("tags"), msg.get("notes")
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    connection.send_result(msg["id"], {"contact": contact})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "whatsapp_bridge/contacts/update",
        vol.Required("contact_id"): str,
        vol.Optional("name"): str,
        vol.Optional("phone"): str,
        vol.Optional("tags"): [str],
        vol.Optional("notes"): str,
    }
)
@websocket_api.async_response
async def ws_update(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    try:
        contact = await _store(hass).async_update(
            msg["contact_id"],
            name=msg.get("name"),
            phone=msg.get("phone"),
            tags=msg.get("tags"),
            notes=msg.get("notes"),
        )
    except KeyError:
        connection.send_error(msg["id"], "not_found", "contact not found")
        return
    except ValueError as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    connection.send_result(msg["id"], {"contact": contact})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "whatsapp_bridge/contacts/delete",
        vol.Required("contact_id"): str,
    }
)
@websocket_api.async_response
async def ws_delete(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    try:
        await _store(hass).async_delete(msg["contact_id"])
    except KeyError:
        connection.send_error(msg["id"], "not_found", "contact not found")
        return
    connection.send_result(msg["id"], {"ok": True})
