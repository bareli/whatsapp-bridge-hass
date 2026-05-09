export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown> & { entity_picture?: string };
  last_changed: string;
  last_updated: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  language: string;
  callService: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ) => Promise<unknown>;
  callWS: <T = unknown>(msg: Record<string, unknown>) => Promise<T>;
  connection: { subscribeMessage: unknown };
  hassUrl: (path?: string) => string;
}

export interface WhatsAppContact {
  id: string;
  name: string;
  phone: string;
  tags: string[];
  notes: string;
}
