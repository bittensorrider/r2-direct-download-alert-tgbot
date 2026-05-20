import { notifyEvent, type NotifyEnv, type R2EventPayload } from "./notify";

interface R2QueueMessage {
  action: string;
  bucket: string;
  object?: {
    key: string;
    size?: number;
    eTag?: string;
  };
  eventTime: string;
}

function mapQueueMessage(message: R2QueueMessage): R2EventPayload | null {
  const key = message.object?.key;
  if (!key) {
    return null;
  }

  const deleteActions = new Set(["DeleteObject", "LifecycleDeletion"]);
  if (deleteActions.has(message.action)) {
    return {
      eventType: "object-delete",
      bucket: message.bucket,
      key,
      timestamp: message.eventTime,
      action: message.action,
      eTag: message.object?.eTag,
    };
  }

  const createActions = new Set([
    "PutObject",
    "CopyObject",
    "CompleteMultipartUpload",
  ]);
  if (createActions.has(message.action)) {
    return {
      eventType: "object-create",
      bucket: message.bucket,
      key,
      timestamp: message.eventTime,
      action: message.action,
      size: message.object?.size,
      eTag: message.object?.eTag,
    };
  }

  return null;
}

export async function handleQueueBatch(
  batch: MessageBatch<R2QueueMessage>,
  env: NotifyEnv,
): Promise<void> {
  for (const message of batch.messages) {
    try {
      const payload = mapQueueMessage(message.body);
      if (!payload) {
        message.ack();
        continue;
      }

      await notifyEvent(env, payload);
      message.ack();
    } catch (error) {
      console.error("Queue message failed", error);
      message.retry();
    }
  }
}
