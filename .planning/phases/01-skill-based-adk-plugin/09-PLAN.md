---
wave: 4
depends_on: [06-PLAN.md, 07-PLAN.md]
files_modified:
  - skills/adk-realworld-scenarios/SKILL.md
  - skills/adk-vision-agents/SKILL.md
  - skills/adk-tutoring-agents/SKILL.md
  - skills/adk-support-agents/SKILL.md
autonomous: false
requirements: [realworld-scenarios, vision, tutoring, support]
---

# Plan 09: Real-World Enterprise Agent Scenarios

## Objective
Create production-ready agent templates for real-world enterprise scenarios: vision-based world interaction, adaptive tutoring, customer support, language interpretation, and accessibility assistance.

## must_haves
- [ ] Vision agents for real-world visual understanding
- [ ] Adaptive tutoring agents with learning progression
- [ ] Enterprise support agents with escalation
- [ ] Real-time interpretation and translation
- [ ] Accessibility assistance agents

## Tasks

<task id="9.1" type="create">
<title>Create Vision-Based World Interaction Agents</title>
<description>
Agents that see and interpret the visual world:

**Vision Scenarios:**
1. **Environmental Awareness** - Describe surroundings, navigate spaces
2. **Object Identification** - Recognize items, read text, scan barcodes
3. **Document Analysis** - Extract info from documents, receipts, forms
4. **Safety Monitoring** - Detect hazards, verify compliance
5. **Quality Inspection** - Manufacturing QA, defect detection

**Code Example:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai import types
import base64

class VisionWorldAgent:
    \"\"\"Agent that perceives and interprets the visual world.\"\"\"

    def __init__(self):
        self.agent = Agent(
            name="vision_world_agent",
            model="gemini-2.5-flash",  # Vision-capable model
            instruction=\"\"\"
            You are a vision assistant helping users understand their visual environment.

            **Capabilities:**
            1. Describe scenes and surroundings in detail
            2. Identify objects, text, and people
            3. Navigate spaces and provide directions
            4. Read documents and extract information
            5. Detect potential safety hazards

            **Communication Style:**
            - Be descriptive but concise
            - Prioritize safety-relevant information
            - Provide spatial context (left, right, near, far)
            - Acknowledge uncertainty when vision is unclear

            **For accessibility users:**
            - Describe scene structure first, then details
            - Call out obstacles and navigation paths
            - Read all visible text clearly
            \"\"\",
            tools=[
                FunctionTool(self.analyze_scene),
                FunctionTool(self.read_text),
                FunctionTool(self.identify_objects),
                FunctionTool(self.navigate_space),
            ],
        )

    async def analyze_scene(self, image: str, context: str = "") -> dict:
        \"\"\"Analyze a scene from an image.

        Args:
            image: Base64 encoded image
            context: User's current situation or needs

        Returns:
            Scene analysis with key elements identified.
        \"\"\"
        # Vision model processes image
        return {
            "scene_type": "indoor_office",
            "key_elements": ["desk", "computer", "chair", "window"],
            "people_count": 2,
            "text_detected": ["EXIT", "Meeting Room 3"],
            "navigation_paths": ["clear path to door on left"],
            "potential_hazards": ["cable on floor near desk"],
        }

    async def read_text(self, image: str, region: str = "all") -> dict:
        \"\"\"Extract and read text from image.\"\"\"
        return {
            "text_blocks": [
                {"location": "top-center", "text": "Company Report Q4 2025"},
                {"location": "body", "text": "Revenue increased 15%..."},
            ],
            "confidence": 0.95,
        }

    async def identify_objects(self, image: str, object_type: str = None) -> dict:
        \"\"\"Identify specific objects in image.\"\"\"
        return {
            "objects": [
                {"type": "laptop", "brand": "Dell", "location": "center"},
                {"type": "coffee_cup", "location": "right"},
            ]
        }

    async def navigate_space(self, image: str, destination: str) -> dict:
        \"\"\"Provide navigation guidance.\"\"\"
        return {
            "current_position": "entrance",
            "destination": destination,
            "path": "Walk forward 10 feet, turn right at the reception desk",
            "obstacles": ["wet floor sign ahead"],
        }

