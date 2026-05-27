# Authentication & Identity Providers for ADK Workflows

All identity flows follow the same pattern: Client authenticates with IdP → obtains JWT → sends `Authorization: Bearer <token>` → Backend middleware verifies → injects `UserContext`.

## Provider Selection Matrix

| Provider | Protocol | When to Use | Verification | Multi-Tenant |
|----------|----------|-------------|-------------|-------------|
| Firebase Auth | Custom JWT | Mobile-first, email/password, federated | `firebase-admin` SDK | `tenant_id` in token |
| Google Identity | OAuth2/OIDC | G Suite, consumer Google accounts | JWKS (`accounts.google.com`) | `hd` claim (domain) |
| GitHub | OAuth2 | Developer tools, open-source | `github.com` API + OAuth2 | Organization membership |
| Microsoft Entra ID | OAuth2/OIDC + SAML | Enterprise, Office 365 | JWKS (`login.microsoftonline.com`) | `tid` claim |
| Apple Sign In | OAuth2/OIDC | iOS/macOS apps | JWKS (`appleid.apple.com`) | — |
| Auth0 | OAuth2/OIDC | Universal, multi-IdP gateway | JWKS (per-tenant) | `tenant` in custom claims |
| Okta | OAuth2/OIDC + SAML | Enterprise SSO | JWKS (per-org) | `org` claim |
| Keycloak | OAuth2/OIDC + SAML | Self-hosted, open-source | JWKS (per-realm) | Realm-scoped |
| Ping Identity | OAuth2/OIDC + SAML | Enterprise, legacy | JWKS (per-env) | Population-based |
| Cognito | OAuth2/OIDC + SAML | AWS-native, mobile/web | JWKS (per-pool) | User pool ID |
| Custom OIDC | OAuth2/OIDC | Any OIDC-compliant IdP | `.well-known/openid-configuration` | Custom claims |

## Universal Token Verification

```python
"""Provider-agnostic JWT verification via .well-known/openid-configuration."""

from jose import jwt, JWTError
from jose.jwk import JWKSet
import httpx
from pydantic import BaseModel
from typing import Optional

class OIDCDiscovery(BaseModel):
    issuer: str
    jwks_uri: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: Optional[str] = None

async def discover_oidc(issuer: str) -> OIDCDiscovery:
    """Fetch OIDC discovery document from any compliant IdP."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{issuer.rstrip('/')}/.well-known/openid-configuration")
        resp.raise_for_status()
        return OIDCDiscovery(**resp.json())

async def verify_oidc_token(token: str, issuer: str, audience: str) -> dict:
    """Verify any OIDC token using discovered JWKS."""
    discovery = await discover_oidc(issuer)
    jwks = JWKSet.from_json(
        httpx.get(discovery.jwks_uri).text
    )
    payload = jwt.decode(
        token,
        jwks.to_dict(),
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
    )
    return payload
```

## Provider-Specific Integration

### Firebase Auth

```python
from firebase_admin import auth, initialize_app, credentials
import os, json

# Init — one-time at startup
cred_dict = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{}"))
initialize_app(credentials.Certificate(cred_dict))

async def verify_firebase(authorization: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    decoded = auth.verify_id_token(token, check_revoked=True)
    return UserContext(
        user_id=decoded["uid"],
        auth_provider="firebase",
        email=decoded.get("email"),
        roles=decoded.get("roles", ["user"]),
        tenant_id=decoded.get("tenant_id"),
    )
```

### Google Identity (OAuth2/OIDC)

```python
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

async def verify_google(authorization: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    payload = await verify_oidc_token(token, GOOGLE_ISSUERS[0], client_id)
    return UserContext(
        user_id=payload["sub"],
        auth_provider="google",
        email=payload.get("email"),
        roles=["user"],
        scopes=payload.get("scope", "").split(),
    )
```

### GitHub OAuth2

```python
# Step 1: Redirect user to GitHub authorization URL
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

async def github_oauth_callback(code: str, client_id: str, client_secret: str) -> UserContext:
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            json={"client_id": client_id, "client_secret": client_secret, "code": code},
            headers={"Accept": "application/json"},
        )
        access_token = token_resp.json()["access_token"]

        # Fetch user identity
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user = user_resp.json()

        # Fetch orgs for role mapping
        orgs_resp = await client.get(
            f"{GITHUB_USER_URL}/orgs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        orgs = [o["login"] for o in orgs_resp.json()]

    return UserContext(
        user_id=f"github:{user['id']}",
        auth_provider="github",
        email=user.get("email"),
        roles=["admin"] if "my-org" in orgs else ["user"],
        scopes=["read", "write"] if "my-org" in orgs else ["read"],
    )
```

