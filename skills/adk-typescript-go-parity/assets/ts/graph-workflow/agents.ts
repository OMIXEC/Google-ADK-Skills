/**
 * Graph workflow: reusable agent factory functions.
 */

import type { Agent, InvocationContext } from "@google/adk";

export interface AgentFactoryConfig {
  name: string;
  description: string;
  instruction: string;
  model?: string;
}

/**
 * Create a simple LLM-backed agent for graph nodes.
 * Replace run() with actual LLM call in production.
 */
export function createGraphNodeAgent(config: AgentFactoryConfig): Agent {
  return {
    name: config.name,
    description: config.description,
    async run(ctx: InvocationContext) {
      return {
        content: {
          role: "model",
          parts: [{ text: `[${config.name}] Processing with instruction: ${config.instruction}` }],
        },
      };
    },
  };
}

/**
 * Create a classifier agent that categorizes input.
 */
export function createClassifier(categories: string[]): Agent {
  return {
    name: "classifier",
    description: `Classifies input into one of: ${categories.join(", ")}`,
    async run(ctx: InvocationContext) {
      const input = ctx.state.get("user_input") as string || "";
      // Production: use LLM to classify, not heuristic
      const category = categories[0]; // Placeholder
      ctx.state.set("category", category);
      return {
        content: {
          role: "model",
          parts: [{ text: `Classified as: ${category}` }],
        },
      };
    },
  };
}
