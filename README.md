# WhatsApp Bridge — Home Assistant integration

> ⚠️ **Unofficial WhatsApp client.** This integration drives
> [`whatsapp-web.js`](https://wwebjs.dev/) inside a companion add-on. WhatsApp's
> Terms of Service do not authorize bot-style use of personal accounts. Your
> account may be banned, temporarily or permanently. **Use a secondary phone
> number, not your primary one.** You accept this risk by installing the
> integration.

Send and receive WhatsApp messages from Home Assistant. Includes:

- A `notify.whatsapp` platform.
- Custom services: `send_text`, `send_media`, `send_location`,
  `contact_add/update/delete`, `session_logout`, `session_restart`.
- A `whatsapp_message_received` HA event for incoming messages.
- Sensors for connection state, phone battery, last-message timestamp.
- An `image.whatsapp_qr` entity that surfaces the pairing QR.
- A **Lovelace QR card** for one-tap pairing.
- A **sidebar panel** for managing your phonebook.

## Requirements

- Home Assistant OS or Supervised.
- The companion **WhatsApp Bridge add-on** running on the same host.
- One spare WhatsApp account / phone number (do **not** use your primary).

## Install

### 1. Install the add-on

In **Settings → Add-ons → Add-on Store → ⋮ → Repositories**, add:

```
https://github.com/your-username/whatsapp-bridge-addon
```

Then install **WhatsApp Bridge** and start it. The first start downloads
Chromium and may take several minutes. Watch the log for a line like:

```
Generated API token: <hex>. Save this in add-on options to keep it stable.
```

You can paste that token into the add-on's **Configuration** tab so it
survives reinstalls. The integration auto-fetches the token on first install
if you leave it blank.

### 2. Install this integration via HACS

In HACS, open **Custom repositories** and add this repository **twice**:

| URL | Category |
|---|---|
| `https://github.com/your-username/whatsapp-bridge-hass` | Integration |
| `https://github.com/your-username/whatsapp-bridge-hass` | Plugin |

Download "WhatsApp Bridge" under both categories, restart Home Assistant.

### 3. Configure

Go to **Settings → Devices & Services → Add Integration → WhatsApp Bridge**.
Accept the ToS warning. The default host (`core-whatsapp_bridge`, port `8080`)
works on standard HAOS. Leave the token blank to fetch it automatically.

### 4. Pair

Add the **WhatsApp QR Card** to a Lovelace dashboard:

```yaml
type: custom:whatsapp-qr-card
entity: image.whatsapp_qr
status_entity: sensor.whatsapp_state
```

Open WhatsApp on your phone → **Linked Devices** → **Link a device**, and scan
the QR shown on the card. Within a few seconds the state flips to **Ready**
and the QR card collapses to a status pill.

## Sending messages

```yaml
service: notify.whatsapp
data:
  target: "+972501234567"
  message: "Front door motion detected at {{ now() }}"
```

Send media:

```yaml
service: whatsapp_bridge.send_media
data:
  target: "+972501234567"
  caption: "Driveway snapshot"
  media_path: /config/www/snapshots/driveway.jpg
```

## Receiving messages

```yaml
trigger:
  - platform: event
    event_type: whatsapp_message_received
action:
  - service: persistent_notification.create
    data:
      title: "WhatsApp from {{ trigger.event.data.from }}"
      message: "{{ trigger.event.data.body }}"
```

The event payload contains: `id`, `from`, `to`, `body`, `timestamp`,
`has_media`, `media_mime`, `ack`.

## Phonebook

Open the **WhatsApp** entry in the sidebar → **Contacts** tab. Or use the
service calls `whatsapp_bridge.contact_add` / `contact_update` /
`contact_delete`. The store lives in
`<config>/.storage/whatsapp_bridge.contacts` and is part of HA backups.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Card stays "Initialising" | Check the add-on log; Chromium may still be starting (first run ≈ 1–2 min). |
| 401 errors in HA log | Token mismatch. Re-fetch via add-on options or remove and re-add the integration. |
| QR never appears | The session is already paired. Use `whatsapp_bridge.session_logout` to force re-pair. |
| `Authentication failed` | Phone unlinked the device. Force re-pair via the panel's Settings tab. |
| Pi 3 / armv7 | Not supported. Use a Pi 4/5 (aarch64) or Intel host. |

## License

Apache-2.0.
