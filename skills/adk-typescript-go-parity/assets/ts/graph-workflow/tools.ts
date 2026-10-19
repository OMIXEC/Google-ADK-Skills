/**
 * Graph workflow: tool definitions.
 */

import type { ToolContext } from "@google/adk";

/**
 * Tool to look up information from a knowledge base.
 */
export async function lookupInformation(
  query: string,
  ctx: ToolContext
): Promise<{ results: string[] }> {
  // Production: replace with actual DB/search call
  return {
    results: [`Result for query: ${query}`],
  };
}

/**
 * Tool to validate data against a schema.
 */
export async function validateData(
  data: Record<string, unknown>,
  schema: string,
  ctx: ToolContext
): Promise<{ valid: boolean; errors: string[] }> {
  // Production: replace with actual schema validation
  return { valid: true, errors: [] };
}
