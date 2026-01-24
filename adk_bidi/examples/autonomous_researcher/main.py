"""
Autonomous Researcher Example

A self-reasoning research agent that autonomously gathers,
analyzes, and synthesizes information.

Usage:
    python -m adk_bidi.examples.autonomous_researcher.main

Requirements:
    - GOOGLE_API_KEY environment variable
"""

import asyncio
import os
from datetime import datetime
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from google.genai import types

from adk_bidi.agents.autonomous_agent import (
    AutonomousAgent,
    ResearchAgent,
    ReasoningPhase,
)
from adk_bidi.core.streaming_config import StreamingPresets
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.persistent_store import InMemoryPersistentStore


# Simulated research tools
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    # Simulated search results
    return f"""Search results for: "{query}"
1. Recent advances in {query} - Journal of AI Research
2. {query}: A comprehensive overview - Tech Blog
3. Understanding {query} - Educational Resource
4. {query} trends in 2024 - Industry Report
5. Expert insights on {query} - Research Paper"""


def fetch_article(url: str) -> str:
    """Fetch and extract article content."""
    # Simulated article content
    return f"""Article from {url}:
This article discusses the topic in detail, covering key concepts,
recent developments, and future directions. The research shows
significant progress in the field with practical applications."""


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arxiv for academic papers."""
    # Simulated arxiv results
    return f"""ArXiv papers for: "{query}"
1. [2024.12345] "{query}: New Approaches" - Smith et al.
   Abstract: Novel methods for improving...
2. [2024.12346] "Advances in {query}" - Johnson et al.
   Abstract: We present a comprehensive study...
3. [2024.12347] "{query} Systems" - Williams et al.
   Abstract: This paper introduces..."""


def summarize_findings(content: str, max_length: int = 200) -> str:
    """Summarize research findings."""
    return f"Summary: {content[:max_length]}..."


def save_research_notes(topic: str, notes: str) -> str:
    """Save research notes to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_{topic.replace(' ', '_')}_{timestamp}.md"
    # In production, this would actually save to file
    return f"Notes saved to {filename}"


def create_autonomous_researcher() -> AutonomousAgent:
    """Create and configure the autonomous researcher."""
    # Create persistent memory for long-term knowledge
    persistent_memory = InMemoryPersistentStore(namespace="research")

    # Create working memory with larger capacity
    working_memory = WorkingMemory(max_size=30)

    # Create the autonomous agent
    agent = AutonomousAgent(
        name="researcher",
        goal="Research topics thoroughly and produce comprehensive summaries",
        instruction="""You are an autonomous research agent.

Your research methodology:
1. OBSERVE: Understand the research topic and requirements
2. THINK: Plan your research approach
3. PLAN: Create a structured research plan
4. ACT: Execute searches and gather information
5. REFLECT: Evaluate findings and identify gaps

Research guidelines:
- Start with broad searches, then narrow down
- Verify information from multiple sources
- Distinguish between facts and opinions
- Cite sources when presenting findings
- Identify areas needing further research

Always explain your reasoning at each step.
Use the think() tool to record your observations and reasoning.
Use create_plan() to structure your research approach.
Store important findings in long-term memory.
""",
        model="gemini-live-2.5-flash-native-audio",
        max_thoughts=100,
        enable_proactivity=True,
        working_memory=working_memory,
        persistent_memory=persistent_memory,
        tools=[
            FunctionTool(web_search),
            FunctionTool(fetch_article),
            FunctionTool(search_arxiv),
            FunctionTool(summarize_findings),
            FunctionTool(save_research_notes),
        ],
    )

    return agent


async def run_research_session():
    """Run an interactive research session."""
    print("Initializing Autonomous Researcher...")
    print("Using model: gemini-live-2.5-flash-native-audio")
    print("-" * 50)

    # Create the researcher
    researcher = create_autonomous_researcher()

    # Create runner
    runner = Runner(
        agent=researcher.adk_agent,
        app_name="autonomous_researcher_example",
    )

    # Create live request queue
    live_queue = LiveRequestQueue()

    # Get streaming configuration with proactive behavior
    run_config = StreamingPresets.autonomous_proactive()

    print(f"\nAutonomous Researcher is ready!")
    print(f"Goal: {researcher.goal}")
    print("\nCommands:")
    print("  research: <topic>   - Start researching a topic")
    print("  status              - Show reasoning summary")
    print("  plan                - Show current research plan")
    print("  progress            - Show goal progress")
    print("  quit                - Exit")
    print("-" * 50)

    async def process_responses():
        """Process responses from the researcher."""
        async for event in runner.run_live(
            user_id="demo_user",
            session_id="demo_session",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Process through autonomous agent
            event = await researcher.process_event(event)

            # Handle response content
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"\nResearcher: {part.text}")

            if hasattr(event, 'turn_complete') and event.turn_complete:
                # Show current phase after each turn
                phase = researcher.current_phase.value
                progress = researcher.goal_progress
                print(f"\n[Phase: {phase} | Progress: {progress:.0%}]")
                print("> ", end="", flush=True)

    async def handle_input():
        """Handle user input."""
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )

                user_input = user_input.strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Ending research session...")
                    live_queue.close()
                    break

                if user_input.lower() == 'status':
                    summary = researcher.get_reasoning_summary()
                    print(f"\n{summary}\n")
                    continue

                if user_input.lower() == 'plan':
                    plan = researcher.get_current_plan()
                    print(f"\n{plan}\n")
                    continue

                if user_input.lower() == 'progress':
                    stats = researcher.get_autonomous_stats()
                    print(f"\nProgress: {stats['goal_progress']:.0%}")
                    print(f"Phase: {stats['current_phase']}")
                    print(f"Actions: {stats['action_count']}")
                    print(f"Thoughts: {stats['thoughts_count']}")
                    print(f"Plan status: {stats['plan_status']}\n")
                    continue

                if user_input.startswith('research:'):
                    topic = user_input[9:].strip()
                    if topic:
                        # Send research request
                        content = types.Content(
                            parts=[types.Part(text=f"Research this topic thoroughly: {topic}")]
                        )
                        live_queue.send_content(content)
                        print(f"[Starting research on: {topic}]")
                    continue

                if user_input:
                    # Send as general query
                    content = types.Content(
                        parts=[types.Part(text=user_input)]
                    )
                    live_queue.send_content(content)

            except EOFError:
                live_queue.close()
                break

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            process_responses(),
            handle_input(),
            return_exceptions=True,
        )
    except Exception as e:
        print(f"Session ended: {e}")
    finally:
        # Final summary
        stats = researcher.get_autonomous_stats()
        print("\n" + "=" * 50)
        print("RESEARCH SESSION SUMMARY")
        print("=" * 50)
        print(f"Goal: {stats['goal']}")
        print(f"Final progress: {stats['goal_progress']:.0%}")
        print(f"Total actions: {stats['action_count']}")
        print(f"Thoughts recorded: {stats['thoughts_count']}")
        print(f"Plan status: {stats['plan_status']}")
        print("\n" + researcher.get_reasoning_summary())


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  export GOOGLE_API_KEY=your_api_key")
        return

    try:
        asyncio.run(run_research_session())
    except KeyboardInterrupt:
        print("\nResearch session interrupted.")


if __name__ == "__main__":
    main()
