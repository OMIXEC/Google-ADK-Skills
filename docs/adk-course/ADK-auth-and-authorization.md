# **ADK on Google Cloud: Authentication, Authorization, and High-Level Security Guide**

This guide gives an engineering team a practical reference for implementing authentication, authorization, and core production security in any ADK-based product deployed on Google Cloud. Authentication verifies identity, while authorization determines what that verified identity is allowed to do through IAM roles and permissions.docs.cloud.google+1

## **Core model**

In Google Cloud terms, **authentication** answers "who are you?" and **authorization** answers "what are you allowed to do?"; both are required for every access path your agent uses in production.docs.cloud.google

For ADK-based systems, the most important design rule is to separate three identities:

* the **runtime identity** of the deployed agent,  
* the **end-user identity** when a user signs in or grants consent,  
* the **tool/data identity** used to access internal or third-party systems.cloud.google+1

Treat the deployed agent like a non-human employee. Give it a dedicated principal, restrict its permissions to the minimum set required, and avoid broad inherited access such as project-wide Editor-style privileges.docs.cloud.google+1

## **Authentication vs authorization**

| Topic | What it means | Typical Google Cloud mechanism | Dev team rule |
| ----- | ----- | ----- | ----- |
| Authentication (AuthN) | Verifies the identity making the request | Service account, OAuth client ID, API key, Application Default Credentials in dev | Never let production code run with ambiguous identity.docs.cloud.google+1 |
| Authorization (AuthZ) | Decides what the authenticated identity can do | IAM roles and permissions bound to the principal | Grant only the permissions required for the concrete task.docs.cloud.google+1 |
| Secret handling | Protects credentials used by the agent or tools | Secret Manager | Never hardcode secrets or commit them to source control.docs.cloud.google+1 |
| Data perimeter | Prevents exfiltration from sensitive services | VPC Service Controls | Use for sensitive production environments and regulated data paths.cloud.google+1 |

## **Identity options for ADK products**

For Vertex AI Agent Engine, Google supports either **agent identity** or **service accounts** for deployed agents. Agent identity is recommended in preview for IAM-based agent security, while service accounts remain the standard shared runtime identity across deployed agents.cloud.google+1

If using service accounts on Agent Engine, the runtime can use either the Google-managed **AI Platform Reasoning Engine Service Agent** in the format `service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`, or a custom service account that the team creates and manages.docs.cloud.google+1

A custom service account is the better production default for most serious ADK products because it gives tighter least-privilege control and cleaner audit boundaries than reusing the default service agent for many capabilities.docs.cloud.google+1

## **Decision matrix**

| Need | Recommended method | Why |
| ----- | ----- | ----- |
| Access Google Cloud resources such as Cloud Storage, BigQuery, Vertex AI, Secret Manager | Service account or Agent Engine agent identity | Native IAM authorization and auditable non-human identity.docs.cloud.google+1 |
| Call a third-party API that requires a vendor token | API key or vendor credential stored in Secret Manager | The vendor may not support Google IAM directly; store and retrieve the secret securely.docs.cloud.google+1 |
| Sign in end users or request delegated access to their personal data | OAuth client ID | Requires user consent and is the correct pattern for user-account access.docs.cloud.google |
| Local development against Google Cloud APIs | Application Default Credentials via `gcloud auth application-default login` or service account impersonation | Matches Google’s recommended local auth flow and avoids embedding keys in code.cloud.google+1 |

## **Recommended production pattern**

## **1\. Use one runtime service account per environment**

Create separate service accounts for `dev`, `staging`, and `prod`, and use different identities for different products or trust zones. This limits blast radius and makes audit logs and IAM reviews much easier to understand.cloud.google+1

Example naming:

* `adk-dev-runtime@PROJECT_ID.iam.gserviceaccount.com`  
* `adk-stg-runtime@PROJECT_ID.iam.gserviceaccount.com`  
* `adk-prod-runtime@PROJECT_ID.iam.gserviceaccount.com`

## **2\. Grant narrow roles, preferably at resource scope**

Grant IAM roles directly on the smallest relevant resource whenever possible, such as a single bucket, dataset, secret, or topic, instead of broad project-level grants. Google documents role assignment and revocation for deployed agents through IAM, and recommends using console, `gcloud`, or Terraform rather than custom Python for role management workflows.docs.cloud.google

Bad pattern:

* Project-wide broad role because "the agent might need it later."docs.cloud.google+1

Good pattern:

* `roles/storage.objectViewer` on one bucket only.  
* `roles/secretmanager.secretAccessor` on one secret only.  
* `roles/bigquery.dataViewer` on one dataset only.

## **3\. Keep user identity separate from agent identity**

When the product supports user login, the user should authenticate separately, usually through OAuth-based login. The agent’s runtime identity should not become a substitute for the end-user identity, especially for user-specific data access that needs consent or per-user authorization boundaries.docs.cloud.google

## **4\. Store secrets in Secret Manager**

Google’s guidance for agent access management explicitly uses Secret Manager for API keys and OAuth client credentials, and supports secret labeling for organization and filtering.docs.cloud.google

