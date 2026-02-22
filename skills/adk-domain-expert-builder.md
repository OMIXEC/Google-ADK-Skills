---
name: adk-domain-expert-builder
description: Build custom domain expert agents for specialized fields not covered by standard personas. Configure expertise level, interaction style (formal/socratic/technical), knowledge sources, safety protocols for regulated domains, tool integrations (MCP/APIs). Use for niche expertise, emerging fields, or domains requiring compliance/liability disclaimers.
version: 1.0.0
---

# adk-domain-expert-builder

**Custom Domain Expert Agent Generator**

Build specialized expert agents for any domain not covered by standard personas. Define your domain's expertise, choose interaction style, configure knowledge sources, and generate a production-ready agent in seconds.

## When to Use

Use this skill when:
- Your domain is not covered by pre-built personas
- You need highly specialized expert knowledge
- You are creating agents for emerging fields or niche expertise
- You want customizable safety protocols for regulated domains
- You need both expert knowledge and interaction style customization

## Quick Start

```bash
# Create domain expert with auto-detection
/adk-domain-expert-builder --domain "marine_biology"

# With specific expertise level
/adk-domain-expert-builder --domain "renewable_energy" --expertise_level "advanced"

# With custom safety protocols
/adk-domain-expert-builder --domain "legal_advice" --expertise_level "intermediate" --safety_protocols "strict"

# With specific interaction style
/adk-domain-expert-builder --domain "data_science" --interaction_style "socratic"
```

## Parameters

### Domain Definition

```bash
--domain "domain_name"                    # Required: domain topic
--subdomain "specialized_area"            # Optional: specific focus area
--expertise_level "beginner|intermediate|advanced|expert"  # Default: intermediate
--interaction_style "formal|casual|socratic|technical|friendly"  # Default: friendly
```

### Knowledge Configuration

```bash
--knowledge_sources "[wikipedia,academic,industry]"  # Data sources
--core_concepts "[list, of, key, concepts]"          # Domain fundamentals
--common_questions "[faq, typical, queries]"         # FAQ pre-seeding
--update_frequency "weekly|monthly|quarterly"        # Knowledge refresh
```

### Tool Integration

```bash
--tools "[tool1, tool2, tool3]"           # Function tools needed
--mcp_servers "[database,search,api]"     # MCP integrations
--external_apis "[stripe,openai,slack]"   # External service integrations
--calculation_engine "enabled|disabled"   # Math/numerical support
```

### Safety & Compliance

```bash
--safety_protocols "minimal|standard|strict"  # Safety level
--liability_disclaimers "enabled|disabled"    # Include disclaimers
--regulated_domain true|false                 # Regulatory compliance
--content_policy "standard|custom"            # Content guidelines
--audit_logging "enabled|disabled"            # Action logging
```

## Domain Expert Categories

### Technology Domains

```bash
# Software Engineering
/adk-domain-expert-builder --domain "software_engineering" \
  --subdomain "cloud_architecture" \
  --tools "[code_analyzer,test_generator,documentation_helper]"

# Data Science & AI
/adk-domain-expert-builder --domain "data_science" \
  --subdomain "machine_learning" \
  --calculation_engine "enabled"

# DevOps & Infrastructure
/adk-domain-expert-builder --domain "devops" \
  --subdomain "kubernetes" \
  --mcp_servers "[github,docker]"

# Cybersecurity
/adk-domain-expert-builder --domain "cybersecurity" \
  --expertise_level "advanced" \
  --safety_protocols "strict"
```

### Scientific Domains

```bash
# Marine Biology
/adk-domain-expert-builder --domain "marine_biology" \
  --knowledge_sources "[academic,research_papers]" \
  --tools "[species_identifier,habitat_analyzer]"

# Astrophysics
/adk-domain-expert-builder --domain "astrophysics" \
  --interaction_style "socratic" \
  --calculation_engine "enabled"

# Climate Science
/adk-domain-expert-builder --domain "climate_science" \
  --subdomain "renewable_energy" \
  --knowledge_sources "[research_papers,industry_reports]"

# Neuroscience
/adk-domain-expert-builder --domain "neuroscience" \
  --expertise_level "advanced" \
  --safety_protocols "strict"
```

### Business & Industry Domains

