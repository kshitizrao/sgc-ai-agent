# @sgc/agent-sdk

TypeScript SDK for integrating the Smart Garage AI Agent into your backend.

## Install

```bash
npm install @sgc/agent-sdk
```

## Usage

```typescript
import { SgcAgentClient } from "@sgc/agent-sdk";

const agent = new SgcAgentClient({
  baseUrl: "http://localhost:8000",
  apiKey: "dev-api-key-change-in-production",
});

const { sessionId } = await agent.createSession({
  customerId: "CUST-001",
  context: {
    customer: {
      vehicleMake: "Maruti Suzuki",
      vehicleModel: "Swift",
      fuelType: "Petrol",
    },
  },
});

const reply = await agent.chat({
  sessionId,
  message: "Do you have brake pads for 2018 Swift?",
});
console.log(reply.response);
```

## Direct Tool Invocation

```typescript
const result = await agent.invokeTool("search_parts", {
  query: "brake pad",
  make: "Maruti Suzuki",
  model: "Swift",
});
```
