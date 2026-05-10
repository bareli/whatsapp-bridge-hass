"""Sidebar panel + Lovelace card registration."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PANEL_FILENAME,
    PANEL_STATIC_URL,
    PANEL_URL_PATH,
    QR_CARD_FILENAME,
)


async def async_register_frontend(hass: HomeAssistant, version: str) -> None:
    """Register static path, sidebar panel, and Lovelace card resource."""
    static_dir = Path(__file__).parent / "panel-static"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)

    if PANEL_STATIC_URL not in hass.data.setdefault(f"{DOMAIN}_static_paths", set()):
        await hass.http.async_register_static_paths(
            [
                _StaticPathConfig(PANEL_STATIC_URL, str(static_dir), False)  # type: ignore[arg-type]
            ]
        )
        hass.data[f"{DOMAIN}_static_paths"].add(PANEL_STATIC_URL)

    qr_card_url = f"{PANEL_STATIC_URL}/{QR_CARD_FILENAME}?v={version}"
    extra_urls: set[str] = hass.data.setdefault(f"{DOMAIN}_extra_js", set())
    if qr_card_url not in extra_urls:
        frontend.add_extra_js_url(hass, qr_card_url)
        extra_urls.add(qr_card_url)

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


class _StaticPathConfig:
    def __init__(self, url_path: str, path: str, cache_headers: bool) -> None:
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers
