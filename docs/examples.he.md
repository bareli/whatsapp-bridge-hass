# דוגמאות

## שליחת הודעה

```yaml
service: notify.whatsapp
data:
  target: "+972501234567"
  message: "Front door motion detected at {{ now() }}"
```

באמצעות השירות ישירות:

```yaml
service: whatsapp_bridge.send_text
data:
  target: "+972501234567"
  message: "Hello from Home Assistant"
```

## שליחת מדיה

```yaml
service: whatsapp_bridge.send_media
data:
  target: "+972501234567"
  caption: "Driveway snapshot"
  media_path: /config/www/snapshots/driveway.jpg
```

## שליחת מיקום

```yaml
service: whatsapp_bridge.send_location
data:
  recipient: "+972501234567"
  latitude: 32.5
  longitude: 34.9
  name: "Home"
```

## תגובה להודעות נכנסות

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

המטען (payload) של האירוע כולל: `id`, `from`, `to`, `body`, `timestamp`, `has_media`,
`media_mime` ו-`ack`.

## כרטיס QR ב-Lovelace { #lovelace-qr-card }

האינטגרציה רושמת את הכרטיס בעצמה.

```yaml
type: custom:whatsapp-qr-card
entity: image.whatsapp_qr
status_entity: sensor.whatsapp_state
```

השתמשו במזהי הישויות הקיימים אצלכם (בהתקנות חדשות: `image.whatsapp_bridge_qr` ו-
`sensor.whatsapp_bridge_state`). כשהמצב משתנה ל-**Ready**, הכרטיס מתכווץ לתג סטטוס.
