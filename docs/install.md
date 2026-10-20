# Install

The setup has two parts: the add-on (runs WhatsApp Web) and the integration (this repository).

## 1. Install the add-on

1. In Home Assistant open **Settings → Add-ons → Add-on Store → ⋮ → Repositories** and add:

    ```text
    https://github.com/bareli/whatsapp-bridge-addon
    ```

2. Install **WhatsApp Bridge** and start it. The first start downloads Chromium and may take
   several minutes.
3. Watch the add-on log for a line like:

    ```text
    Generated API token: <hex>. Save this in add-on options to keep it stable.
    ```

You can paste that token into the add-on's **Configuration** tab so it survives reinstalls. If
you leave the token blank when adding the integration, it fetches the token automatically on
first install.

## 2. Install the integration with HACS

=== "HACS search"

    1. Open HACS and search for **WhatsApp Bridge**.
    2. Download it.

    If the search does not find it, use the custom repository method.

=== "Custom repository"

    1. In HACS open the top-right **⋮** menu and choose **Custom repositories**.
    2. Repository: `https://github.com/bareli/whatsapp-bridge-hass`
    3. Type: **Integration**.
    4. Install **WhatsApp Bridge**.

Restart Home Assistant. The integration registers the sidebar **WhatsApp** panel and the
`whatsapp-qr-card` Lovelace element automatically, so no separate plugin install is needed.

## 3. Add the integration

Go to **Settings → Devices & Services → Add Integration → WhatsApp Bridge**.

1. Accept the terms warning (the checkbox is required to continue).
2. Enter the connection details:

    | Field | Notes |
    |---|---|
    | Host | Default `core-whatsapp_bridge` |
    | Port | Default `8080` |
    | API token | Optional. Leave blank to fetch it from the add-on automatically. |

Only one WhatsApp Bridge instance is supported.

## 4. Pair your phone

Open the **WhatsApp** entry in the sidebar: the pairing QR is shown at the top while the
bridge is in the `qr`, `loading` or `disconnected` state. On your phone open WhatsApp →
**Linked Devices → Link a device** and scan it. Within a few seconds the state becomes
**Ready**.

Prefer a dashboard? See the [QR card](examples.md#lovelace-qr-card).
