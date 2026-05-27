/**
 * Graph workflow: DAG-based routing with conditional edges.
 * Classify input → route to specialized handler based on conditions.
 */

import type { Agent, AgentConfig, InvocationContext } from "@google/adk";
import { GraphAgent, Node, Edge, Condition } from "@google/adk/agent";

// ── Agent definitions ──────────────────────────────────────────────

const classifier: Agent = {
  name: "classifier",
  description: "Classifies input into 'technical', 'business', or 'general'",
  async run(ctx: InvocationContext) {
    const input = ctx.state.get("user_input") || "";
    // Simple heuristic — replace with LLM-based classification in production
    const techKeywords = ["code", "bug", "api", "deploy", "database"];
    const bizKeywords = ["revenue", "customer", "market", "strategy", "sales"];

    const isTech = techKeywords.some((k) => input.toLowerCase().includes(k));
    const isBiz = bizKeywords.some((k) => input.toLowerCase().includes(k));

    let category = "general";
    if (isTech && !isBiz) category = "technical";
    else if (isBiz && !isTech) category = "business";

    ctx.state.set("category", category);
    return {
      content: {
        role: "model",
        parts: [{ text: `Input classified as: ${category}` }],
      },
    };
  },
};

const technicalHandler: Agent = {
  name: "technical_handler",
  description: "Handles technical queries",
  async run(ctx: InvocationContext) {
    const input = ctx.state.get("user_input");
    return {
      content: {
        role: "model",
        parts: [{ text: `Technical analysis: ${input}` }],
      },
    };
  },
};

const businessHandler: Agent = {
  name: "business_handler",
  description: "Handles business queries",
  async run(ctx: InvocationContext) {
    const input = ctx.state.get("user_input");
    return {
      content: {
        role: "model",
        parts: [{ text: `Business analysis: ${input}` }],
      },
    };
  },
};

const generalHandler: Agent = {
  name: "general_handler",
  description: "Handles general queries",
  async run(ctx: InvocationContext) {
    const input = ctx.state.get("user_input");
    return {
      content: {
        role: "model",
        parts: [{ text: `General response: ${input}` }],
      },
    };
  },
};

// ── Routing condition ───────────────────────────────────────────────

function routeByCategory(state: Map<string, unknown>): string {
  const category = state.get("category") as string;
  switch (category) {
    case "technical":
      return "technical_handler";
    case "business":
      return "business_handler";
    default:
      return "general_handler";
  }
}

// ── Graph definition ────────────────────────────────────────────────

export const routerGraph = new GraphAgent({
  name: "router_workflow",
  description: "Classify input then route to specialized handler",
  nodes: [
    new Node({ name: "classifier", agent: classifier }),
    new Node({ name: "technical_handler", agent: technicalHandler }),
    new Node({ name: "business_handler", agent: businessHandler }),
    new Node({ name: "general_handler", agent: generalHandler }),
  ],
  edges: [
    new Edge({
      source: "classifier",
      target: new Condition({ fn: routeByCategory }),
    }),
  ],
});

export { classifier, technicalHandler, businessHandler, generalHandler };