```bash
# Supply Chain Management
/adk-domain-expert-builder --domain "supply_chain" \
  --tools "[inventory_analyzer,route_optimizer]" \
  --mcp_servers "[erp_systems]"

# Manufacturing
/adk-domain-expert-builder --domain "manufacturing" \
  --subdomain "quality_control" \
  --tools "[defect_detector,spc_analyzer]"

# Hospitality Management
/adk-domain-expert-builder --domain "hospitality" \
  --tools "[booking_system,guest_satisfaction_tracker]"

# Retail Operations
/adk-domain-expert-builder --domain "retail" \
  --subdomain "inventory_management" \
  --knowledge_sources "[industry_standards,best_practices]"
```

### Medical & Health Domains

```bash
# Nutrition (with strict disclaimers)
/adk-domain-expert-builder --domain "nutrition" \
  --liability_disclaimers "enabled" \
  --safety_protocols "strict" \
  --interaction_style "technical"

# Physical Therapy
/adk-domain-expert-builder --domain "physical_therapy" \
  --safety_protocols "strict" \
  --tools "[exercise_analyzer,progress_tracker]"

# Mental Health Coaching (non-clinical)
/adk-domain-expert-builder --domain "mental_health_coaching" \
  --expertise_level "intermediate" \
  --safety_protocols "strict" \
  --liability_disclaimers "enabled"

# Dental Care Education
/adk-domain-expert-builder --domain "dental_education" \
  --safety_protocols "standard" \
  --tools "[tooth_identifier,care_recommender]"
```

### Creative & Arts Domains

```bash
# Music Production
/adk-domain-expert-builder --domain "music_production" \
  --subdomain "audio_engineering" \
  --interaction_style "technical"

# Graphic Design
/adk-domain-expert-builder --domain "graphic_design" \
  --tools "[design_analyzer,color_palette_generator]" \
  --interaction_style "creative"

# Film Production
/adk-domain-expert-builder --domain "film_production" \
  --subdomain "cinematography" \
  --knowledge_sources "[film_studies,industry_standards]"

# Interior Design
/adk-domain-expert-builder --domain "interior_design" \
  --tools "[room_visualizer,space_planner]"
```

### Legal & Regulatory Domains

```bash
# Compliance Officer (non-practicing)
/adk-domain-expert-builder --domain "regulatory_compliance" \
  --expertise_level "advanced" \
  --safety_protocols "strict" \
  --liability_disclaimers "enabled" \
  --audit_logging "enabled"

# Intellectual Property Education
/adk-domain-expert-builder --domain "intellectual_property" \
  --expertise_level "intermediate" \
  --liability_disclaimers "enabled" \
  --interaction_style "technical"

# Contract Analysis Assistant (educational)
/adk-domain-expert-builder --domain "contract_analysis" \
  --expertise_level "intermediate" \
  --safety_protocols "strict" \
  --liability_disclaimers "enabled"
```

### Environmental & Sustainability

```bash
# Environmental Consulting
/adk-domain-expert-builder --domain "environmental_science" \
  --subdomain "sustainability" \
  --tools "[carbon_calculator,impact_analyzer]"

# Green Building (LEED)
/adk-domain-expert-builder --domain "green_building" \
  --subdomain "leed_certification" \
  --knowledge_sources "[leed_standards,building_codes]"

# Waste Management
/adk-domain-expert-builder --domain "waste_management" \
  --tools "[waste_classifier,recycling_guide]"
```

## Configuration Profiles

### Beginner-Friendly Expert

```bash
/adk-domain-expert-builder --domain "data_science" \
  --expertise_level "beginner" \
  --interaction_style "friendly" \
  --core_concepts "[data,statistics,visualization]" \
  --calculation_engine "enabled"
```

**Generated Agent Features:**
- Simple explanations without jargon
- Patient, encouraging tone
- Frequent clarifying questions
- Analogies to everyday concepts
- Progressive difficulty increase

### Socratic Method Expert

```bash
/adk-domain-expert-builder --domain "philosophy" \
  --interaction_style "socratic" \
  --expertise_level "advanced"
```

**Generated Agent Features:**
- Questions instead of answers
- Student discovery-focused
- Logical rigor
- Debate facilitation
- Critical thinking emphasis

### Technical Expert

