import type { ChatRequest, ContextEnvelope } from "./client";

export interface StreamEvent {
  type: "token" | "done" | "error";
  content?: string;
  intent?: string;
  sourceRefs?: Array<{ table: string; recordId: string }>;
  message?: string;
}

function toSnakeContext(ctx?: ContextEnvelope): Record<string, unknown> | undefined {
  if (!ctx) return undefined;
  return {
    customer: ctx.customer
      ? {
          customer_id: ctx.customer.customerId,
          vehicle_make: ctx.customer.vehicleMake,
          vehicle_model: ctx.customer.vehicleModel,
          fuel_type: ctx.customer.fuelType,
        }
      : undefined,
    location: ctx.location,
  };
}

export async function* streamChat(
  baseUrl: string,
  apiKey: string,
  request: ChatRequest
): AsyncGenerator<StreamEvent> {
  const wsUrl = baseUrl.replace(/^http/, "ws") + "/v1/chat/stream";
  const ws = new WebSocket(wsUrl, { headers: { "X-API-Key": apiKey } } as unknown as string[]);

  await new Promise<void>((resolve, reject) => {
    ws.onopen = () => resolve();
    ws.onerror = () => reject(new Error("WebSocket connection failed"));
  });

  ws.send(
    JSON.stringify({
      session_id: request.sessionId,
      message: request.message,
      context: toSnakeContext(request.context),
    })
  );

  const queue: StreamEvent[] = [];
  let done = false;

  ws.onmessage = (event) => {
    queue.push(JSON.parse(event.data as string) as StreamEvent);
  };
  ws.onclose = () => {
    done = true;
  };

  while (!done || queue.length > 0) {
    if (queue.length > 0) {
      yield queue.shift()!;
    } else {
      await new Promise((r) => setTimeout(r, 50));
    }
  }
}