### Microsoft Entra ID (Azure AD)

```python
async def verify_entraid(authorization: str, tenant_id: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
    payload = await verify_oidc_token(token, issuer, client_id)

    return UserContext(
        user_id=payload.get("oid", payload["sub"]),  # oid = object ID (stable)
        auth_provider="entraid",
        email=payload.get("email") or payload.get("preferred_username"),
        roles=payload.get("roles", ["user"]),
        tenant_id=payload.get("tid"),
    )
```

### Apple Sign In

```python
APPLE_ISSUER = "https://appleid.apple.com"

async def verify_apple(authorization: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    payload = await verify_oidc_token(token, APPLE_ISSUER, client_id)

    return UserContext(
        user_id=payload["sub"],  # Stable per-team user ID
        auth_provider="apple",
        email=payload.get("email"),  # Only present on first sign-in
    )
```

### Auth0 (Multi-IdP Gateway)

```python
async def verify_auth0(authorization: str, domain: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    issuer = f"https://{domain}/"
    payload = await verify_oidc_token(token, issuer, client_id)

    return UserContext(
        user_id=payload["sub"],
        auth_provider=payload.get("auth0_provider", "auth0"),
        email=payload.get("email"),
        roles=payload.get("https://app.example.com/roles", ["user"]),
        tenant_id=payload.get("https://app.example.com/tenant_id"),
    )
```

### Okta

```python
async def verify_okta(authorization: str, okta_domain: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    issuer = f"https://{okta_domain}"
    payload = await verify_oidc_token(token, issuer, client_id)

    return UserContext(
        user_id=payload["sub"],
        auth_provider="okta",
        email=payload.get("email"),
        roles=payload.get("groups", ["user"]),
        tenant_id=payload.get("org"),
    )
```

### AWS Cognito

```python
async def verify_cognito(authorization: str, user_pool_id: str, client_id: str) -> UserContext:
    token = authorization.removeprefix("Bearer ")
    region = user_pool_id.split("_")[0]
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    payload = await verify_oidc_token(token, issuer, client_id)

    return UserContext(
        user_id=payload["sub"],
        auth_provider="cognito",
        email=payload.get("email"),
        roles=payload.get("cognito:groups", ["user"]),
        scopes=payload.get("scope", "read").split(),
    )
```

## SAML → JWT Bridge Pattern

SAML is NOT directly consumable by ADK backends. Deploy an auth gateway that exchanges SAML assertions for JWTs.

```
[User] → [App] → [SAML IdP] → SAML Assertion
                                    ↓
                            [Auth Gateway]
                            (Cloud Run / Lambda / API Gateway)
                                    ↓
                            Verifies assertion
                            Maps NameID → user_id
                            Maps attributes → roles, tenant_id
                            Issues internal JWT
                                    ↓
                            [ADK Backend] (sees only JWT)
```

```yaml
# auth-gateway/saml-config.yaml — Per-IdP SAML mapping
idps:
  okta:
    entity_id: "http://www.okta.com/exk..."
    sso_url: "https://my-org.okta.com/app/.../sso/saml"
    certificate: "saml/okta-cert.pem"
    claims_mapping:
      user_id: "NameID"
      email: "email"
      roles: "groups"
      tenant_id: "organization"
    jwt:
      issuer: "https://auth-gateway.example.com"
      audience: "adk-backend"
      ttl_seconds: 3600

  azure_ad:
    entity_id: "https://sts.windows.net/<tenant-id>/"
    sso_url: "https://login.microsoftonline.com/<tenant-id>/saml2"
    certificate: "saml/azure-cert.pem"
    claims_mapping:
      user_id: "nameID"
      email: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
      roles: "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
      tenant_id: "http://schemas.microsoft.com/identity/claims/tenantid"

  keycloak:
    entity_id: "https://keycloak.example.com/auth/realms/<realm>"
    sso_url: "https://keycloak.example.com/auth/realms/<realm>/protocol/saml"
    certificate: "saml/keycloak-cert.pem"
    claims_mapping:
      user_id: "nameID"
      email: "email"
      roles: "roles"
```

