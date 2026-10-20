# Usage

## Connection settings

| Option | Default | Description |
|---|---|---|
| Host | `core-whatsapp_bridge` | Host of the add-on. |
| Port | `8080` | Port of the add-on. |
| API token | empty | Fetched from the add-on when left blank. |

If the add-on rejects the token later, Home Assistant starts a reauthentication flow where you
enter a new token.

## Targets

Every service that takes a `target` (or `recipient`) accepts one of:

- a phone number, for example `+972501234567`. Characters other than digits and `+` are
  removed, and a missing leading `+` is added;
- a contact name from the phonebook (case-insensitive);
- a contact id from the phonebook.

## Services

### `whatsapp_bridge.send_text`

| Field | Required | Description |
|---|---|---|
| `target` | yes | Phone, contact name or contact id. |
| `message` | yes | Message body. |
| `quoted_msg_id` | no | Id of a message to quote. |

### `whatsapp_bridge.send_media`

| Field | Required | Description |
|---|---|---|
| `target` | yes | Phone, contact name or contact id. |
| `caption` | no | Caption text. |
| `media_url` | one of | HTTPS URL to fetch and send. |
| `media_path` | one of | Local file path under the HA config directory (must be an allowed path). |
| `as_document` | no | Send as a document. Default `false`. |
| `as_voice` | no | Send as a voice note. Default `false`. |

`media_url` and `media_path` are mutually exclusive.

### `whatsapp_bridge.send_location`

| Field | Required | Description |
|---|---|---|
| `recipient` | yes | Phone, contact name or contact id. |
| `latitude` | yes | -90 to 90. |
| `longitude` | yes | -180 to 180. |
| `name` | no | Place name. |

### Phonebook services

| Service | Fields |
|---|---|
| `whatsapp_bridge.contact_add` | `name` and `phone` (required), `tags`, `notes` |
| `whatsapp_bridge.contact_update` | `contact_id` (required), `name`, `phone`, `tags`, `notes` |
| `whatsapp_bridge.contact_delete` | `contact_id` (required) |

The phonebook is stored in `<config>/.storage/whatsapp_bridge.contacts` and is included in
Home Assistant backups.

### Session services

| Service | What it does |
|---|---|
| `whatsapp_bridge.session_logout` | Forces a re-pair with the phone; the next start shows a new QR. |
| `whatsapp_bridge.session_restart` | Recreates the WhatsApp Web client without losing the session. |

## `notify.whatsapp`

Call it with `target` (a string or a list) and `message`. The optional `data` block accepts
`media_url`, `media_path`, `caption`, `as_document` and `as_voice`. Without `media_*` the
message is sent as text. A call without a target is ignored with a warning in the log, and an
invalid phone number is skipped with a warning.

## Entities

| Entity | Notes |
|---|---|
| State sensor | Enum: Initialising, Waiting for QR scan, Loading, Ready, Disconnected. Attributes: `phone`, `push_name`, `last_seen_at`. |
| Phone battery sensor | Percentage. |
| Last message at sensor | Timestamp. |
| Connected binary sensor | Connectivity class. |
| QR code image | PNG of the pairing QR. |

All entities belong to one **WhatsApp Bridge** device. On fresh installs entity ids carry the
`whatsapp_bridge_` prefix (for example `sensor.whatsapp_bridge_state` and
`image.whatsapp_bridge_qr`); installs from before 0.1.5 keep their older ids. Check
**Settings → Devices & Services → WhatsApp Bridge** for the exact ids on your system.

## Sidebar panel

The **WhatsApp** panel has three tabs:

- **Contacts**: list, add, edit, delete, and send a text to a contact.
- **Conversations**: conversation history is not stored locally yet; the tab points you to the
  `whatsapp_message_received` event.
- **Settings**: restart the client, or log out to force a re-pair.
