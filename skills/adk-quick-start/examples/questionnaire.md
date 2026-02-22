# ADK Quick Start Questionnaire

Use this questionnaire to discover which ADK skill best matches your goals.

## Question 1: What's Your Experience Level?

**A) Complete beginner** - New to agents, want to learn quickly
**B) Some experience** - Built agents before, know what I want
**C) Expert** - Building production systems, need advanced features

→ **If A:** Recommend: Simple Agents skill
→ **If B:** Recommend: Custom Agent Builder skill
→ **If C:** Recommend: Multi-Agent Workflows or Integration Tools

---

## Question 2: What's Your Primary Goal?

**A) Learn about ADK** - Understand capabilities, explore possibilities
**B) Build a quick agent** - Fast prototype for a specific task
**C) Custom agent** - Specific requirements for my use case
**D) Multiple agents** - Coordinated system with specialization
**E) Production system** - Deploy agents to users

→ **If A:** Recommend: Quick Start (this skill) + Simple Agents
→ **If B:** Recommend: Simple Agents (templates are fastest)
→ **If C:** Recommend: Custom Agent Builder
→ **If D:** Recommend: Multi-Agent Workflows
→ **If E:** Recommend: Production Deployment (after building agent)

---

## Question 3: What Data Does Your Agent Need?

**A) No special data** - Just reasoning and existing knowledge
**B) Real-time info** - Need web search or live data
**C) Document knowledge** - Learn from uploaded documents
**D) External systems** - Connect to databases, APIs, services
**E) Multiple types** - Combination of the above

→ **If A:** Recommend: Custom Agent Builder or Simple Agents
→ **If B:** Recommend: Custom Agent Builder (with web search tools)
→ **If C:** Recommend: Knowledge & Memory Systems (RAG)
→ **If D:** Recommend: Integration Tools (MCP servers)
→ **If E:** Recommend: Custom Agent Builder + Knowledge Systems + Integration Tools

---

## Question 4: Does Your Agent Need Real-Time Interaction?

**A) No** - Async, batch, or request-response is fine
**B) Maybe** - Would be nice but not essential
**C) Yes** - Needs live, streaming, or voice interaction

→ **If A:** Can use standard agent patterns
→ **If B:** Consider Real-Time Agents for future
→ **If C:** Recommend: Real-Time Agents skill

---

## Question 5: When Do You Want to Deploy?

**A) Just exploring** - Learning and testing
**B) Soon** - Want to deploy in weeks
**C) Now** - Production system needed ASAP
**D) Later** - Build first, deploy later

→ **If A:** Start with Simple Agents, learn at own pace
→ **If B:** Build with Custom Agent Builder, then use Production Deployment
→ **If C:** Start with templates, deploy quickly with Cloud Run
→ **If D:** Build fully featured agent, then deploy when ready

---

## Your Recommended Path

Based on typical answer combinations:

### Path 1: Fastest Start (Learning)
- Question 1 → A (Beginner)
- Question 2 → A (Learn) or B (Quick)
- **Start here:** Simple Agents skill
- **Then:** Read through examples and templates

### Path 2: Custom Agent Development
- Question 1 → B (Some experience)
- Question 2 → C (Custom) or D (Multiple)
- **Start here:** Custom Agent Builder skill
- **Then progress to:** Multi-Agent Workflows if needed

### Path 3: Enterprise/Advanced
- Question 1 → C (Expert)
- Question 2 → D (Multiple) or E (Production)
- **Start here:** Multi-Agent Workflows skill
- **Add:** Integration Tools and Knowledge Systems as needed
- **Deploy with:** Production Deployment skill

### Path 4: Knowledge-Heavy System
- Question 3 → C or D (Data needs)
- **Start here:** Custom Agent Builder
- **Then:** Knowledge & Memory Systems skill
- **Add:** Integration Tools if needed

### Path 5: Real-Time System
- Question 4 → C (Real-time needed)
- **Start here:** Real-Time Agents skill
- **Combine with:** Custom Agent Builder for logic
- **Deploy with:** Production Deployment

---

## Quick Decision Matrix

| I want to... | Start with | Then | Then |
|--------------|-----------|------|------|
| Learn ADK | Simple Agents | Multi-Agent Workflows | Real-Time Agents |
| Build quick prototype | Simple Agents | Deploy with Cloud Run | Monitor & iterate |
| Create custom agent | Custom Agent Builder | Knowledge Systems | Deploy to production |
| Build multi-agent system | Custom Agent Builder | Multi-Agent Workflows | Integration Tools |
| Add knowledge/memory | Custom Agent Builder | Knowledge & Memory | Integrate RAG |
| Build voice agent | Real-Time Agents | Custom Agent Builder | Deploy to Cloud Run |
| Connect external services | Custom Agent Builder | Integration Tools | MCP servers |
| Deploy to production | Build first (any path) | Production Deployment | Monitor with logging |

---

## Example Scenarios

**"Build a research agent quickly"**
- Q1: Beginner → Start with Simple Agents (Researcher template)
- Q2: Quick prototype → Use template as-is or customize
- Q5: Learning → Test with `/adk:test` command
- **Recommended skill:** Simple Agents

**"I need a fitness coaching agent with personalized memory"**
- Q1: Some experience → Know what I want
- Q2: Custom agent → Specific requirements
- Q3: Document knowledge → Remember client profiles
- **Recommended skills:** Custom Agent Builder → Knowledge & Memory Systems

**"Build a multi-agent system for customer support"**
- Q1: Some experience → Building production systems
- Q2: Multiple agents → Supervisor routes to specialists
- Q3: External systems → Connect to ticket database
- Q4: Real-time → Live chat support
- **Recommended skills:** Multi-Agent Workflows → Integration Tools → Production Deployment

**"Deploy voice assistant to my team"**
- Q1: Expert → Production system
- Q2: Production system → Need reliability
- Q4: Real-time → Voice interaction essential
- Q5: Production → Deploy now
- **Recommended skills:** Real-Time Agents → Production Deployment

---

## Not Sure?

When in doubt:
1. Start with **Simple Agents** to understand ADK concepts
2. Try a template that seems close to your use case
3. Test with `/adk:test` command
4. Based on what you learn, move to Custom Agent Builder
5. Add advanced features (multi-agent, RAG, integrations) as needed

The progression from simple → custom → multi-agent → integrated → production ensures you learn each layer before adding complexity.
