"""Sidebar panel registration."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PANEL_FILENAME,
    PANEL_STATIC_URL,
    PANEL_URL_PATH,
)


async def async_register_panel(hass: HomeAssistant, version: str) -> None:
    """Register the static path and the custom sidebar panel (idempotent)."""
    static_dir = Path(__file__).parent / "panel-static"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)

    if PANEL_STATIC_URL not in hass.data.setdefault(f"{DOMAIN}_static_paths", set()):
        await hass.http.async_register_static_paths(
            [
                # Type lives in homeassistant.components.http.StaticPathConfig
                # but we use the dict-tolerant helper for older HA cores.
                _StaticPathConfig(PANEL_STATIC_URL, str(static_dir), False)  # type: ignore[arg-type]
            ]
        )
        hass.data[f"{DOMAIN}_static_paths"].add(PANEL_STATIC_URL)

    if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
        return

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="whatsapp-panel",
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{PANEL_STATIC_URL}/{PANEL_FILENAME}?v={version}",
        sidebar_title="WhatsApp",
        sidebar_icon="mdi:whatsapp",
        require_admin=True,
        embed_iframe=False,
        trust_external=False,
    )


async def async_unregister_panel(hass: HomeAssistant) -> None:
    if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)


# Tiny shim so we don't crash on HA cores predating StaticPathConfig.
class _StaticPathConfig:
    def __init__(self, url_path: str, path: str, cache_headers: bool) -> None:
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers
