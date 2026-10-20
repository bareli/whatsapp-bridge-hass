# Troubleshooting

| Symptom | Fix |
|---|---|
| Card stays "Initialising" | Check the add-on log; Chromium may still be starting (first run takes about 1 to 2 minutes). |
| 401 errors in the HA log | Token mismatch. Re-fetch the token from the add-on options, or remove and re-add the integration. |
| QR never appears | The session is already paired. Use `whatsapp_bridge.session_logout` to force a re-pair. |
| `Authentication failed` | The phone unlinked the device. Force a re-pair from the panel's **Settings** tab. |
| Raspberry Pi 3 / armv7 | Not supported. Use a Pi 4/5 (aarch64) or an Intel host. |
| "Cannot reach the add-on at that host/port" | Check that the add-on is running and that host and port match. |
| "Token rejected by the add-on" | Paste the current token from the add-on log or its Configuration tab. |
| Card or panel shows no QR | Entity ids differ between fresh installs (`whatsapp_bridge_` prefix) and older ones; use the ids shown for your device. |
