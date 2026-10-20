# Examples

## Send a message

```yaml
service: notify.whatsapp
data:
  target: "+972501234567"
  message: "Front door motion detected at {{ now() }}"
```

With the service directly:

```yaml
service: whatsapp_bridge.send_text
data:
  target: "+972501234567"
  message: "Hello from Home Assistant"
```

## Send media

```yaml
service: whatsapp_bridge.send_media
data:
  target: "+972501234567"
  caption: "Driveway snapshot"
  media_path: /config/www/snapshots/driveway.jpg
```

## Send a location

```yaml
service: whatsapp_bridge.send_location
data:
  recipient: "+972501234567"
  latitude: 32.5
  longitude: 34.9
  name: "Home"
```

## React to incoming messages

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

The event payload contains `id`, `from`, `to`, `body`, `timestamp`, `has_media`,
`media_mime` and `ack`.

## Lovelace QR card

The integration registers the card for you.

```yaml
type: custom:whatsapp-qr-card
entity: image.whatsapp_qr
status_entity: sensor.whatsapp_state
```

Use the entity ids that exist on your system (on fresh installs they are
`image.whatsapp_bridge_qr` and `sensor.whatsapp_bridge_state`). When the state becomes
**Ready**, the card collapses to a status pill.
