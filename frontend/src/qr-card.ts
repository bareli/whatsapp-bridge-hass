import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "./shared/types";
import { restartSession } from "./shared/api";

interface QrCardConfig {
  type: string;
  entity?: string;
  status_entity?: string;
}

const STATE_LABEL: Record<string, string> = {
  init: "Initialising",
  qr: "Waiting for QR scan",
  loading: "Loading",
  ready: "Ready",
  disconnected: "Disconnected",
};

@customElement("whatsapp-qr-card")
export class WhatsAppQrCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @state() private _config?: QrCardConfig;
  @state() private _busy = false;

  setConfig(config: QrCardConfig) {
    if (!config) throw new Error("Invalid config");
    this._config = {
      type: config.type,
      entity: config.entity || "image.whatsapp_qr",
      status_entity: config.status_entity || "sensor.whatsapp_state",
    };
  }

  static get styles() {
    return css`
      ha-card {
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
      }
      .pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        color: #fff;
        font-size: 13px;
        font-weight: 600;
      }
      .pill.ready { background: #16a34a; }
      .pill.qr { background: #f59e0b; }
      .pill.loading { background: #3b82f6; }
      .pill.init { background: #6b7280; }
      .pill.disconnected { background: #dc2626; }
      img.qr {
        width: 256px;
        height: 256px;
        background: #fff;
        border-radius: 8px;
        padding: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,.15);
      }
      .meta { font-size: 13px; color: var(--secondary-text-color); }
      .footer {
        font-size: 11px;
        color: var(--secondary-text-color);
        text-align: center;
        max-width: 320px;
        margin-top: 8px;
      }
      mwc-button { --mdc-theme-primary: var(--primary-color); }
    `;
  }

  render() {
    if (!this._config || !this.hass) return nothing;

    const statusEntity = this.hass.states[this._config.status_entity!];
    const imageEntity = this.hass.states[this._config.entity!];
    const stateValue = statusEntity?.state ?? "init";
    const phone = statusEntity?.attributes?.phone as string | undefined;

    return html`
      <ha-card header="WhatsApp Bridge">
        <span class="pill ${stateValue}">${STATE_LABEL[stateValue] || stateValue}</span>
        ${stateValue === "qr" && imageEntity?.attributes?.entity_picture
          ? html`<img class="qr" alt="WhatsApp QR" src=${imageEntity.attributes.entity_picture as string} />`
          : nothing}
        ${stateValue === "ready"
          ? html`<div class="meta">Linked to ${phone || "phone"}</div>`
          : nothing}
        ${stateValue === "disconnected"
          ? html`
              <mwc-button
                raised
                ?disabled=${this._busy}
                @click=${this._restart}
              >Restart session</mwc-button>
            `
          : nothing}
        <div class="footer">
          Unofficial WhatsApp client — your account may be banned.
          Use a secondary number, not your primary.
        </div>
      </ha-card>
    `;
  }

  private async _restart() {
    if (!this.hass) return;
    this._busy = true;
    try {
      await restartSession(this.hass);
    } finally {
      this._busy = false;
    }
  }

  getCardSize(): number {
    return 6;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "whatsapp-qr-card": WhatsAppQrCard;
  }
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description: string;
    }>;
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "whatsapp-qr-card",
  name: "WhatsApp QR Card",
  description: "Pair WhatsApp Bridge by scanning the QR code.",
});
