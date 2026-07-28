export interface CustomerContext {
  customerId?: string;
  vehicleId?: string;
  vehicleMake?: string;
  vehicleModel?: string;
  vehicleVariant?: string;
  fuelType?: string;
  registrationNo?: string;
  mileageKm?: number;
  vehicleAgeMonths?: number;
  locale?: string;
}

export interface LocationContext {
  latitude?: number;
  longitude?: number;
  area?: string;
}

export interface ContextEnvelope {
  customer?: CustomerContext;
  location?: LocationContext;
  garageId?: string;
  metadata?: Record<string, string>;
}

export interface ChatRequest {
  sessionId: string;
  message: string;
  context?: ContextEnvelope;
}

export interface ChatResponse {
  sessionId: string;
  response: string;
  intent?: string;
  sourceRefs?: Array<{ table: string; recordId: string }>;
  requiresHumanReview?: boolean;
  modelUsed?: string;
}

export interface SgcAgentClientOptions {
  baseUrl: string;
  apiKey: string;
}

function toSnakeContext(ctx?: ContextEnvelope): Record<string, unknown> | undefined {
  if (!ctx) return undefined;
  return {
    customer: ctx.customer
      ? {
          customer_id: ctx.customer.customerId,
          vehicle_id: ctx.customer.vehicleId,
          vehicle_make: ctx.customer.vehicleMake,
          vehicle_model: ctx.customer.vehicleModel,
          vehicle_variant: ctx.customer.vehicleVariant,
          fuel_type: ctx.customer.fuelType,
          registration_no: ctx.customer.registrationNo,
          mileage_km: ctx.customer.mileageKm,
          vehicle_age_months: ctx.customer.vehicleAgeMonths,
          locale: ctx.customer.locale,
        }
      : undefined,
    location: ctx.location
      ? {
          latitude: ctx.location.latitude,
          longitude: ctx.location.longitude,
          area: ctx.location.area,
        }
      : undefined,
    garage_id: ctx.garageId,
    metadata: ctx.metadata,
  };
}

function fromSnakeChatResponse(data: Record<string, unknown>): ChatResponse {
  return {
    sessionId: data.session_id as string,
    response: data.response as string,
    intent: data.intent as string | undefined,
    sourceRefs: data.source_refs as ChatResponse["sourceRefs"],
    requiresHumanReview: data.requires_human_review as boolean | undefined,
    modelUsed: data.model_used as string | undefined,
  };
}

export class SgcAgentClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(options: SgcAgentClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.apiKey = options.apiKey;
  }

  private headers(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-API-Key": this.apiKey,
    };
  }

  async createSession(options?: {
    customerId?: string;
    vehicleId?: string;
    context?: ContextEnvelope;
  }): Promise<{ sessionId: string }> {
    const res = await fetch(`${this.baseUrl}/v1/sessions`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        customer_id: options?.customerId,
        vehicle_id: options?.vehicleId,
        context: toSnakeContext(options?.context),
      }),
    });
    if (!res.ok) throw new Error(`Session creation failed: ${res.status}`);
    const data = (await res.json()) as { session_id: string };
    return { sessionId: data.session_id };
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.baseUrl}/v1/chat`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        session_id: request.sessionId,
        message: request.message,
        context: toSnakeContext(request.context),
      }),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
    const data = (await res.json()) as Record<string, unknown>;
    return fromSnakeChatResponse(data);
  }

  async invokeTool(
    toolName: string,
    parameters: Record<string, unknown> = {},
    sessionId?: string
  ): Promise<{ success: boolean; data: unknown; error?: string }> {
    const res = await fetch(`${this.baseUrl}/v1/tools/invoke`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({
        tool_name: toolName,
        parameters,
        session_id: sessionId,
      }),
    });
    if (!res.ok) throw new Error(`Tool invoke failed: ${res.status}`);
    return (await res.json()) as { success: boolean; data: unknown; error?: string };
  }

  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    return (await res.json()) as { status: string };
  }
}

export { streamChat } from "./streaming";
