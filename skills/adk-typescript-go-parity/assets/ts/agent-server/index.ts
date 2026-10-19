/**
 * ADK Agent Server — TypeScript agent-side template.
 * Exposes agent via A2A protocol with AgentCard, auth middleware, and SSE transport.
 */

import { createAgent } from "./agent";
import { authMiddleware } from "./middleware";

const PORT = parseInt(process.env.PORT || "8080", 10);
const AGENT_NAME = process.env.AGENT_NAME || "ts-agent-server";
const AGENT_URL = process.env.AGENT_URL || `http://localhost:${PORT}/a2a/${AGENT_NAME}`;

// ── AgentCard — how other agents discover this agent ────────────────

const agentCard = {
  name: AGENT_NAME,
  description: "ADK Agent Server — handles queries with tools and auth",
  url: AGENT_URL,
  capabilities: {
    streaming: true,
    push_notifications: false,
  },
  auth_scheme: {
    type: "bearer",
    description: "Firebase Auth token or OAuth2 Bearer token",
  },
  version: "1.0.0",
  docs_url: `${AGENT_URL}/docs`,
  examples: [
    {
      query: "What is the weather in Tokyo?",
      response: "The weather in Tokyo is 22°C, partly cloudy.",
    },
  ],
};

// ── Server setup ─────────────────────────────────────────────────────

async function main() {
  const agent = createAgent(AGENT_NAME);

  console.log(`Agent: ${agent.name}`);
  console.log(`AgentCard URL: ${agentCard.url}`);
  console.log(`Capabilities: streaming=${agentCard.capabilities.streaming}`);

  // Mount A2A endpoint with auth middleware
  // Production: use Express/Fastify with ADK A2A server adapter
  console.log(`[${AGENT_NAME}] Ready on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`A2A endpoint: http://localhost:${PORT}/a2a/${AGENT_NAME}`);
}

main().catch(console.error);

export { agentCard, AGENT_NAME };
