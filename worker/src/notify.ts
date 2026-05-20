export interface R2EventPayload {
  eventType: "download" | "object-create" | "object-delete";
  bucket: string;
  key: string;
  timestamp: string;
  action?: string;
  size?: number;
  eTag?: string;
  method?: string;
  ip?: string | null;
  country?: string | null;
  userAgent?: string | null;
  referer?: string | null;
  range?: string | null;
  bytesSent?: number | null;
}

export interface NotifyEnv {
  WEBHOOK_URL: string;
  WEBHOOK_SECRET: string;
}

export async function notifyEvent(
  env: NotifyEnv,
  payload: R2EventPayload,
): Promise<void> {
  if (!env.WEBHOOK_URL || !env.WEBHOOK_SECRET) {
    console.error("WEBHOOK_URL or WEBHOOK_SECRET is not configured");
    return;
  }

  const response = await fetch(env.WEBHOOK_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${env.WEBHOOK_SECRET}`,
    },
    body: JSON.stringify({
      event_type: payload.eventType,
      bucket: payload.bucket,
      key: payload.key,
      timestamp: payload.timestamp,
      action: payload.action,
      size: payload.size,
      eTag: payload.eTag,
      method: payload.method,
      ip: payload.ip,
      country: payload.country,
      userAgent: payload.userAgent,
      referer: payload.referer,
      range: payload.range,
      bytesSent: payload.bytesSent,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    console.error(`Webhook failed (${response.status}): ${body}`);
  }
}
