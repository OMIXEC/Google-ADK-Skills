/**
 * Agent definition for ADK Agent Server.
 * Configures LlmAgent with tools, instructions, and output schema.
 */

import type { Agent, InvocationContext } from "@google/adk";
import { searchKnowledgeBase, fetchExternalData } from "./tools";

export interface AgentOutput {
  answer: string;
  confidence: number;
  sources: string[];
}

export function createAgent(name: string): Agent {
  return {
    name,
    description: "General-purpose agent with knowledge base and external API tools",
    instruction: `You are a helpful assistant. Use tools when you need specific information.
1. Use searchKnowledgeBase for internal information.
2. Use fetchExternalData for external API calls.
3. Always cite sources in your response.
4. Be concise but thorough.`,

    tools: [searchKnowledgeBase, fetchExternalData],

    async run(ctx: InvocationContext) {
      const userInput = ctx.state.get("user_input") as string || "";

      return {
        content: {
          role: "model",
          parts: [{ text: `Processed: ${userInput}` }],
        },
      };
    },
  };
}