Use Secret Manager for:

* external API keys,  
* OAuth client secrets,  
* webhook signing secrets,  
* database passwords when IAM-based auth is not available.cloud.google+1

## **5\. Add a data perimeter for sensitive environments**

VPC Service Controls can create a security perimeter around Google Cloud resources to reduce data exfiltration risk, and Google documents that Cloud Run and Secret Manager can both participate in VPC Service Controls protections.cloud.google+2

## **Implementation cheat sheet**

## **AuthN checklist**

* Assign a dedicated runtime identity for every deployed agent service.cloud.google  
* Prefer custom service accounts for production agents when using Agent Engine.cloud.google  
* Use Application Default Credentials on Google Cloud runtimes; avoid service account keys where possible.cloud.google  
* Use OAuth client IDs for end-user login and consented user data access.docs.cloud.google  
* Put third-party API keys and OAuth secrets in Secret Manager, not `.env` files in production.cloud.google+1  
* For local development, use `gcloud auth application-default login` or service account impersonation.cloud.google+1

## **AuthZ checklist**

* Start from zero permissions, then add only what the agent needs.cloud.google+1  
* Prefer predefined or custom least-privilege roles over broad project roles.docs.cloud.google  
* Bind roles at the resource level when possible, not only at the project level.docs.cloud.google  
* Separate read, write, admin, and destructive actions across different tools and identities.docs.cloud.google+1  
* Review and revoke unused IAM grants regularly using IAM policy inspection and change control.docs.cloud.google

## **Security checklist**

* Use Secret Manager for credentials and rotate secrets on a schedule.cloud.google+1  
* Put sensitive services inside VPC Service Controls where exfiltration risk matters.cloud.google+1  
* Consider CMEK when compliance requires customer-managed encryption for Agent Engine deployments, noting the regional and immutability limitations Google documents.docs.cloud.google  
* Enable Cloud Logging, Cloud Monitoring, and Cloud Trace APIs in the project so access and failures are observable.cloud.google  
* Use separate projects or strong environment isolation for dev, staging, and prod.cloud.google  
* Prefer Terraform, `gcloud`, or policy-as-code for IAM changes instead of ad hoc console editing for repeatable production operations.docs.cloud.google

## **Common architecture patterns**

## **Pattern A: Agent accesses Google Cloud data directly**

Use a custom service account attached to the deployed agent and grant only the required IAM roles on the exact resources it must access. This is the cleanest pattern for Cloud Storage, BigQuery, Secret Manager, and other Google Cloud services.cloud.google+1

Example flow:

1. Agent runs as `adk-prod-runtime`.  
2. IAM grants `roles/storage.objectViewer` on `gs://prod-knowledge-bucket`.  
3. Agent can read objects there but cannot write, list unrelated buckets, or modify IAM.docs.cloud.google

## **Pattern B: Agent calls third-party APIs**

Use Secret Manager to store the external API key or vendor credential, then grant the runtime principal only the ability to access that secret. The agent loads the secret at runtime and uses it only inside the relevant tool implementation.cloud.google+1

This reduces leakage risk and avoids scattering credentials across code, CI, and environment files.cloud.google+1

## **Pattern C: Agent acts on behalf of a signed-in user**

Use OAuth client IDs for user login and user-consent flows. This is the correct pattern when the user must explicitly authorize access to calendars, email, drives, or other user-owned resources.docs.cloud.google

The runtime service account still exists for infrastructure operations, but it should not silently bypass the user-consent boundary.docs.cloud.google

## **Pattern D: Cross-project service account usage**

Google documents extra setup when a custom service account lives in a different project than the deployed agent. This requires allowing cross-project service account usage and granting the Vertex AI service agent the `roles/iam.serviceAccountTokenCreator` role in the service-account-hosting project.cloud.google+1

This pattern is useful in large organizations with centralized identity projects, but it adds complexity and should be standardized early.cloud.google

## **Concrete Google Cloud commands**

## **List a deployed agent principal’s roles**

