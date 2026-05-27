# Identity & Database Integration for ADK Workflows

## Identity Architecture

```
[Client] ──Bearer <ID_TOKEN>──> [API Gateway] ──> [Auth Middleware] ──> [ADK Workflow]
                                       │                    │
                                       │            UserContext {
                                       │              user_id,
                                       │              auth_provider,
                                       │              roles,
                                       │              scopes,
                                       │              tenant_id?
                                       │            }
                                       │
                              [DB] ←──┘ (RLS keyed on user_id)
```

**Core principle:** Identity is external, stateless, and token-based. The ADK workflow never manages passwords, never stores auth state, and never infers user identity from request body.

## 1. Identity Model

### UserContext — Canonical Identity Struct

Every ADK workflow node receives this struct. It is injected by middleware — never constructed inside the workflow.

```python
from pydantic import BaseModel, Field
from typing import Optional

class UserContext(BaseModel):
    """Identity context injected by auth middleware into every workflow call."""
    user_id: str = Field(description="Stable user identifier (Firebase uid, OAuth sub, SAML nameID)")
    auth_provider: str = Field(description="firebase | oauth2 | saml")
    email: Optional[str] = Field(default=None, description="User email from verified token")
    roles: list[str] = Field(default_factory=lambda: ["user"])
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    tenant_id: Optional[str] = Field(default=None, description="Multi-tenant context")
```

```go
type UserContext struct {
    UserID       string   `json:"user_id"`
    AuthProvider string   `json:"auth_provider"` // firebase, oauth2, saml
    Email        string   `json:"email,omitempty"`
    Roles        []string `json:"roles"`
    Scopes       []string `json:"scopes"`
    TenantID     string   `json:"tenant_id,omitempty"`
}
```

```typescript
interface UserContext {
  user_id: string;
  auth_provider: "firebase" | "oauth2" | "saml";
  email?: string;
  roles: string[];
  scopes: string[];
  tenant_id?: string;
}
```

### Preferred Identity Providers

| Provider | Token Type | Verification | When to Use |
|----------|-----------|-------------|-------------|
| Firebase Auth | ID Token (JWT) | `firebase-admin` SDK | Default. Email/password + federated. |
| OAuth2/OIDC | Access/ID Token (JWT) | JWKS endpoint | Enterprise SSO, Google, GitHub, Microsoft |
| SAML | Assertion → JWT bridge | IdP proxy or gateway | Legacy enterprise IdPs |

### Stateless Authentication Handshake

```
1. Client (Flutter/web/mobile/CLI)
   → Authenticates with Firebase or IdP directly
   → Obtains short-lived ID token / JWT

2. Transport
   → Every request: Authorization: Bearer <ID_TOKEN>
   → X-Correlation-ID header for tracing

3. Backend (Python/Go/TS)
   → Middleware verifies signature, issuer, audience, expiry
   → Extracts stable subject key:
     • Firebase: uid
     • OAuth/SAML: sub / nameID → internal user_id
   → Injects UserContext into request/context

4. ADK Workflow
   → Receives UserContext from middleware
   → All tools receive user_id (and tenant_id) explicitly
   → No implicit identity inference
```

## 2. Auth Middleware — Language-Specific Patterns

### Python (FastAPI / Starlette)

