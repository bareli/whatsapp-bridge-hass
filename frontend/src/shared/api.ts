import type { HomeAssistant, WhatsAppContact } from "./types";

export async function listContacts(
  hass: HomeAssistant,
): Promise<WhatsAppContact[]> {
  const res = await hass.callWS<{ contacts: WhatsAppContact[] }>({
    type: "whatsapp_bridge/contacts/list",
  });
  return res.contacts;
}

export async function createContact(
  hass: HomeAssistant,
  data: Omit<WhatsAppContact, "id">,
): Promise<WhatsAppContact> {
  const res = await hass.callWS<{ contact: WhatsAppContact }>({
    type: "whatsapp_bridge/contacts/create",
    name: data.name,
    phone: data.phone,
    tags: data.tags,
    notes: data.notes,
  });
  return res.contact;
}

export async function updateContact(
  hass: HomeAssistant,
  data: WhatsAppContact,
): Promise<WhatsAppContact> {
  const res = await hass.callWS<{ contact: WhatsAppContact }>({
    type: "whatsapp_bridge/contacts/update",
    contact_id: data.id,
    name: data.name,
    phone: data.phone,
    tags: data.tags,
    notes: data.notes,
  });
  return res.contact;
}

export async function deleteContact(
  hass: HomeAssistant,
  id: string,
): Promise<void> {
  await hass.callWS({
    type: "whatsapp_bridge/contacts/delete",
    contact_id: id,
  });
}

export async function sendText(
  hass: HomeAssistant,
  target: string,
  message: string,
): Promise<void> {
  await hass.callService("whatsapp_bridge", "send_text", { target, message });
}

export async function restartSession(hass: HomeAssistant): Promise<void> {
  await hass.callService("whatsapp_bridge", "session_restart", {});
}

export async function logoutSession(hass: HomeAssistant): Promise<void> {
  await hass.callService("whatsapp_bridge", "session_logout", {});
}
