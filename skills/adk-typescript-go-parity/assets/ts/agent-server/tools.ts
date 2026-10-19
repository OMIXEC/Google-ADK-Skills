/**
 * Tool definitions for ADK Agent Server.
 * Each tool has a clear signature, parameter schema, and error handling.
 */

import type { ToolContext } from "@google/adk";

/**
 * Search internal knowledge base.
 * Production: replace with actual vector DB or RAG pipeline.
 */
export async function searchKnowledgeBase(
  query: string,
  topK: number = 5,
  ctx?: ToolContext
): Promise<{ results: Array<{ title: string; content: string; score: number }> }> {
  // Parameterized — never interpolate user input directly
  const sanitizedQuery = query.trim().slice(0, 500);

  // Placeholder — replace with actual search
  return {
    results: [
      {
        title: `Result for: ${sanitizedQuery}`,
        content: "Relevant information found in knowledge base.",
        score: 0.92,
      },
    ],
  };
}

/**
 * Fetch data from external API.
 * Production: replace with actual HTTP client call.
 */
export async function fetchExternalData(
  endpoint: string,
  params?: Record<string, string>,
  ctx?: ToolContext
): Promise<{ status: number; data: unknown }> {
  // Validate endpoint
  const allowedEndpoints = ["weather", "news", "stocks"];
  const base = endpoint.split("/")[0];
  if (!allowedEndpoints.includes(base)) {
    throw new Error(`Endpoint '${base}' not allowed. Allowed: ${allowedEndpoints.join(", ")}`);
  }

  // Placeholder — replace with actual HTTP call
  return {
    status: 200,
    data: { endpoint, params, result: "Data fetched successfully" },
  };
}

/**
 * Quality gate tool — call when output meets requirements.
 * Escalates the event to signal loop completion.
 */
export async function qualityGate(
  score: number,
  threshold: number = 0.8,
  ctx?: ToolContext
): Promise<{ passed: boolean; score: number; threshold: number }> {
  const passed = score >= threshold;
  if (passed && ctx) {
    ctx.actions.escalate = true;
  }
  return { passed, score, threshold };
}