# Real-time vision with streaming
class RealTimeVisionAgent:
    \"\"\"Vision agent for live video streams.\"\"\"

    def __init__(self):
        self.agent = Agent(
            name="realtime_vision",
            model="gemini-live-2.5-flash-native-audio",
            instruction=\"\"\"
            You are providing real-time visual assistance.
            Describe important changes in the environment.
            Prioritize safety and navigation information.
            Speak naturally and conversationally.
            \"\"\",
        )

    async def process_video_frame(self, frame: bytes, timestamp: float):
        \"\"\"Process a single video frame.\"\"\"
        content = types.Content(parts=[
            types.Part(inline_data=types.Blob(
                mime_type="image/jpeg",
                data=base64.b64encode(frame).decode(),
            ))
        ])
        # Process with agent
        return content
```

**Accessibility Applications:**
- Guide visually impaired users through spaces
- Describe visual content in images/videos
- Read documents and signs aloud
- Identify faces and people for context
</description>
<files>
- skills/adk-vision-agents/SKILL.md
- skills/adk-vision-agents/references/vision-capabilities.md
- skills/adk-vision-agents/references/accessibility-patterns.md
- skills/adk-vision-agents/examples/environmental-awareness.md
- skills/adk-vision-agents/examples/document-analysis.md
- skills/adk-vision-agents/examples/accessibility-assistant.md
</files>
</task>

<task id="9.2" type="create">
<title>Create Adaptive Tutoring Agents</title>
<description>
Intelligent tutoring agents that adapt to learner progress:

**Adaptive Learning Features:**
1. **Learning Style Detection** - Visual, auditory, kinesthetic
2. **Knowledge Assessment** - Pre/post testing, gaps analysis
3. **Progression Tracking** - Competency levels, mastery
4. **Personalized Paths** - Adaptive curriculum
5. **Engagement Monitoring** - Attention, confusion detection

**Code Example:**
```python
from google.adk.agents import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"

class CompetencyLevel(Enum):
    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

@dataclass
class LearnerProfile:
    \"\"\"Tracks learner preferences and progress.\"\"\"
    learner_id: str
    learning_style: LearningStyle = LearningStyle.VISUAL
    competency_levels: Dict[str, CompetencyLevel] = field(default_factory=dict)
    completed_lessons: List[str] = field(default_factory=list)
    struggle_areas: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    engagement_score: float = 0.8
    preferred_pace: str = "moderate"