```python
# middleware/auth.py
from fastapi import Request, HTTPException, Depends
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, initialize_app
from jose import jwt, JWTError
from pydantic import BaseModel
import os
from typing import Optional

# Firebase init (one-time)
cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"))
initialize_app(cred)

class UserContext(BaseModel):
    user_id: str
    auth_provider: str
    email: Optional[str] = None
    roles: list[str] = ["user"]
    scopes: list[str] = ["read"]
    tenant_id: Optional[str] = None

async def verify_firebase_token(authorization: str) -> UserContext:
    """Verify Firebase ID token and extract UserContext."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=True)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")

    return UserContext(
        user_id=decoded["uid"],
        auth_provider="firebase",
        email=decoded.get("email"),
        roles=decoded.get("roles", ["user"]),
        scopes=decoded.get("scopes", ["read"]),
        tenant_id=decoded.get("tenant_id"),
    )

async def verify_oauth2_token(
    authorization: str,
    issuer: str,
    audience: str,
    jwks_url: str,
) -> UserContext:
    """Verify generic OAuth2/OIDC JWT against IdP JWKS."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        # Fetch JWKS and verify
        from jose import jwk, jwt
        # In production: cache JWKS, handle key rotation
        payload = jwt.decode(
            token,
            key=None,  # Replace with JWKS fetch: jwk.construct(jwks_data)
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"JWT verification failed: {e}")

    return UserContext(
        user_id=payload.get("sub", "unknown"),
        auth_provider="oauth2",
        email=payload.get("email"),
        roles=payload.get("roles", ["user"]),
        scopes=payload.get("scope", "read").split(),
        tenant_id=payload.get("tenant_id"),
    )

# FastAPI dependency
async def get_user_context(request: Request) -> UserContext:
    """FastAPI dependency: extract UserContext from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    provider = request.headers.get("X-Auth-Provider", "firebase")

    if provider == "firebase":
        return await verify_firebase_token(auth_header)
    elif provider == "oauth2":
        return await verify_oauth2_token(
            auth_header,
            issuer=os.getenv("OIDC_ISSUER", ""),
            audience=os.getenv("OIDC_AUDIENCE", ""),
            jwks_url=os.getenv("OIDC_JWKS_URL", ""),
        )
    else:
        raise HTTPException(status_code=401, detail=f"Unsupported auth provider: {provider}")


# ADK workflow entrypoint with identity
from google.adk.runners import InProcessRunner

async def run_workflow_with_identity(
    workflow_agent,
    query: str,
    user_ctx: UserContext,
) -> dict:
    """Run ADK workflow with identity context injected."""
    runner = InProcessRunner(agent=workflow_agent)
    result = await runner.run(
        query=query,
        # UserContext passed via session state — accessed by all nodes
        session_state={"user_context": user_ctx.model_dump()},
    )
    return result
```

### Go (Echo / chi / net/http)

```go
// middleware/auth.go
package middleware

import (
    "context"
    "net/http"
    "os"
    "strings"

    firebase "firebase.google.com/go/v4/auth"
    "github.com/lestrrat-go/jwx/v2/jwk"
    "github.com/lestrrat-go/jwx/v2/jwt"
)

type contextKey string

const UserContextKey contextKey = "user_context"

type UserContext struct {
    UserID       string   `json:"user_id"`
    AuthProvider string   `json:"auth_provider"`
    Email        string   `json:"email,omitempty"`
    Roles        []string `json:"roles"`
    Scopes       []string `json:"scopes"`
    TenantID     string   `json:"tenant_id,omitempty"`
}

func GetUserContext(ctx context.Context) (UserContext, bool) {
    uc, ok := ctx.Value(UserContextKey).(UserContext)
    return uc, ok
}

// FirebaseMiddleware verifies Firebase ID tokens from Authorization header.
func FirebaseMiddleware(firebaseAuth *firebase.Client) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
                http.Error(w, `{"error":"missing Authorization header"}`, http.StatusUnauthorized)
                return
            }

            idToken := strings.TrimPrefix(authHeader, "Bearer ")
            token, err := firebaseAuth.VerifyIDToken(r.Context(), idToken)
            if err != nil {
                http.Error(w, `{"error":"invalid token"}`, http.StatusUnauthorized)
                return
            }

            roles := []string{"user"}
            if r, ok := token.Claims["roles"].([]interface{}); ok {
                for _, v := range r {
                    if s, ok := v.(string); ok {
                        roles = append(roles, s)
                    }
                }
            }

            uc := UserContext{
                UserID:       token.UID,
                AuthProvider: "firebase",
                Email:        token.Claims["email"].(string),
                Roles:        roles,
                Scopes:       []string{"read"},
            }
            if tid, ok := token.Claims["tenant_id"].(string); ok {
                uc.TenantID = tid
            }

            ctx := context.WithValue(r.Context(), UserContextKey, uc)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// OAuth2Middleware verifies generic OAuth2/OIDC JWTs.
func OAuth2Middleware(issuer, audience, jwksURL string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
                http.Error(w, `{"error":"missing Authorization header"}`, http.StatusUnauthorized)
                return
            }

            idToken := strings.TrimPrefix(authHeader, "Bearer ")

            // Fetch JWKS and verify
            keySet, err := jwk.Fetch(r.Context(), jwksURL)
            if err != nil {
                http.Error(w, `{"error":"jwks fetch failed"}`, http.StatusUnauthorized)
                return
            }

            parsed, err := jwt.Parse([]byte(idToken),
                jwt.WithKeySet(keySet),
                jwt.WithAudience(audience),
                jwt.WithIssuer(issuer),
            )
            if err != nil {
                http.Error(w, `{"error":"token verification failed"}`, http.StatusUnauthorized)
                return
            }

            uc := UserContext{
                UserID:       parsed.Subject(),
                AuthProvider: "oauth2",
                Roles:        []string{"user"},
                Scopes:       []string{"read"},
            }

            ctx := context.WithValue(r.Context(), UserContextKey, uc)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}
```

