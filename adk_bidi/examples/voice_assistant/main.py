"""
Voice Assistant Example

A complete voice assistant using native audio models with
real-time bidirectional streaming.

Usage:
    python -m adk_bidi.examples.voice_assistant.main

Requirements:
    - GOOGLE_API_KEY environment variable
    - Audio input/output support
"""

import asyncio
import os
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from google.genai import types

from adk_bidi.agents.voice_agent import VoiceAgent, VoicePersonality, VoiceConfig
from adk_bidi.core.streaming_config import StreamingPresets
from adk_bidi.memory.working_memory import WorkingMemory


# Define tools for the assistant
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%I:%M %p")


def get_weather(location: str = "current") -> str:
    """Get weather information for a location."""
    # Simulated weather data
    return f"The weather in {location} is currently 72°F and sunny."


def set_reminder(task: str, time: str) -> str:
    """Set a reminder for a task."""
    return f"Reminder set: '{task}' at {time}"


def search_knowledge(query: str) -> str:
    """Search the knowledge base."""
    # Simulated knowledge search
    return f"Here's what I found about '{query}': This is a helpful response."


def create_voice_assistant() -> VoiceAgent:
    """Create and configure the voice assistant."""
    # Configure voice settings
    voice_config = VoiceConfig(
        personality=VoicePersonality.FRIENDLY,
        speaking_rate="normal",
        enable_emotions=True,
        enable_interruption=True,
        use_native_audio=True,
    )

    # Create working memory for context
    working_memory = WorkingMemory(max_size=20)

    # Create the voice agent
    agent = VoiceAgent(
        name="voice_assistant",
        instruction="""You are a friendly and helpful voice assistant.

Your capabilities:
- Answer questions and have conversations
- Tell the current time
- Provide weather information
- Set reminders
- Search for information

Guidelines:
- Be conversational and natural
- Keep responses concise for voice
- Ask clarifying questions when needed
- Show empathy and understanding
""",
        voice_config=voice_config,
        working_memory=working_memory,
        tools=[
            FunctionTool(get_current_time),
            FunctionTool(get_weather),
            FunctionTool(set_reminder),
            FunctionTool(search_knowledge),
        ],
    )

    return agent


async def run_voice_session():
    """Run an interactive voice session."""
    print("Initializing Voice Assistant...")
    print("Using native audio model: gemini-live-2.5-flash-native-audio")
    print("-" * 50)

    # Create the assistant
    assistant = create_voice_assistant()

    # Create runner
    runner = Runner(
        agent=assistant.adk_agent,
        app_name="voice_assistant_example",
    )

    # Create live request queue
    live_queue = LiveRequestQueue()

    # Get streaming configuration
    run_config = StreamingPresets.native_audio()

    print("\nVoice Assistant is ready!")
    print("Type your messages (or 'quit' to exit)")
    print("-" * 50)

    # For this example, we'll use text input
    # In production, you would stream audio directly

    async def process_responses():
        """Process responses from the assistant."""
        async for event in runner.run_live(
            user_id="demo_user",
            session_id="demo_session",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Handle different event types
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"\nAssistant: {part.text}")
                        if hasattr(part, 'inline_data') and part.inline_data:
                            print("[Audio response received]")

            # Check for turn completion
            if hasattr(event, 'turn_complete') and event.turn_complete:
                print("\n> ", end="", flush=True)

    async def handle_input():
        """Handle user input."""
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    live_queue.close()
                    break

                if user_input.strip():
                    # Send text content
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
        # Get session stats
        stats = assistant.get_voice_stats()
        print("\n" + "-" * 50)
        print("Session Statistics:")
        print(f"  Personality: {stats['personality']}")
        print(f"  Native audio: {stats['use_native_audio']}")
        print(f"  Memory items: {stats['working_memory_size']}")


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  export GOOGLE_API_KEY=your_api_key")
        return

    try:
        asyncio.run(run_voice_session())
    except KeyboardInterrupt:
        print("\nSession interrupted.")


if __name__ == "__main__":
    main()