class AdaptiveTutor:
    \"\"\"Intelligent tutor that adapts to learner needs.\"\"\"

    def __init__(self, subject: str, profile: LearnerProfile):
        self.subject = subject
        self.profile = profile

        # Knowledge assessment agent
        self.assessor = LlmAgent(
            name="knowledge_assessor",
            model="gemini-2.5-flash",
            description="Assesses learner knowledge and gaps",
            instruction=f\"\"\"
            You assess {subject} knowledge through adaptive questioning.
            Start with medium-difficulty questions.
            Adjust difficulty based on responses.
            Identify knowledge gaps and strengths.
            \"\"\",
        )

        # Content presenter agent
        self.presenter = LlmAgent(
            name="content_presenter",
            model="gemini-2.5-flash",
            description="Presents learning content adaptively",
            instruction=f\"\"\"
            You present {subject} content tailored to the learner.

            Learner profile:
            - Learning style: {profile.learning_style.value}
            - Pace: {profile.preferred_pace}
            - Struggle areas: {profile.struggle_areas}

            Adapt your teaching:
            - Visual learners: Use diagrams, charts, examples
            - Auditory: Explain conversationally
            - Kinesthetic: Provide hands-on exercises
            - Reading: Give detailed written explanations
            \"\"\",
        )

        # Practice facilitator agent
        self.practice_agent = LlmAgent(
            name="practice_facilitator",
            model="gemini-2.5-flash",
            description="Guides practice and provides feedback",
            instruction=\"\"\"
            You facilitate practice exercises.
            Provide immediate, constructive feedback.
            Celebrate progress.
            Offer hints when struggling.
            Track mastery progression.
            \"\"\",
        )

        # Main tutor coordinator
        self.tutor = LlmAgent(
            name="adaptive_tutor",
            model="gemini-2.5-pro",  # Better reasoning for adaptation
            description=f"Adaptive {subject} tutor",
            instruction=f\"\"\"
            You are an adaptive {subject} tutor.

            **Your approach:**
            1. Assess current knowledge level
            2. Present content matched to learning style
            3. Facilitate practice with scaffolding
            4. Monitor engagement and adjust pace
            5. Celebrate progress and build confidence

            **Adaptation rules:**
            - If learner struggles 3+ times: simplify, provide more scaffolding
            - If learner succeeds easily: increase challenge
            - If engagement drops: change approach, add interactive elements
            - Always maintain encouraging, patient tone
            \"\"\",
            tools=[
                AgentTool(agent=self.assessor),
                AgentTool(agent=self.presenter),
                AgentTool(agent=self.practice_agent),
            ],
        )

    def update_profile(self, performance: dict):
        \"\"\"Update learner profile based on performance.\"\"\"
        if performance["success_rate"] > 0.8:
            # Learner is progressing well
            topic = performance["topic"]
            current = self.profile.competency_levels.get(topic, CompetencyLevel.NOVICE)
            if current.value < CompetencyLevel.EXPERT.value:
                self.profile.competency_levels[topic] = CompetencyLevel(current.value + 1)
        elif performance["success_rate"] < 0.5:
            # Learner is struggling
            self.profile.struggle_areas.append(performance["topic"])

# Voice-enabled tutor for real-time interaction
voice_tutor = Agent(
    name="voice_tutor",
    model="gemini-live-2.5-flash-native-audio",
    instruction=\"\"\"
    You are a voice-enabled tutor for conversational learning.
    Speak naturally and encouragingly.
    Ask questions to check understanding.
    Provide immediate verbal feedback.
    Use conversational practice for language learning.
    \"\"\",
)
```
</description>
<files>
- skills/adk-tutoring-agents/SKILL.md
- skills/adk-tutoring-agents/references/adaptive-learning.md
- skills/adk-tutoring-agents/references/learner-profiles.md
- skills/adk-tutoring-agents/examples/math-tutor.md
- skills/adk-tutoring-agents/examples/language-tutor.md
- skills/adk-tutoring-agents/examples/coding-tutor.md
</files>
</task>

<task id="9.3" type="create">
<title>Create Enterprise Support and Interpretation Agents</title>
<description>
Production-ready support and interpretation agents:

**Enterprise Support System:**
```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import FunctionTool
from enum import Enum

class TicketPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class EnterpriseSupportSystem:
    \"\"\"Multi-tier enterprise support system.\"\"\"

    def __init__(self, company_name: str, rag_tool):
        # Tier 1: Automated self-service
        self.tier1_agent = LlmAgent(
            name="tier1_support",
            model="gemini-2.5-flash",
            description="First-line automated support",
            instruction=f\"\"\"
            You are {company_name} Tier 1 support.

            **Your role:**
            1. Greet customer warmly
            2. Search knowledge base for answers
            3. Provide step-by-step solutions
            4. Escalate to Tier 2 if:
               - Issue not in knowledge base
               - Customer requests human
               - Technical complexity exceeds FAQ

            **Always:**
            - Verify customer identity first
            - Create ticket for all interactions
            - Document resolution steps
            \"\"\",
            tools=[rag_tool, FunctionTool(self.create_ticket)],
        )

        # Tier 2: Technical specialist
        self.tier2_agent = LlmAgent(
            name="tier2_support",
            model="gemini-2.5-pro",  # Better reasoning
            description="Technical specialist support",
            instruction=\"\"\"
            You are a Tier 2 technical specialist.

            **Your role:**
            1. Investigate complex technical issues
            2. Access system logs and diagnostics
            3. Perform advanced troubleshooting
            4. Escalate to engineering if needed

            **Documentation:**
            - Update ticket with all findings
            - Document root cause analysis
            - Add to knowledge base if new issue
            \"\"\",
            tools=[
                rag_tool,
                FunctionTool(self.access_system_logs),
                FunctionTool(self.run_diagnostics),
            ],
        )

        # Tier 3: Engineering escalation
        self.tier3_agent = LlmAgent(
            name="tier3_engineering",
            model="gemini-2.5-pro",
            description="Engineering escalation handler",
            instruction=\"\"\"
            You handle engineering-level escalations.

            **Your role:**
            1. Analyze bug reports and feature requests
            2. Assess severity and impact
            3. Create engineering tickets (Jira)
            4. Communicate timeline to customer

            **Priority assessment:**
            - CRITICAL: System down, data loss
            - HIGH: Major feature broken
            - MEDIUM: Workaround available
            - LOW: Enhancement request
            \"\"\",
        )

        # Support coordinator
        self.coordinator = LlmAgent(
            name="support_coordinator",
            model="gemini-2.5-flash",
            description="Routes support requests to appropriate tier",
            instruction=\"\"\"
            You coordinate support requests.

            **Routing logic:**
            - FAQ-type questions -> Tier 1
            - Technical issues -> Tier 2
            - Bug reports, feature requests -> Tier 3
            - Always start with Tier 1 unless escalation

            **Handoff protocol:**
            - Brief next tier on context
            - Transfer ticket ownership
            - Notify customer of escalation
            \"\"\",
            tools=[
                AgentTool(agent=self.tier1_agent),
                AgentTool(agent=self.tier2_agent),
                AgentTool(agent=self.tier3_agent),
            ],
        )

    async def create_ticket(self, customer_id: str, issue: str, priority: str) -> dict:
        \"\"\"Create support ticket.\"\"\"
        return {"ticket_id": "T-12345", "status": "open"}

    async def access_system_logs(self, customer_id: str, timerange: str) -> dict:
        \"\"\"Access system logs for debugging.\"\"\"
        return {"logs": [...], "errors_found": 3}

    async def run_diagnostics(self, customer_id: str, tests: List[str]) -> dict:
        \"\"\"Run diagnostic tests.\"\"\"
        return {"results": {...}, "issues_detected": [...]}

# Real-time language interpreter
interpreter_agent = Agent(
    name="realtime_interpreter",
    model="gemini-live-2.5-flash-native-audio",
    instruction=\"\"\"
    You are a real-time language interpreter.

    **Languages:** English, Spanish, Mandarin, French, German, Japanese

    **Protocol:**
    1. Listen to speaker
    2. Interpret to target language immediately
    3. Maintain speaker's tone and emphasis
    4. Handle technical/domain terms accurately

    **Professional standards:**
    - Neutral, accurate interpretation
    - No editorializing or summarizing
    - Flag unclear terms for clarification
    - Maintain confidentiality
    \"\"\",
)
```
</description>
<files>
- skills/adk-support-agents/SKILL.md
- skills/adk-support-agents/references/escalation-patterns.md
- skills/adk-support-agents/references/ticket-management.md
- skills/adk-support-agents/examples/enterprise-helpdesk.md
- skills/adk-support-agents/examples/technical-support.md
- skills/adk-interpretation-agents/SKILL.md
- skills/adk-interpretation-agents/examples/realtime-interpreter.md
</files>
</task>

## Verification Criteria
- [ ] Vision agents handle real-world visual scenarios
- [ ] Tutoring agents adapt to learner profiles
- [ ] Support system handles multi-tier escalation
- [ ] Interpretation works in real-time
- [ ] All scenarios are production-ready

## Acceptance
Real-world scenario agents solve practical enterprise problems.