### TypeScript (Express / Next.js / Cloud Functions)

```typescript
// middleware/auth.ts
import { Request, Response, NextFunction } from "express";
import { getAuth } from "firebase-admin/auth";
import { jwtVerify, createRemoteJWKSet } from "jose";
import type { UserContext } from "../types";

// Extend Express Request to carry UserContext
declare global {
  namespace Express {
    interface Request {
      userContext?: UserContext;
    }
  }
}

/**
 * Express middleware: verify Firebase ID token.
 * Attaches UserContext to req.userContext.
 */
export function firebaseAuthMiddleware() {
  return async (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Missing Authorization header" });
    }

    const idToken = authHeader.slice(7);

    try {
      const decoded = await getAuth().verifyIdToken(idToken, true);

      req.userContext = {
        user_id: decoded.uid,
        auth_provider: "firebase",
        email: decoded.email,
        roles: (decoded.roles as string[]) ?? ["user"],
        scopes: (decoded.scopes as string[]) ?? ["read"],
        tenant_id: decoded.tenant_id as string | undefined,
      };

      next();
    } catch (error) {
      return res.status(401).json({ error: "Invalid token", detail: String(error) });
    }
  };
}

/**
 * Express middleware: verify OAuth2/OIDC JWT against IdP JWKS.
 */
export function oauth2AuthMiddleware(config: {
  issuer: string;
  audience: string;
  jwksUrl: string;
}) {
  const JWKS = createRemoteJWKSet(new URL(config.jwksUrl));

  return async (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Missing Authorization header" });
    }

    const idToken = authHeader.slice(7);

    try {
      const { payload } = await jwtVerify(idToken, JWKS, {
        issuer: config.issuer,
        audience: config.audience,
      });

      req.userContext = {
        user_id: (payload.sub as string) ?? "unknown",
        auth_provider: "oauth2",
        email: payload.email as string | undefined,
        roles: (payload.roles as string[]) ?? ["user"],
        scopes: ((payload.scope as string) ?? "read").split(" "),
        tenant_id: payload.tenant_id as string | undefined,
      };

      next();
    } catch (error) {
      return res.status(401).json({ error: "Token verification failed", detail: String(error) });
    }
  };
}

/**
 * Next.js API route wrapper: extract UserContext.
 */
export function withAuth(handler: (req: Request, res: Response, ctx: UserContext) => Promise<void>) {
  return async (req: Request, res: Response) => {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Missing Authorization header" });
    }

    try {
      const decoded = await getAuth().verifyIdToken(authHeader.slice(7), true);

      const ctx: UserContext = {
        user_id: decoded.uid,
        auth_provider: "firebase",
        roles: (decoded.roles as string[]) ?? ["user"],
        scopes: (decoded.scopes as string[]) ?? ["read"],
      };

      await handler(req, res, ctx);
    } catch (error) {
      return res.status(401).json({ error: "Invalid token" });
    }
  };
}
```

## 3. Database Integration Patterns

**Rule:** Every DB integration follows "JWT → backend verifies → DB enforces row-level access." All queries are parameterized. No connection strings or service accounts committed to source.

### Supabase

**Treat as:** Postgres + Row Level Security (RLS) + JWT-based auth.

**Recommended mode:** Backend-mediated access. The ADK backend uses the Supabase client (or standard Postgres driver) with service role. RLS and query-layer filters enforce tenant/user isolation.

