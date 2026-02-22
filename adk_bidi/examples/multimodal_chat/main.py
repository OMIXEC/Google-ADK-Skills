"""
Multimodal Chat Example

A multimodal chat application supporting text, audio, and images
with real-time bidirectional streaming.

Usage:
    python -m adk_bidi.examples.multimodal_chat.main

Requirements:
    - GOOGLE_API_KEY environment variable
"""

import asyncio
import os
import base64
from pathlib import Path
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from google.genai import types

from adk_bidi.agents.multimodal_agent import (
    MultimodalAgent,
    MultimodalConfig,
    VisionAgent,
)
from adk_bidi.core.streaming_config import StreamingPresets
from adk_bidi.memory.working_memory import WorkingMemory


# Define tools for the assistant
def analyze_image_content(description: str) -> str:
    """Provide analysis of image content."""
    return f"Image analysis: {description}"


def transcribe_audio(audio_info: str) -> str:
    """Transcribe audio content."""
    return f"Audio transcription: {audio_info}"


def search_similar_images(query: str) -> str:
    """Search for similar images."""
    return f"Found similar images for: {query}"


def create_multimodal_assistant() -> MultimodalAgent:
    """Create and configure the multimodal assistant."""
    # Configure multimodal settings
    config = MultimodalConfig(
        enable_text=True,
        enable_audio=True,
        enable_image=True,
        enable_video=False,
        response_modalities=["TEXT", "AUDIO"],
        image_analysis_detail="high",
    )

    # Create working memory
    working_memory = WorkingMemory(max_size=25)

    # Create the multimodal agent
    agent = MultimodalAgent(
        name="multimodal_assistant",
        instruction="""You are a multimodal assistant that can see, hear, and read.

Your capabilities:
- Analyze and describe images in detail
- Process and respond to audio input
- Engage in text-based conversation
- Combine information from multiple modalities

Guidelines:
- When you receive an image, describe what you see
- When you receive audio, acknowledge what you heard
- Reference specific details from images and audio
- Integrate information across modalities
- Be descriptive and thorough with visual content
""",
        multimodal_config=config,
        working_memory=working_memory,
        tools=[
            FunctionTool(analyze_image_content),
            FunctionTool(transcribe_audio),
            FunctionTool(search_similar_images),
        ],
    )

    return agent


def load_image(image_path: str) -> bytes:
    """Load an image file and return bytes."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    return path.read_bytes()


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64."""
    return base64.b64encode(image_bytes).decode("utf-8")


async def run_multimodal_session():
    """Run an interactive multimodal session."""
    print("Initializing Multimodal Chat...")
    print("Using model: gemini-2.0-flash-live-001")
    print("-" * 50)

    # Create the assistant
    assistant = create_multimodal_assistant()

    # Create runner
    runner = Runner(
        agent=assistant.adk_agent,
        app_name="multimodal_chat_example",
    )

    # Create live request queue
    live_queue = LiveRequestQueue()

    # Get streaming configuration
    run_config = StreamingPresets.text_and_audio()

    print("\nMultimodal Chat is ready!")
    print("Commands:")
    print("  text: <message>     - Send text message")
    print("  image: <file_path>  - Send an image")
    print("  status              - Show modality status")
    print("  quit                - Exit")
    print("-" * 50)

    async def process_responses():
        """Process responses from the assistant."""
        async for event in runner.run_live(
            user_id="demo_user",
            session_id="demo_session",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Process the event through the agent
            event = await assistant.process_event(event)

            # Handle response content
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"\nAssistant: {part.text}")
                        if hasattr(part, 'inline_data') and part.inline_data:
                            mime_type = part.inline_data.mime_type
                            if mime_type.startswith('audio/'):
                                print("[Audio response]")
                            elif mime_type.startswith('image/'):
                                print("[Image response]")

            if hasattr(event, 'turn_complete') and event.turn_complete:
                print("\n> ", end="", flush=True)

    async def handle_input():
        """Handle user input."""
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )

                user_input = user_input.strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    live_queue.close()
                    break

                if user_input.lower() == 'status':
                    summary = assistant.get_modality_summary()
                    print(f"\n{summary}\n")
                    continue

                if user_input.startswith('image:'):
                    # Handle image input
                    image_path = user_input[6:].strip()
                    try:
                        image_bytes = load_image(image_path)
                        await assistant.process_image(
                            image_bytes,
                            description=f"Image from {image_path}"
                        )

                        # Send image with text prompt
                        mime_type = "image/jpeg"
                        if image_path.lower().endswith('.png'):
                            mime_type = "image/png"

                        blob = types.Blob(
                            mime_type=mime_type,
                            data=image_bytes
                        )
                        live_queue.send_realtime(blob)

                        # Ask about the image
                        content = types.Content(
                            parts=[types.Part(text="What do you see in this image?")]
                        )
                        live_queue.send_content(content)
                        print(f"[Sent image: {image_path}]")

                    except FileNotFoundError as e:
                        print(f"Error: {e}")
                    except Exception as e:
                        print(f"Error processing image: {e}")
                    continue

                if user_input.startswith('text:'):
                    user_input = user_input[5:].strip()

                if user_input:
                    # Process text through agent
                    await assistant.process_text(user_input)

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
        stats = assistant.get_multimodal_stats()
        print("\n" + "-" * 50)
        print("Session Statistics:")
        print(f"  Active modalities: {stats['active_modalities']}")
        print(f"  Images received: {stats['images_received']}")
        print(f"  Audio chunks: {stats['audio_chunks']}")
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
        asyncio.run(run_multimodal_session())
    except KeyboardInterrupt:
        print("\nSession interrupted.")


if __name__ == "__main__":
    main()