```bash
/adk-domain-expert-builder --domain "kubernetes" \
  --interaction_style "technical" \
  --expertise_level "advanced" \
  --tools "[k8s_analyzer,yaml_validator]"
```

**Generated Agent Features:**
- Technical jargon and precision
- Direct, efficient communication
- Assumes knowledge foundation
- Code/config examples
- Performance optimization focus

### Regulated Domain Expert

```bash
/adk-domain-expert-builder --domain "medical_advice" \
  --safety_protocols "strict" \
  --liability_disclaimers "enabled" \
  --regulated_domain true \
  --audit_logging "enabled"
```

**Generated Agent Features:**
- Prominent disclaimers
- Professional language
- Safety-first recommendations
- Escalation to professionals
- Full audit trail of interactions
- Compliance monitoring

## Generated Code Example

```python
# agents/marine_biology_expert/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from tools.marine_tools import identify_species, analyze_habitat

# Domain-expert specific instruction template
instruction = """
You are a marine biology expert specializing in ocean conservation.

**Expertise Areas:**
- Marine species identification and behavior
- Ecosystem dynamics and food webs
- Ocean conservation and sustainability
- Marine research methodologies
- Coastal habitat protection
- Climate change impacts on marine systems

**Communication Style:** Scientific yet accessible, evidence-based, enthusiastic
**Interaction Approach:** Encourage curiosity, provide context, cite research

**Knowledge Foundation:**
- 200+ common marine species and their characteristics
- Major ocean ecosystems and biodiversity hotspots
- Current conservation challenges and solutions
- Research methodologies in marine biology
- Climate change impacts on marine environments

**Behavior Guidelines:**
1. Provide accurate, scientifically-based information
2. Cite research sources when available
3. Acknowledge uncertainty and knowledge limits
4. Encourage citizen science and ocean stewardship
5. Connect individual actions to ecosystem impacts
6. Explain complex concepts with relatable examples
7. Stay current with marine conservation developments

**Available Tools:**
- identify_species: Identify marine species from description/image
- analyze_habitat: Assess marine habitat conditions
- conservation_tracker: Find relevant conservation projects
- research_search: Find peer-reviewed marine research

**Limitations Acknowledgment:**
- Cannot provide medical advice (refer to healthcare professionals)
- Cannot provide legal advice on marine regulations (refer to authorities)
- Research conclusions always uncertain (note confidence levels)
- Field observations should be verified by professionals
"""

marine_expert_agent = Agent(
    name="marine_biology_expert",
    model="gemini-2.5-flash",
    description="Marine biology expert for species ID, ecosystem analysis, conservation guidance",
    instruction=instruction,
    tools=[
        FunctionTool(identify_species),
        FunctionTool(analyze_habitat),
    ],
)

root_agent = marine_expert_agent
```

## Knowledge Base Configuration

Each domain expert auto-configures appropriate knowledge base:

### Knowledge Source Types

```yaml
Academic:
  - Peer-reviewed research papers
  - University course materials
  - Textbooks and academic references

Industry:
  - Industry standards and best practices
  - Technical specifications
  - Professional guidelines

Community:
  - Stack Overflow / community forums
  - GitHub repositories and documentation
  - Open-source project wikis

Regulatory:
  - Government standards and regulations
  - Compliance frameworks
  - Legal statutes and guidelines
```

### Example: Law Domain Knowledge Setup

```bash
/adk-domain-expert-builder --domain "law" \
  --subdomain "intellectual_property" \
  --knowledge_sources "[regulatory,industry,academic]"

# Auto-configures RAG corpus with:
# +-- Patent office guidelines
# +-- Trademark registration standards
# +-- IP law textbooks
# +-- Court precedents (public domain)
# +-- Current IP regulations
# +-- Industry best practices
```

## Safety Protocols by Domain

### Strict (Medical, Legal, Financial)

```python
# Mandatory disclaimers and checks
- Professional qualification disclaimer
- "Not a substitute for professional advice"
- Escalation to licensed professional required
- Liability acknowledgment
- Audit logging of all interactions
- Content policy strict enforcement
- Regular safety audits
```

### Standard (Technical, General Knowledge)

```python
# Balanced safety and usability
- Accurate information standard
- Acknowledge limitations
- Suggest professional consultation if complex
- Error handling and recovery
- Periodic content review
```

### Minimal (Creative, Educational)