```python
# db/supabase.py
from supabase import create_client, Client
import os

# Service role client — backend only, never exposed to frontend
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),  # service_role, not anon
)

def get_user_orders(user_id: str, tenant_id: str | None = None) -> list[dict]:
    """Fetch orders scoped to user. RLS + explicit user_id filter."""
    query = supabase.table("orders").select("*").eq("user_id", user_id)
    if tenant_id:
        query = query.eq("tenant_id", tenant_id)
    result = query.execute()
    return result.data

def insert_order(user_id: str, order_data: dict) -> dict:
    """Insert order with explicit user_id. RLS validates on write."""
    order_data["user_id"] = user_id
    result = supabase.table("orders").insert(order_data).execute()
    return result.data[0]
```

**Supabase RLS policies (SQL):**

```sql
-- Enable RLS on multi-tenant tables
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Users can only read their own orders
CREATE POLICY "users_read_own_orders" ON orders
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only insert their own orders
CREATE POLICY "users_insert_own_orders" ON orders
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Tenant isolation for multi-tenant apps
CREATE POLICY "tenant_isolation" ON orders
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true));
```

**Supabase rules for the meta-skill:**

- Never expose `service_role` key to frontend
- Enable RLS on every multi-tenant table
- Use `anon` key only for non-critical reads; `service_role` for trusted backend operations
- Store Supabase URL and keys in environment/secret manager
- Enable `row level security` on tables before any data ingestion

### Neon (Serverless Postgres)

**Treat as:** Postgres with branching. Same RLS patterns as Supabase.

```python
# db/neon.py
import psycopg2
import psycopg2.extras
import os

def get_neon_connection():
    """Create connection to Neon. Connection string from env — never committed."""
    return psycopg2.connect(
        os.getenv("NEON_DATABASE_URL"),
        sslmode="require",
        connect_timeout=10,
    )

def query_user_data(user_id: str, query: str, params: tuple = ()) -> list[dict]:
    """Parameterized query scoped to user_id."""
    conn = get_neon_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"{query} AND user_id = %s",  # Always append user_id filter
                params + (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()
```

**Neon RLS setup (SQL):**

```sql
-- Enable RLS on multi-tenant tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Users see only their documents within their tenant
CREATE POLICY "user_tenant_documents" ON documents
    FOR ALL
    USING (user_id = current_setting('app.user_id') AND tenant_id = current_setting('app.tenant_id'));

-- Set runtime variables per session
-- Backend runs: SET app.user_id = '<user_id>'; SET app.tenant_id = '<tenant_id>';
```

**Neon rules for the meta-skill:**

- Connection strings in secret manager — never in code or config files
- TLS enforced: `sslmode=require`
- RLS enabled on all multi-tenant tables, keyed on `user_id` / `tenant_id`
- Use per-branch connection strings for dev/staging/prod
- Optionally configure IP allowlist for backend runtime

### Convex

**Treat as:** Serverless DB/runtime with its own auth hooking.

```typescript
// convex/auth.ts — Auth integration layer
import { query, mutation, QueryCtx, MutationCtx } from "./_generated/server";

export interface ConvexUserContext {
  user_id: string;
  auth_provider: string;
  roles: string[];
  tenant_id?: string;
}

/**
 * Extract UserContext from Convex auth identity.
 * Convex auth is configured to accept Firebase/OAuth2 tokens.
 */
export async function getUserContext(ctx: QueryCtx | MutationCtx): Promise<ConvexUserContext> {
  const identity = await ctx.auth.getUserIdentity();

  if (!identity) {
    throw new Error("Unauthenticated — no identity found");
  }

  // identity.subject maps to Firebase uid or OAuth sub
  return {
    user_id: identity.subject,
    auth_provider: identity.issuer.includes("firebase") ? "firebase" : "oauth2",
    roles: (identity.claims?.roles as string[]) ?? ["user"],
    tenant_id: identity.claims?.tenant_id as string | undefined,
  };
}

// Example: user-scoped query
export const getUserOrders = query({
  args: {},
  handler: async (ctx) => {
    const user = await getUserContext(ctx);
    return await ctx.db
      .query("orders")
      .withIndex("by_user_id", (q) => q.eq("user_id", user.user_id))
      .collect();
  },
});

// Example: user-scoped mutation
export const createOrder = mutation({
  args: { order: { /* ... */ } },
  handler: async (ctx, args) => {
    const user = await getUserContext(ctx);

    return await ctx.db.insert("orders", {
      ...args.order,
      user_id: user.user_id,
      tenant_id: user.tenant_id,
      created_at: Date.now(),
    });
  },
});
```