```python
# auth-gateway/saml_bridge.py
"""Simplified SAML→JWT bridge. In production, use python3-saml or pysaml2."""

from onelogin.saml2.auth import OneLogin_Saml2_Auth
import jwt, time, os

def saml_to_jwt(saml_response: str, idp_config: dict) -> str:
    """Validate SAML assertion and issue internal JWT."""
    auth = OneLogin_Saml2_Auth(request_data={"SAMLResponse": saml_response}, ...)
    auth.process_response()
    attributes = auth.get_attributes()

    claims = {
        "user_id": attributes[idp_config["claims_mapping"]["user_id"]][0],
        "auth_provider": "saml",
        "email": attributes.get(idp_config["claims_mapping"]["email"], [None])[0],
        "roles": attributes.get(idp_config["claims_mapping"]["roles"], ["user"]),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "iss": idp_config["jwt"]["issuer"],
        "aud": idp_config["jwt"]["audience"],
    }

    return jwt.encode(claims, os.getenv("JWT_SIGNING_KEY"), algorithm="HS256")
```

## Go Auth Middleware — Multi-Provider

```go
// middleware/auth_multiprovider.go
package middleware

import (
    "context"
    "net/http"
    "os"
    "strings"
)

type ProviderType string
const (
    FirebaseProvider ProviderType = "firebase"
    GoogleProvider   ProviderType = "google"
    EntraIDProvider  ProviderType = "entraid"
    OktaProvider     ProviderType = "okta"
    Auth0Provider    ProviderType = "auth0"
    CognitoProvider  ProviderType = "cognito"
)

type AuthProvider interface {
    Verify(ctx context.Context, token string) (UserContext, error)
    Type() ProviderType
}

// MultiProviderAuth validates JWTs from any configured IdP.
type MultiProviderAuth struct {
    providers map[ProviderType]AuthProvider
}

func NewMultiProviderAuth() *MultiProviderAuth {
    m := &MultiProviderAuth{providers: make(map[ProviderType]AuthProvider)}
    // Register configured providers
    if os.Getenv("FIREBASE_ENABLED") == "true" {
        m.providers[FirebaseProvider] = NewFirebaseProvider()
    }
    if os.Getenv("ENTRAID_ENABLED") == "true" {
        m.providers[EntraIDProvider] = NewEntraIDProvider(
            os.Getenv("ENTRAID_TENANT_ID"),
            os.Getenv("ENTRAID_CLIENT_ID"),
        )
    }
    if os.Getenv("OKTA_ENABLED") == "true" {
        m.providers[OktaProvider] = NewOIDCProvider(
            "okta",
            os.Getenv("OKTA_ISSUER"),
            os.Getenv("OKTA_AUDIENCE"),
        )
    }
    // Add more providers as needed
    return m
}

func (m *MultiProviderAuth) Middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if !strings.HasPrefix(authHeader, "Bearer ") {
            http.Error(w, `{"error":"unauthorized"}`, 401)
            return
        }
        token := strings.TrimPrefix(authHeader, "Bearer ")

        // Auto-detect provider from token issuer (decode JWT header)
        // or use X-Auth-Provider header
        providerType := ProviderType(r.Header.Get("X-Auth-Provider"))
        if _, ok := m.providers[providerType]; !ok {
            providerType = m.detectProvider(token)
        }

        provider := m.providers[providerType]
        uc, err := provider.Verify(r.Context(), token)
        if err != nil {
            http.Error(w, `{"error":"invalid token"}`, 401)
            return
        }

        ctx := context.WithValue(r.Context(), UserContextKey, uc)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func (m *MultiProviderAuth) detectProvider(token string) ProviderType {
    // Decode JWT header without verification to find issuer
    // Match issuer against configured providers
    // Fall back to Firebase if unknown
    return FirebaseProvider
}
```

## TypeScript Multi-Provider