```python
# Light guidance
- Responsible use expectations
- No harmful content
- Optional professional consultation for sensitive topics
```

## Tool Integration

Each domain expert can include domain-specific tools:

```bash
# Software Engineering Tools
/adk-domain-expert-builder --domain "software_engineering" \
  --tools "[code_analyzer,test_generator,performance_profiler,bug_detector]"

# Data Science Tools
/adk-domain-expert-builder --domain "data_science" \
  --tools "[data_analyzer,visualization_helper,model_trainer]" \
  --calculation_engine "enabled"

# Marine Biology Tools
/adk-domain-expert-builder --domain "marine_biology" \
  --tools "[species_identifier,habitat_mapper,conservation_tracker]"

# Culinary Arts Tools
/adk-domain-expert-builder --domain "culinary_arts" \
  --tools "[recipe_analyzer,nutrition_calculator,flavor_pairing_suggester]"
```

## Multi-Domain Orchestration

Combine multiple domain experts:

```bash
# Create climate research team
/adk-domain-expert-builder --domain "climate_science" --deployment none
/adk-domain-expert-builder --domain "marine_biology" --deployment none
/adk-domain-expert-builder --domain "environmental_policy" --deployment none

# Orchestrate with supervisor
/adk-multi-agent-orchestrator \
  --agents "climate_scientist,marine_expert,policy_advisor" \
  --coordinator "research_lead"
```

## Examples

### Example 1: Cybersecurity Consultant

```bash
$ /adk-domain-expert-builder \
  --domain "cybersecurity" \
  --expertise_level "advanced" \
  --subdomain "application_security" \
  --safety_protocols "strict" \
  --tools "[vulnerability_scanner,threat_analyzer,security_auditor]"

Cybersecurity Expert Agent Created

Configuration:
- Domain: Cybersecurity / Application Security
- Expertise Level: Advanced
- Tools: Vulnerability detection, threat analysis, security auditing
- Safety: Strict protocols for responsible disclosure
- Knowledge: OWASP Top 10, CWE database, security research papers

Generated Agent:
- Penetration testing guidance (educational)
- Secure code review assistance
- Threat modeling support
- Security architecture guidance
- Vulnerability remediation advice

Deployment Ready - contains:
+ Security-specific instruction template
+ Tool integrations for security testing
+ Responsible disclosure guidelines
+ Compliance monitoring
+ Audit logging of recommendations
```

### Example 2: Supply Chain Expert

```bash
$ /adk-domain-expert-builder \
  --domain "supply_chain" \
  --subdomain "logistics_optimization" \
  --expertise_level "intermediate" \
  --tools "[inventory_analyzer,route_optimizer,demand_forecaster]" \
  --mcp_servers "[erp_systems,gis_mapping]"

Supply Chain Expert Agent Created

Capabilities:
- Inventory optimization recommendations
- Route efficiency analysis
- Demand forecasting insights
- Supplier relationship guidance
- Logistics cost reduction strategies
- Resilience planning for disruptions

Integration:
- Connected to ERP system via MCP
- Real-time inventory data
- GIS mapping for route optimization
- Predictive analytics enabled
```

## Deployment

All domain experts deploy identically:

```bash
# After generation
cd domain_expert_agent

# Local testing
python -m uvicorn src.main:app --reload

# Production deployment
gcloud run deploy domain-expert --source .

# With specific domain name
gcloud run deploy marine-biology-expert --source .
```

## Using with Flutter

Domain expert agents work seamlessly with Flutter SDK:

```bash
# Generate expert
/adk-domain-expert-builder --domain "fitness_coaching" --subdomain "nutrition"

# Deploy backend
cd fitness_nutrition_expert && gcloud run deploy fitness-nutrition --source .

# Use with Flutter app
# Connect Flutter app to https://fitness-nutrition-{hash}.run.app
```

## Related Skills

- **adk-adaptive-agent-generator** - Create from natural language description
- **adk-persona-builder** - Use pre-built personas
- **adk-rag-builder** - Add knowledge bases to domain experts
- **adk-mcp-integration** - Connect to domain-specific tools
- **adk-multi-agent-orchestrator** - Coordinate multiple domain experts

## More Information

See CLAUDE.md for prompt engineering best practices.
See MCP Server Catalog for domain-specific integrations.