**Convex rules for the meta-skill:**

- All data access functions take `UserContext` and enforce filters server-side
- Use Convex's built-in auth system configured to accept Firebase/OAuth2 tokens
- Index on `user_id` for queries; compound index on `(tenant_id, user_id)` for multi-tenant
- No user data queries without identity check
- Schema enforces `user_id` field on all user-data tables

## 4. Firebase Production Configuration

### Project Setup

```
Dev project:    my-app-dev    (firebase.google.com)
Prod project:   my-app-prod   (separate — no config sharing)
```

### Firebase Admin SDK (Backend)

```python
import os
import json
from firebase_admin import credentials, initialize_app

# Option A: Service account JSON from env (CI/CD friendly)
service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if service_account_json:
    cred = credentials.Certificate(json.loads(service_account_json))
else:
    # Option B: File path (local dev only)
    cred = credentials.Certificate("service_account.json")

initialize_app(cred)
```

### Firebase Client SDK (Frontend — NOT in backend)

```typescript
// Client-side only. Never use this pattern in backend.
import { initializeApp } from "firebase/app";
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";

const app = initializeApp({
  apiKey: "YOUR_API_KEY",     // OK to be public
  authDomain: "my-app.firebaseapp.com",
  projectId: "my-app-prod",
});

const auth = getAuth(app);
// Client signs in and gets ID token: await signInWithEmailAndPassword(auth, email, password)
// Token sent to backend via Authorization header
```

### Firestore / RTDB Security Rules

```javascript
// Firestore rules — enforce user-scoped access
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // User profile: only the user can read/write their own
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Orders: user can only access their own orders
    match /orders/{orderId} {
      allow read, write: if request.auth != null
        && request.auth.uid == resource.data.user_id;
    }

    // Multi-tenant: enforce tenant_id match
    match /tenants/{tenantId}/data/{docId} {
      allow read, write: if request.auth != null
        && request.auth.token.tenant_id == tenantId;
    }
  }
}
```

### Firebase Best Practices

- Separate dev and prod Firebase projects — never share configs
- Backend uses Firebase Admin SDK with `service_account.json` (env-based in CI/CD)
- Client uses Firebase Client SDK (never Admin SDK)
- Short-lived ID tokens + periodic refresh (client SDK handles this)
- Use Emulator Suite for local development: `firebase emulators:start`
- Firestore rules enforce `request.auth.uid == userId` on all user-data paths
- Enable Firebase Auth email enumeration protection in production

## 5. OAuth2 / SAML Integration

### OAuth2 / OIDC Configuration

```python
# config/oauth2.py — per-IdP configuration
from pydantic import BaseModel

class OIDCConfig(BaseModel):
    issuer: str          # e.g., "https://accounts.google.com"
    audience: str        # OAuth2 client ID
    jwks_url: str        # e.g., "https://www.googleapis.com/oauth2/v3/certs"
    user_id_claim: str = "sub"
    email_claim: str = "email"
    roles_claim: str = "roles"
    tenant_id_claim: str | None = None

# Multi-IdP configuration
IDP_CONFIGS = {
    "google": OIDCConfig(
        issuer="https://accounts.google.com",
        audience=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        jwks_url="https://www.googleapis.com/oauth2/v3/certs",
    ),
    "azure": OIDCConfig(
        issuer=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/v2.0",
        audience=os.getenv("AZURE_CLIENT_ID"),
        jwks_url=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/discovery/v2.0/keys",
        user_id_claim="oid",
        tenant_id_claim="tid",
    ),
    "custom": OIDCConfig(
        issuer=os.getenv("OIDC_ISSUER", ""),
        audience=os.getenv("OIDC_AUDIENCE", ""),
        jwks_url=os.getenv("OIDC_JWKS_URL", ""),
    ),
}
```

### SAML → JWT Bridge

SAML assertions are NOT natively consumable by ADK workflows. They must be exchanged for a JWT by an IdP proxy or gateway before reaching the backend.

```
[SAML IdP] → SAML Assertion → [Auth Gateway / Proxy]
                                   │
                          Exchanges SAML for JWT/session
                                   │
                          ┌────────┘
                          ▼
                    [ADK Backend]
                    (sees only JWT — never SAML)
```

