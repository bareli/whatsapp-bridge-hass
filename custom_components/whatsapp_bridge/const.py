"""Constants for the WhatsApp Bridge integration."""
from __future__ import annotations

DOMAIN = "whatsapp_bridge"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_TOS = "tos_accepted"

DEFAULT_HOST = "a0d7b954-whatsapp_bridge"  # Supervisor internal DNS pattern; user can override
DEFAULT_PORT = 8080

EVENT_MESSAGE_RECEIVED = "whatsapp_message_received"

PANEL_URL_PATH = "whatsapp"
PANEL_STATIC_URL = "/whatsapp_bridge_static"
PANEL_FILENAME = "whatsapp-panel.js"

SERVICE_SEND_TEXT = "send_text"
SERVICE_SEND_MEDIA = "send_media"
SERVICE_SEND_LOCATION = "send_location"
SERVICE_CONTACT_ADD = "contact_add"
SERVICE_CONTACT_UPDATE = "contact_update"
SERVICE_CONTACT_DELETE = "contact_delete"
SERVICE_SESSION_LOGOUT = "session_logout"
SERVICE_SESSION_RESTART = "session_restart"

PLATFORMS = ["binary_sensor", "sensor", "image"]

STORAGE_KEY = "whatsapp_bridge.contacts"
STORAGE_VERSION = 1
