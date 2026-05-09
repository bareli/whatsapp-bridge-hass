"""Config flow for WhatsApp Bridge."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    WhatsAppApiClient,
    WhatsAppAuthError,
    WhatsAppError,
    WhatsAppOfflineError,
)
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    CONF_TOS,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_INTERNAL_HOST = "core-whatsapp_bridge"  # supervisor docker DNS hint
TITLE = "WhatsApp Bridge"


class WhatsAppBridgeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._tos_accepted: bool = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_TOS):
                errors["base"] = "tos_required"
            else:
                self._tos_accepted = True
                return await self.async_step_connection()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_TOS, default=False): bool}
            ),
            errors=errors,
            description_placeholders={
                "tos_url": "https://www.whatsapp.com/legal/terms-of-service"
            },
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        defaults = {
            CONF_HOST: DEFAULT_INTERNAL_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_TOKEN: "",
        }
        if user_input is not None:
            host: str = user_input[CONF_HOST].strip()
            port: int = int(user_input[CONF_PORT])
            token: str = user_input[CONF_TOKEN].strip()

            session = async_get_clientsession(self.hass)
            client = WhatsAppApiClient(session, host, port, token or None)

            try:
                if not token:
                    fetched = await client.bootstrap_token()
                    if fetched:
                        token = fetched
                        client.update_token(token)
                    else:
                        errors["base"] = "missing_token"
                if not errors:
                    await client.status()
            except WhatsAppAuthError:
                errors[CONF_TOKEN] = "invalid_token"
            except WhatsAppOfflineError:
                errors["base"] = "cannot_connect"
            except WhatsAppError as err:
                _LOGGER.exception("Unexpected error during config: %s", err)
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=TITLE,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_TOKEN: token,
                    },
                )

            defaults = {CONF_HOST: host, CONF_PORT: port, CONF_TOKEN: token}

        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=defaults[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=defaults[CONF_PORT]): int,
                    vol.Optional(CONF_TOKEN, default=defaults[CONF_TOKEN]): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, _entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        host = entry.data[CONF_HOST]
        port = entry.data[CONF_PORT]

        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            session = async_get_clientsession(self.hass)
            client = WhatsAppApiClient(session, host, port, token or None)
            try:
                await client.status()
            except WhatsAppAuthError:
                errors[CONF_TOKEN] = "invalid_token"
            except WhatsAppOfflineError:
                errors["base"] = "cannot_connect"
            except WhatsAppError:
                errors["base"] = "unknown"
            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_TOKEN: token}
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    def _get_reauth_entry(self):
        return self.hass.config_entries.async_get_entry(self.context["entry_id"])
