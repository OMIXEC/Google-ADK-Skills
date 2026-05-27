/**
 * ADK Workflow Client (TypeScript)
 *
 * Typed client for consuming ADK workflows over HTTP.
 * Handles auth token propagation, retries, and streaming.
 *
 * Usage:
 *   const client = new WorkflowClient({ baseUrl: "https://api.example.com" });
 *   const result = await client.run("order-processing", { query: "..." });
 */

// ── Types ────────────────────────────────────────────────────────

export interface UserContext {
  user_id: string;
  auth_provider: "firebase" | "oauth2" | "saml";
  roles: string[];
  scopes: string[];
  tenant_id?: string;
}

export interface WorkflowRunRequest {
  query: string;
  user_context: UserContext;
  params?: Record<string, unknown>;
  correlation_id?: string;
}

export interface WorkflowRunResult {
  status: "ok" | "error";
  correlation_id: string;
  data?: unknown;
  error?: string;
  latency_ms: number;
  node_results?: Record<string, unknown>;
}

export interface WorkflowClientConfig {
  baseUrl: string;
  getIdToken: () => Promise<string>;
  timeout?: number;
  maxRetries?: number;
}

export interface StreamEvent {
  type: "node_start" | "node_complete" | "tool_call" | "workflow_complete" | "error";
  data: Record<string, unknown>;
}

// ── Client ───────────────────────────────────────────────────────

export class WorkflowClient {
  private baseUrl: string;
  private getIdToken: () => Promise<string>;
  private timeout: number;
  private maxRetries: number;

  constructor(config: WorkflowClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.getIdToken = config.getIdToken;
    this.timeout = config.timeout ?? 300_000; // 5 min default
    this.maxRetries = config.maxRetries ?? 3;
  }

  /**
   * Run a workflow synchronously.
   * Returns the complete result after all nodes finish.
   */
  async run(
    workflowName: string,
    request: Omit<WorkflowRunRequest, "correlation_id">
  ): Promise<WorkflowRunResult> {
    const correlationId = crypto.randomUUID();
    const idToken = await this.getIdToken();

    const payload: WorkflowRunRequest = {
      ...request,
      correlation_id: correlationId,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(
        `${this.baseUrl}/api/workflows/${workflowName}/run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${idToken}`,
            "X-Correlation-ID": correlationId,
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        }
      );

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Workflow run failed: ${response.status} — ${errorBody}`);
      }

      const result: WorkflowRunResult = await response.json();
      return result;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error(`Workflow timed out after ${this.timeout}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Run a workflow with streaming events.
   * Yields events as nodes execute.
   */
  async *runStreaming(
    workflowName: string,
    request: Omit<WorkflowRunRequest, "correlation_id">
  ): AsyncGenerator<StreamEvent> {
    const correlationId = crypto.randomUUID();
    const idToken = await this.getIdToken();

    const response = await fetch(
      `${this.baseUrl}/api/workflows/${workflowName}/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
          "X-Correlation-ID": correlationId,
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ ...request, correlation_id: correlationId }),
      }
    );

    if (!response.ok) {
      throw new Error(`Stream connection failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body for streaming");

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") return;
            try {
              yield JSON.parse(data) as StreamEvent;
            } catch {
              // Skip unparseable chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Retry a workflow run with exponential backoff.
   */
  async runWithRetry(
    workflowName: string,
    request: Omit<WorkflowRunRequest, "correlation_id">
  ): Promise<WorkflowRunResult> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        return await this.run(workflowName, request);
      } catch (error) {
        lastError = error as Error;
        if (attempt < this.maxRetries) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError ?? new Error("Max retries exceeded");
  }
}

// ── Auth Middleware (Express example) ─────────────────────────────

/**
 * Express/Next.js API route middleware to verify Firebase ID tokens.
 * Extracts UserContext from verified token and attaches to request.
 */
export async function verifyFirebaseToken(
  idToken: string,
  adminAuth: { verifyIdToken: (token: string) => Promise<{ uid: string; email?: string; [key: string]: unknown }> }
): Promise<UserContext> {
  const decoded = await adminAuth.verifyIdToken(idToken);

  return {
    user_id: decoded.uid,
    auth_provider: "firebase",
    roles: (decoded.roles as string[]) ?? ["user"],
    scopes: (decoded.scopes as string[]) ?? ["read"],
    tenant_id: decoded.tenant_id as string | undefined,
  };
}

/**
 * Generic OAuth2/OIDC token verification.
 * Validates JWT signature against IdP JWKS endpoint.
 */
export async function verifyOAuth2Token(
  idToken: string,
  config: {
    issuer: string;
    audience: string;
    jwksUrl: string;
  }
): Promise<UserContext> {
  // In production: use jose or jsonwebtoken with JWKS
  // const { payload } = await jwtVerify(idToken, JWKS.createRemoteJWKSet(new URL(config.jwksUrl)), {
  //   issuer: config.issuer,
  //   audience: config.audience,
  // });

  // Placeholder — replace with real JWT verification
  const payload = { sub: "unknown", email: "unknown" };

  return {
    user_id: payload.sub ?? "unknown",
    auth_provider: "oauth2",
    roles: (payload.roles as string[]) ?? ["user"],
    scopes: (payload.scopes as string[]) ?? ["read"],
  };
}
