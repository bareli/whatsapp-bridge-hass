import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, WhatsAppContact } from "./shared/types";
import {
  createContact,
  deleteContact,
  listContacts,
  logoutSession,
  restartSession,
  sendText,
  updateContact,
} from "./shared/api";

type Tab = "contacts" | "conversations" | "settings";

interface Draft {
  id?: string;
  name: string;
  phone: string;
  notes: string;
}

@customElement("whatsapp-panel")
export class WhatsAppPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ attribute: false }) narrow = false;
  @property({ attribute: false }) panel?: { config?: Record<string, unknown> };

  @state() private _tab: Tab = "contacts";
  @state() private _contacts: WhatsAppContact[] = [];
  @state() private _loading = false;
  @state() private _error?: string;
  @state() private _editing?: Draft;
  @state() private _sendTo?: WhatsAppContact;
  @state() private _sendBody = "";
  @state() private _sending = false;

  protected firstUpdated() {
    this._refresh();
  }

  protected updated(changed: Map<string, unknown>) {
    if (changed.has("hass") && !this._contacts.length && this.hass && !this._loading) {
      this._refresh();
    }
  }

  private async _refresh() {
    if (!this.hass) return;
    this._loading = true;
    this._error = undefined;
    try {
      this._contacts = await listContacts(this.hass);
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._loading = false;
    }
  }

  static get styles() {
    return css`
      :host {
        display: block;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
        height: 100vh;
        overflow: auto;
      }
      header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: var(--app-header-background-color, var(--primary-color));
        color: var(--app-header-text-color, #fff);
      }
      header h1 { font-size: 18px; margin: 0; }
      nav {
        display: flex;
        gap: 4px;
        padding: 8px 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      nav button {
        background: transparent;
        border: none;
        padding: 8px 14px;
        border-radius: 6px;
        cursor: pointer;
        color: var(--primary-text-color);
      }
      nav button.active {
        background: var(--primary-color);
        color: #fff;
      }
      main { padding: 16px; max-width: 960px; margin: 0 auto; }
      .row { display: flex; gap: 12px; align-items: center; }
      .row > * { flex: 1; }
      .toolbar { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { padding: 10px; text-align: left; border-bottom: 1px solid var(--divider-color); font-size: 14px; }
      th { font-weight: 600; }
      .actions { display: flex; gap: 6px; }
      button.btn {
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 13px;
      }
      button.btn.primary {
        background: var(--primary-color);
        color: #fff;
        border-color: var(--primary-color);
      }
      button.btn.danger {
        background: #dc2626;
        color: #fff;
        border-color: #dc2626;
      }
      .modal-backdrop {
        position: fixed; inset: 0; background: rgba(0,0,0,.5);
        display: flex; align-items: center; justify-content: center; z-index: 50;
      }
      .modal {
        background: var(--card-background-color);
        border-radius: 8px;
        padding: 16px;
        width: min(420px, 92vw);
        display: flex; flex-direction: column; gap: 10px;
      }
      label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
      input, textarea {
        font: inherit;
        padding: 8px;
        border-radius: 6px;
        border: 1px solid var(--divider-color);
        background: var(--primary-background-color);
        color: var(--primary-text-color);
      }
      .error {
        background: #fee2e2; color: #991b1b;
        padding: 8px 12px; border-radius: 6px; font-size: 13px;
      }
      .tos {
        background: #fef3c7; color: #78350f;
        padding: 10px 12px; border-radius: 6px; font-size: 12px; line-height: 1.4;
      }
    `;
  }

  render() {
    return html`
      <header>
        <ha-icon icon="mdi:whatsapp"></ha-icon>
        <h1>WhatsApp Bridge</h1>
      </header>
      <nav>
        ${(["contacts", "conversations", "settings"] as Tab[]).map(
          (t) => html`
            <button
              class=${t === this._tab ? "active" : ""}
              @click=${() => (this._tab = t)}
            >${t.charAt(0).toUpperCase() + t.slice(1)}</button>
          `,
        )}
      </nav>
      <main>
        ${this._error ? html`<div class="error">${this._error}</div>` : nothing}
        ${this._tab === "contacts" ? this._renderContacts() : nothing}
        ${this._tab === "conversations" ? this._renderConversations() : nothing}
        ${this._tab === "settings" ? this._renderSettings() : nothing}
      </main>
      ${this._editing ? this._renderEditor() : nothing}
      ${this._sendTo ? this._renderSendDialog() : nothing}
    `;
  }

  private _renderContacts() {
    return html`
      <div class="toolbar">
        <strong>${this._contacts.length} contact(s)</strong>
        <div class="actions">
          <button class="btn" @click=${this._refresh}>Refresh</button>
          <button class="btn primary" @click=${() =>
            (this._editing = { name: "", phone: "", notes: "" })}>Add contact</button>
        </div>
      </div>
      ${this._loading
        ? html`<p>Loading…</p>`
        : html`
            <table>
              <thead>
                <tr><th>Name</th><th>Phone</th><th>Notes</th><th></th></tr>
              </thead>
              <tbody>
                ${this._contacts.map(
                  (c) => html`
                    <tr>
                      <td>${c.name}</td>
                      <td><code>${c.phone}</code></td>
                      <td>${c.notes || ""}</td>
                      <td class="actions">
                        <button class="btn" @click=${() =>
                          (this._sendTo = c)}>Send</button>
                        <button class="btn" @click=${() =>
                          (this._editing = {
                            id: c.id,
                            name: c.name,
                            phone: c.phone,
                            notes: c.notes,
                          })}>Edit</button>
                        <button class="btn danger" @click=${() => this._delete(c.id)}>Delete</button>
                      </td>
                    </tr>
                  `,
                )}
              </tbody>
            </table>
          `}
    `;
  }

  private _renderConversations() {
    return html`
      <p>Conversation history is not stored locally yet. Use Developer Tools → Events
        and listen for <code>whatsapp_message_received</code> to wire automations.</p>
    `;
  }

  private _renderSettings() {
    return html`
      <div class="tos">
        Reminder: <code>whatsapp-web.js</code> is unofficial. Your account may be
        banned for bot-style use. Prefer a secondary phone number.
      </div>
      <div class="row" style="margin-top:16px">
        <button class="btn" @click=${async () => this.hass && (await restartSession(this.hass))}>
          Restart client
        </button>
        <button class="btn danger" @click=${async () =>
          this.hass && confirm("Force re-pair with the phone?") && (await logoutSession(this.hass))}>
          Logout (force re-pair)
        </button>
      </div>
    `;
  }

  private _renderEditor() {
    const draft = this._editing!;
    return html`
      <div class="modal-backdrop" @click=${(e: MouseEvent) =>
        e.target === e.currentTarget && (this._editing = undefined)}>
        <div class="modal">
          <h3 style="margin:0">${draft.id ? "Edit contact" : "Add contact"}</h3>
          <label>Name
            <input .value=${draft.name}
              @input=${(e: Event) =>
                (this._editing = { ...draft, name: (e.target as HTMLInputElement).value })} />
          </label>
          <label>Phone
            <input .value=${draft.phone}
              placeholder="+972501234567"
              @input=${(e: Event) =>
                (this._editing = { ...draft, phone: (e.target as HTMLInputElement).value })} />
          </label>
          <label>Notes
            <textarea rows="3" .value=${draft.notes}
              @input=${(e: Event) =>
                (this._editing = { ...draft, notes: (e.target as HTMLTextAreaElement).value })}></textarea>
          </label>
          <div class="actions" style="justify-content:flex-end">
            <button class="btn" @click=${() => (this._editing = undefined)}>Cancel</button>
            <button class="btn primary" @click=${this._save}>Save</button>
          </div>
        </div>
      </div>
    `;
  }

  private _renderSendDialog() {
    const c = this._sendTo!;
    return html`
      <div class="modal-backdrop" @click=${(e: MouseEvent) =>
        e.target === e.currentTarget && (this._sendTo = undefined)}>
        <div class="modal">
          <h3 style="margin:0">Send to ${c.name}</h3>
          <label>Message
            <textarea rows="4" .value=${this._sendBody}
              @input=${(e: Event) => (this._sendBody = (e.target as HTMLTextAreaElement).value)}></textarea>
          </label>
          <div class="actions" style="justify-content:flex-end">
            <button class="btn" @click=${() => {
              this._sendTo = undefined;
              this._sendBody = "";
            }}>Cancel</button>
            <button class="btn primary" ?disabled=${this._sending} @click=${this._send}>
              ${this._sending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private async _save() {
    if (!this.hass || !this._editing) return;
    const draft = this._editing;
    try {
      if (draft.id) {
        await updateContact(this.hass, {
          id: draft.id,
          name: draft.name,
          phone: draft.phone,
          tags: [],
          notes: draft.notes,
        });
      } else {
        await createContact(this.hass, {
          name: draft.name,
          phone: draft.phone,
          tags: [],
          notes: draft.notes,
        });
      }
      this._editing = undefined;
      await this._refresh();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    }
  }

  private async _delete(id: string) {
    if (!this.hass) return;
    if (!confirm("Delete this contact?")) return;
    try {
      await deleteContact(this.hass, id);
      await this._refresh();
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    }
  }

  private async _send() {
    if (!this.hass || !this._sendTo || !this._sendBody.trim()) return;
    this._sending = true;
    try {
      await sendText(this.hass, this._sendTo.phone, this._sendBody);
      this._sendTo = undefined;
      this._sendBody = "";
    } catch (err: unknown) {
      this._error = err instanceof Error ? err.message : String(err);
    } finally {
      this._sending = false;
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "whatsapp-panel": WhatsAppPanel;
  }
}