bash  
`gcloud projects get-iam-policy PROJECT_ID \`  
  `--flatten="bindings[].members" \`  
  `--filter="bindings.members:serviceAccount:PRINCIPAL" \`  
  `--format="value(bindings.role)"`

Google documents this flow for inspecting the roles assigned to the service account used by a deployed agent.docs.cloud.google

## **Grant a role**

bash  
`gcloud projects add-iam-policy-binding PROJECT_ID \`  
  `--member="serviceAccount:PRINCIPAL" \`  
  `--role="ROLE_NAME"`

## **Revoke a role**

bash  
`gcloud projects remove-iam-policy-binding PROJECT_ID \`  
  `--member="serviceAccount:PRINCIPAL" \`  
  `--role="ROLE_NAME"`

These are the documented `gcloud` patterns for granting and revoking roles for deployed agents.docs.cloud.google

## **Create a secret**

bash  
`gcloud secrets create SECRET_ID --replication-policy="automatic"`  
`gcloud secrets versions add SECRET_ID --data-file="FILE_PATH"`

## **List secrets**

bash  
`gcloud secrets list --filter="FILTER"`

Google’s agent access management documentation uses Secret Manager as the recommended store for API keys and OAuth credentials.docs.cloud.google

## **Team design rules**

## **Rule 1: Every tool gets an access review**

For every ADK tool, document:

* what identity it uses,  
* what systems it reaches,  
* what permissions it requires,  
* whether it performs read, write, or destructive actions,  
* whether user consent or human approval is required.youtubedocs.cloud.google

## **Rule 2: Separate low-risk and high-risk tools**

Read-only tools should not share the same authorization boundary as write-capable or destructive tools. Use separate modules, approval workflows, and in some cases separate service accounts for privileged action paths.youtubedocs.cloud.google

## **Rule 3: Never let prompts be the only guardrail**

Prompt instructions such as "do not delete data" are not security controls by themselves. Real control must come from IAM, secret scoping, tool design, and approval gates.docs.cloud.google+1

## **Rule 4: Prefer an intermediary service for sensitive systems**

Instead of giving the agent raw direct access to every backend, place sensitive operations behind narrowly designed internal APIs or tools. This layered pattern is highlighted in Google Cloud security guidance for agent scenarios as a way to isolate credentials and restrict direct data access.youtube

## **Rule 5: Design for revocation**

Every permission grant should be easy to inspect, rotate, and revoke. Google explicitly documents grant and revoke flows for deployed agent principals, and this should become part of incident response and offboarding playbooks.docs.cloud.google

## **Example permission bundles**

These are example bundles for design discussion, not copy-paste defaults.

| Tool capability | Suggested access pattern | Notes |
| ----- | ----- | ----- |
| Read docs from one bucket | `roles/storage.objectViewer` on one bucket | Read-only knowledge access.docs.cloud.google |
| Read one secret | `roles/secretmanager.secretAccessor` on one secret | Use for vendor API keys.docs.cloud.google+1 |
| Run Vertex AI inference | `roles/aiplatform.user` or the documented Agent Engine identity roles, depending on runtime model | Keep inference separate from admin permissions.cloud.google |
| Use project quota from agent identity | `roles/serviceusage.serviceUsageConsumer` | Google recommends this for agent identity setup.cloud.google |
| Impersonate a service account in controlled admin workflows | `roles/iam.serviceAccountUser` for deployment, `roles/iam.serviceAccountTokenCreator` only when explicitly required | High-risk permission; constrain tightly.cloud.google+1 |

## **High-level security reference architecture**

A strong security baseline for an ADK product on Google Cloud usually includes:

* authenticated end-user access through OAuth or enterprise identity,  
* a dedicated runtime identity for the agent,  
* least-privilege IAM grants on data and tools,  
* Secret Manager for secrets,  
* structured logging and tracing enabled,  
* VPC Service Controls for sensitive data perimeters,  
* optional CMEK for regulated deployments on Agent Engine.cloud.google+3

This layered model is stronger than any single control because it assumes mistakes will happen and limits how far a compromised tool, prompt, or credential can reach.cloud.googleyoutube

## **Anti-patterns**

Avoid these recurring mistakes:

* Using one broad service account for every environment and every tool.docs.cloud.google+1  
* Giving project-wide broad roles because permissions are not yet understood.docs.cloud.google  
* Keeping API keys in source code, container images, or CI variables without Secret Manager.cloud.google+1  
* Treating prompt wording as the main authorization control.youtube  
* Mixing user-consented actions with the agent’s infrastructure identity without a clear boundary.docs.cloud.google  
* Creating long-lived service account keys unless there is no better option.cloud.google

## **Minimum rollout plan**

## **Phase 1: Foundation**

* Create per-environment projects or strong isolation boundaries.cloud.google  
* Create dedicated runtime service accounts.cloud.google  
* Enable Vertex AI, Cloud Logging, Cloud Monitoring, Cloud Trace, Resource Manager, and Secret Manager related APIs as needed.cloud.google  
* Put all vendor secrets in Secret Manager.cloud.google+1

## **Phase 2: Least privilege**

* Inventory every tool and required permission.docs.cloud.google  
* Grant narrow IAM roles at resource scope.docs.cloud.google  
* Validate access with integration tests and failure-path tests.cloud.google+1

## **Phase 3: Hardening**

* Add VPC Service Controls for sensitive services.cloud.google+1  
* Add approval steps for privileged actions.youtube  
* Add IAM review, secret rotation, and revoke playbooks.docs.cloud.google  
* Add CMEK when compliance requires it for Agent Engine workloads.docs.cloud.google

## **Fast cheat sheet**

## **Which auth method should be used?**

| Scenario | Use this |
| :---: | :---: |

| Scenario | Use this |
| ----- | ----- |
| Agent reads Cloud Storage or BigQuery | Service account or Agent Engine agent identity.docs.cloud.google+1 |
| Agent calls a third-party SaaS API | API key or credential from Secret Manager.docs.cloud.google+1 |
| User logs into the product | OAuth client ID.docs.cloud.google |
| Local developer testing | ADC via `gcloud auth application-default login`, optionally service account impersonation.cloud.google+1 |