```typescript
// middleware/auth-providers.ts
import { getAuth } from "firebase-admin/auth";
import { jwtVerify, createRemoteJWKSet } from "jose";
import type { UserContext } from "../types";

interface ProviderConfig {
  type: string;
  issuer: string;
  audience: string;
  jwksUrl?: string;
  enabled: boolean;
}

const providers: Map<string, ProviderConfig> = new Map([
  ["google", {
    type: "google",
    issuer: "https://accounts.google.com",
    audience: process.env.GOOGLE_CLIENT_ID!,
    jwksUrl: "https://www.googleapis.com/oauth2/v3/certs",
    enabled: !!process.env.GOOGLE_CLIENT_ID,
  }],
  ["entraid", {
    type: "entraid",
    issuer: `https://login.microsoftonline.com/${process.env.ENTRAID_TENANT_ID}/v2.0`,
    audience: process.env.ENTRAID_CLIENT_ID!,
    enabled: !!process.env.ENTRAID_CLIENT_ID,
  }],
  ["okta", {
    type: "okta",
    issuer: `https://${process.env.OKTA_DOMAIN}`,
    audience: process.env.OKTA_AUDIENCE!,
    enabled: !!process.env.OKTA_DOMAIN,
  }],
  ["auth0", {
    type: "auth0",
    issuer: `https://${process.env.AUTH0_DOMAIN}/`,
    audience: process.env.AUTH0_AUDIENCE!,
    enabled: !!process.env.AUTH0_DOMAIN,
  }],
]);

export async function verifyMultiProvider(authorization: string): Promise<UserContext> {
  const token = authorization.slice(7); // Remove "Bearer "

  // Try Firebase first (fastest, no JWKS fetch needed)
  if (process.env.FIREBASE_ENABLED === "true") {
    try {
      const decoded = await getAuth().verifyIdToken(token, true);
      return {
        user_id: decoded.uid,
        auth_provider: "firebase",
        email: decoded.email,
        roles: decoded.roles ?? ["user"],
      };
    } catch { /* Fall through to next provider */ }
  }

  // Try each configured OIDC provider
  const tokenHeader = JSON.parse(Buffer.from(token.split(".")[0], "base64").toString());
  // Match kid/iss to provider...

  // Try each enabled provider
  for (const [name, config] of providers) {
    if (!config.enabled) continue;
    try {
      const JWKS = createRemoteJWKSet(new URL(config.jwksUrl ?? `${config.issuer}/.well-known/openid-configuration`));
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: config.issuer,
        audience: config.audience,
      });
      return {
        user_id: (payload.sub ?? payload.oid ?? "unknown") as string,
        auth_provider: name,
        email: payload.email as string,
        roles: (payload.roles as string[]) ?? ["user"],
        tenant_id: payload.tid as string | undefined,
      };
    } catch { /* Try next provider */ }
  }

  throw new Error("Token verification failed against all providers");
}
```

## Provider Configuration Checklist

- [ ] Provider discovery URL / JWKS endpoint configured
- [ ] Audience (`aud`) validated — never accept tokens meant for other apps
- [ ] Issuer (`iss`) validated — matches expected provider
- [ ] Token expiry (`exp`) checked on every request
- [ ] Token revocation checked where supported (Firebase `check_revoked=True`)
- [ ] JWT signing key rotation handled (JWKS cache with TTL, periodic refresh)
- [ ] Claims mapping documented: `sub` → `user_id`, groups → `roles`
- [ ] Multi-tenancy handled: `tenant_id` / `tid` / `org` claim propagated
- [ ] Separate credentials (client_id, secrets) for dev/staging/prod
- [ ] OAuth redirect URIs restricted to known domains
- [ ] CSRF state parameter validated in OAuth flows
- [ ] PKCE enforced for public OAuth clients (SPA, mobile)

## Role Mapping

Map provider-specific groups/claims to application roles:

```python
# auth/role_mapper.py — centralized role resolution

ROLE_MAPPINGS = {
    "entraid": {
        "admin-group-id": "admin",
        "editor-group-id": "editor",
    },
    "okta": {
        "Everyone": "user",
        "Admin": "admin",
    },
    "auth0": {
        "Admin": "admin",
        "Content Manager": "editor",
        "Viewer": "viewer",
    },
}

def resolve_roles(provider: str, claims: dict) -> list[str]:
    """Map provider-specific claims to application roles."""
    mapping = ROLE_MAPPINGS.get(provider, {})
    provider_groups = claims.get("groups", []) or claims.get("roles", [])

    roles = {"user"}  # Default role
    for group in provider_groups:
        if group in mapping:
            roles.add(mapping[group])

    return sorted(roles)
```