The meta-skill assumes SAML is converted upstream. If the user asks about SAML, generate the auth gateway config, not in-workflow SAML parsing.

## 6. Workflow Node Identity Injection

Every ADK workflow node must receive identity context. Tools must take `user_id` explicitly.

```python
# app/workflow.py — identity-aware workflow

from google.adk import Agent
from google.adk.agents.graph import GraphAgent, Node, Edge, Condition
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from .context import UserContext
from .db import get_user_orders, insert_order

class FetchOrdersParams(BaseModel):
    user_id: str = Field(description="User ID from verified auth token")
    limit: int = Field(default=50)

class FetchOrdersResult(BaseModel):
    orders: list[dict]
    user_id: str

def fetch_orders(params: FetchOrdersParams) -> FetchOrdersResult:
    """Fetch orders scoped to user_id. user_id comes from UserContext, never inferred."""
    orders = get_user_orders(params.user_id, limit=params.limit)
    return FetchOrdersResult(orders=orders, user_id=params.user_id)

# Agent instructions enforce identity-aware behavior
order_agent = Agent(
    name="order_fetcher",
    model="gemini-2.5-flash",
    instruction="""You fetch orders for authenticated users.
    The user_id is available in session.state['user_context']['user_id'].
    ALWAYS pass user_id to tools — never guess or infer identity.""",
    tools=[FunctionTool(fetch_orders)],
)
```

## 7. Web Security Headers

Every API gateway / frontend must configure security headers:

```python
# middleware/security.py — FastAPI security headers middleware
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' https://*.googleapis.com; "
            "frame-ancestors 'none'"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        return response

# Apply to FastAPI app
app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

```go
// middleware/security.go — Go security headers middleware
func SecurityHeadersMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Security-Policy",
            "default-src 'self'; script-src 'self'; frame-ancestors 'none'")
        w.Header().Set("Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload")
        w.Header().Set("X-Content-Type-Options", "nosniff")
        w.Header().Set("X-Frame-Options", "DENY")
        w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
        w.Header().Set("Permissions-Policy",
            "camera=(), microphone=(), geolocation=()")
        next.ServeHTTP(w, r)
    })
}
```

## 8. Identity & Security Checklist

### Auth & Tokens

- [ ] No ID token, service key, or secret exposed on frontend
- [ ] All API endpoints require valid JWT (enforced by middleware)
- [ ] Token expiry checked on every request
- [ ] Token audience (`aud`) validated against expected value
- [ ] Token issuer (`iss`) validated against trusted IdPs
- [ ] HMAC/RSA key rotation handled (JWKS cache with TTL)
- [ ] Firebase Auth: `check_revoked=True` on `verify_id_token`

### DB Access

- [ ] RLS or equivalent per-tenant isolation enabled on all DBs
- [ ] All queries parameterized — never string interpolation
- [ ] `user_id` explicitly passed to every DB query (never inferred)
- [ ] Service role keys never exposed to frontend
- [ ] Supabase: `anon` key for non-critical reads only
- [ ] Neon: TLS enforced (`sslmode=require`)
- [ ] Convex: all data access functions verify identity first

### Secrets & Config

- [ ] No connection strings, API keys, or service accounts committed to source
- [ ] All secrets via environment or secret manager (GCP Secret Manager, Vault, etc.)
- [ ] `.env` and `service_account.json` in `.gitignore`
- [ ] CI/CD pipelines inject secrets via platform secret store
- [ ] Separate credentials for dev, staging, and prod environments

### Transport & Headers

- [ ] HTTPS enforced end-to-end (HSTS preload)
- [ ] Content-Security-Policy configured
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] CORS configured to specific allowed origins (not `*`)
- [ ] API gateway enforces rate limiting per user_id

### Multi-Tenant Isolation

- [ ] `tenant_id` propagated from UserContext to all DB queries
- [ ] RLS policies include `tenant_id` check
- [ ] Cross-tenant data access impossible at DB level (RLS enforces)
- [ ] Tenant ID validated against authenticated user's tenant membership

### Workflow-Level

- [ ] Every workflow node receives `UserContext` from middleware
- [ ] Tools accept `user_id` as explicit parameter (never inferred)
- [ ] Agent instructions explicitly prohibit identity guessing
- [ ] Correlation ID propagated through all nodes (never contains PII)
- [ ] Workflow errors logged without leaking tokens or PII
