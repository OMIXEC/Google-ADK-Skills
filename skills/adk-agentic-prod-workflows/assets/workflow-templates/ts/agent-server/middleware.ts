/**
 * Auth middleware for ADK Agent Server.
 * Verifies Firebase Auth tokens and OAuth2 Bearer tokens.
 * Injects UserContext into agent invocation context.
 */

export interface UserContext {
  user_id: string;
  auth_provider: string;
  email?: string;
  roles: string[];
  tenant_id?: string;
  scopes: string[];
}

/**
 * Verify Firebase Auth token using Firebase Admin SDK.
 */
export async function verifyFirebaseToken(token: string): Promise<UserContext> {
  try {
    // Production: use firebase-admin SDK
    // import { getAuth } from "firebase-admin/auth";
    // const decoded = await getAuth().verifyIdToken(token, true);
    // return {
    //   user_id: decoded.uid,
    //   auth_provider: "firebase",
    //   email: decoded.email,
    //   roles: decoded.roles ?? ["user"],
    //   tenant_id: decoded.tenant_id,
    //   scopes: [],
    // };

    // Placeholder
    return {
      user_id: "user-from-token",
      auth_provider: "firebase",
      roles: ["user"],
      scopes: [],
    };
  } catch {
    throw new Error("Invalid Firebase token");
  }
}

/**
 * Verify OAuth2 Bearer token using JWKS.
 */
export async function verifyOAuth2Token(
  token: string,
  issuer: string,
  audience: string
): Promise<UserContext> {
  try {
    // Production: use jose library
    // import { jwtVerify, createRemoteJWKSet } from "jose";
    // const JWKS = createRemoteJWKSet(new URL(`${issuer}/.well-known/openid-configuration`));
    // const { payload } = await jwtVerify(token, JWKS, { issuer, audience });

    // Placeholder
    return {
      user_id: "oauth2-user",
      auth_provider: "oauth2",
      roles: ["user"],
      scopes: ["read"],
    };
  } catch {
    throw new Error("Invalid OAuth2 token");
  }
}

/**
 * Main auth middleware — auto-detects provider from token type.
 */
export async function authMiddleware(
  authorization: string,
  config?: { issuer?: string; audience?: string }
): Promise<UserContext> {
  if (!authorization || !authorization.startsWith("Bearer ")) {
    throw new Error("Missing or invalid Authorization header");
  }

  const token = authorization.slice(7);

  // Auto-detect provider
  // Firebase tokens: long, JWT format, issued by securetoken.google.com
  // OAuth2 tokens: JWT with 'iss' claim pointing to IdP

  try {
    // Try Firebase first (fastest — no JWKS fetch if using Admin SDK)
    if (process.env.FIREBASE_ENABLED === "true") {
      return await verifyFirebaseToken(token);
    }
  } catch {
    // Fall through to OAuth2
  }

  // Try OAuth2/OIDC
  if (config?.issuer) {
    return await verifyOAuth2Token(token, config.issuer, config.audience || "");
  }

  throw new Error("Token verification failed — no provider configured");
}

/**
 * CSP, HSTS, and security headers for agent server responses.
 */
export function securityHeaders(): Record<string, string> {
  return {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
  };
}
