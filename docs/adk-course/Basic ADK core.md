Basic ADK core

Below is the **next continuation section (V6)**, integrating **enterprise-grade security for ADK multi-agent systems** into the architecture you’ve built so far.

This section connects:

* multi-agent orchestration  
* runtime behavior  
* real-world security controls  
* Google Cloud production practices

---

# **1\. Why Security Becomes Critical in Agent Systems**

In traditional systems:

* code executes predefined logic

In ADK systems:

* agents **decide what to do**  
* agents **call tools autonomously**  
* agents **interact with external systems**

This introduces a new risk model:

LLM reasoning \+ tool execution \= autonomous actions

### **Core Risk Shift**

| Traditional App | Agent System |
| ----- | ----- |
| deterministic | non-deterministic |
| fixed API calls | dynamic tool selection |
| predictable behavior | emergent behavior |

---

# **2\. Core Security Risks in Multi-Agent Systems**

## **2.1 Rogue Actions**

Agents may:

* execute unintended operations  
* misuse tools  
* act outside intended scope

Cause:

* prompt injection  
* incorrect reasoning  
* malicious inputs

---

## **2.2 Sensitive Data Disclosure**

Agents may:

* leak secrets  
* expose user data  
* exfiltrate information via outputs

---

## **2.3 System-Level Risk Amplification**

In multi-agent systems:

Agent A compromised → influences Agent B → propagates across system

This is why **security must be layered and enforced externally**, not just via prompts.

---

# **3\. Authentication vs Authorization (Foundation)**

Every agent action must pass two checks:

---

## **3.1 Authentication (AuthN)**

Who are you?

Verifies:

* agent identity  
* credentials

Examples:

* Service Account  
* API Key  
* OAuth

---

## **3.2 Authorization (AuthZ)**

What are you allowed to do?

Verifies:

* permissions  
* access scope

Managed via:

* IAM roles

---

## **3.3 Mental Model**

Authentication → identity established  
Authorization → permissions enforced

---

# **4\. Service Accounts (Agent Identity)**

Every deployed agent runs as a **principal**.

---

## **4.1 Default Service Account**

* automatically created  
* basic permissions  
* used for quick setup

---

## **4.2 Custom Service Account (Recommended)**

You define:

* exact permissions  
* scoped access

### **Principle Applied**

Least Privilege \= only required permissions

---

## **4.3 Example**

Agent needs:  
\- read from storage  
\- write logs

→ grant ONLY:  
\- storage.objects.get  
\- logging.write

---

# **5\. Authentication Methods in Agent Systems**

## **5.1 Service Account**

Used for:

* Google Cloud services

---

## **5.2 API Keys**

Used for:

* external APIs

Risk:

* must be stored securely (Secret Manager)

---

## **5.3 OAuth**

Used for:

* user-level permissions

Example:

* accessing user calendar  
* accessing email

---

# **6\. Permission Management (IAM)**

Access is controlled via:

* roles  
* policies

---

## **6.1 Granting Permissions**

gcloud projects add-iam-policy-binding ...

---

## **6.2 Revoking Permissions**

Remove roles immediately if:

* not needed  
* security risk detected

---

## **6.3 Best Practice**

* use CLI for automation  
* avoid manual console changes in production

---

# **7\. Security Across Agent Lifecycle**

Agent execution pipeline introduces risks at every stage:

---

## **7.1 Input / Perception Layer**

Risk:

* prompt injection  
* malicious input

Mitigation:

* input filtering  
* validation

---

## **7.2 System Instructions Layer**

Risk:

* instructions overridden

Mitigation:

* strict separation:  
  * system instructions (trusted)  
  * user input (untrusted)

---

## **7.3 Reasoning / Planning Layer**

Risk:

* flawed logic  
* manipulated decisions

Mitigation:

* constrain via tools  
* validate outputs

---

## **7.4 Tool Execution Layer**

Risk:

* unauthorized actions  
* API misuse

Mitigation:

* IAM controls  
* deterministic enforcement

---

## **7.5 Memory Layer**

Risk:

* storing malicious data  
* persistent injection

Mitigation:

* sanitize stored data  
* validate memory writes

---

## **7.6 Response Rendering Layer**

Risk:

* XSS  
* data exfiltration

Mitigation:

* output sanitization  
* content filtering

---

# **8\. Core Security Principles (Google Framework)**

## **8.1 Human Control**

Agents must:

* operate under human authority  
* not act fully autonomously in critical flows

---

## **8.2 Limited Powers**

Agents must:

* have restricted permissions  
* not escalate privileges

---

## **8.3 Observability**

All actions must be:

* logged  
* traceable  
* auditable

---

# **9\. Defense-in-Depth Architecture**

Google uses a **hybrid layered approach**:

---

## **9.1 Deterministic Enforcement Layer**

Runs outside LLM.

### **Example Rules**

\- block transactions \> $500  
\- require confirmation for delete actions

---

## **9.2 Reasoning-Based Defense**

LLM-based checks:

* detect anomalies  
* evaluate intent

---

## **9.3 Combined Model**

LLM → suggests action  
Deterministic layer → approves or blocks

---

# **10\. Model Armor (Critical Security Layer)**

Model Armor protects:

* inputs (prompts)  
* outputs (responses)

---

## **10.1 Prompt Injection Protection**

Detects:

* hidden malicious instructions  
* jailbreak attempts

---

## **10.2 Sensitive Data Protection**

Uses:

* Data Loss Prevention (DLP)

Actions:

* mask  
* redact  
* tokenize

---

## **10.3 Output Filtering**

Prevents:

* harmful content  
* unsafe responses

---

# **11\. Content Safety Controls**

Systems must:

1. assess risks  
2. test outputs  
3. configure filters  
4. monitor behavior

---

## **Example Controls**

* hate speech filters  
* dangerous content filters  
* policy enforcement

---

# **12\. Security in Multi-Agent Orchestration**

## **12.1 Key Risk**

Agent A → passes malicious output → Agent B executes it

---

## **12.2 Mitigation Strategy**

* validate all inter-agent communication  
* enforce schemas  
* sanitize outputs

---

## **12.3 Secure Delegation**

Parent Agent  
   → validates input  
   → delegates task  
   → verifies result

---

# **13\. Secure Architecture Pattern**

User  
 ↓  
API Gateway  
 ↓  
Security Layer (Model Armor \+ Filters)  
 ↓  
Root Agent  
 ↓  
Workflow Agents  
 ↓  
Tool Execution (IAM controlled)  
 ↓  
Audit Logs \+ Cloud Trace  
 ↓  
Response

---

# **14\. Observability and Auditing**

Use:

* Cloud Trace  
* structured logs  
* event tracking

Track:

* inputs  
* decisions  
* tool calls  
* outputs

---

# **15\. Common Security Failures**

## **15.1 Over-permissioned Agents**

Fix:

* least privilege

---

## **15.2 Trusting LLM Output**

Fix:

* always validate

---

## **15.3 No Input Filtering**

Fix:

* sanitize all inputs

---

## **15.4 No Output Filtering**

Fix:

* enforce response policies

---

# **16\. Secure Multi-Agent Checklist**

## **Identity**

* service account defined  
* roles minimal

---

## **Input**

* validated  
* sanitized

---

## **Execution**

* tool access controlled  
* deterministic checks

---

## **Output**

* filtered  
* safe

---

## **Monitoring**

* logs enabled  
* traces collected

---

# **17\. Key Takeaways**

* agent systems introduce new security risks due to autonomy  
* authentication defines identity  
* authorization defines permissions  
* IAM \+ service accounts are foundational  
* security must cover the entire lifecycle  
* hybrid defense (rules \+ AI) is mandatory  
* Model Armor provides critical protection  
* observability is essential for trust

---

# **18\. What You Should Implement Next**

To move to production-level security:

1. create custom service accounts  
2. restrict IAM roles  
3. implement input filtering  
4. add Model Armor  
5. enforce deterministic tool policies  
6. enable logging \+ tracing  
7. validate all agent outputs

---

