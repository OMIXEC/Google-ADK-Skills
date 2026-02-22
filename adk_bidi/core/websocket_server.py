"""
WebSocket Server - FastAPI WebSocket patterns for multi-agent streaming.

Provides production-ready WebSocket server implementations for
bidirectional streaming with multi-agent coordination.
"""

import asyncio
import json
import base64
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types

from adk_bidi.core.streaming_config import StreamingPresets


@dataclass
class ConnectionInfo:
    """Information about an active WebSocket connection."""
    websocket: WebSocket
    user_id: str
    session_id: str
    runner: Runner
    queue: LiveRequestQueue
    connected_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    is_audio_mode: bool = False


class MultiAgentWebSocketServer:
    """
    WebSocket server for multi-agent real-time interactions.

    Handles bidirectional streaming between clients and ADK agents,
    supporting text, audio, and multimodal communication.

    Example:
        server = MultiAgentWebSocketServer(root_agent)

        @app.websocket("/ws/{user_id}/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
            await server.handle_connection(websocket, user_id, session_id)
    """

    def __init__(
        self,
        agent: Agent,
        app_name: str = "multi_agent_bidi",
        default_modality: str = "TEXT",
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
    ):
        """
        Initialize the WebSocket server.

        Args:
            agent: The root ADK agent (or supervisor)
            app_name: Application name for the runner
            default_modality: Default response modality
            on_connect: Callback when client connects
            on_disconnect: Callback when client disconnects
            on_message: Callback when message received
        """
        self.agent = agent
        self.app_name = app_name
        self.default_modality = default_modality
        self.sessions: Dict[str, ConnectionInfo] = {}

        # Callbacks
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: str,
        is_audio: bool = False,
    ) -> None:
        """
        Handle a WebSocket connection lifecycle.

        Args:
            websocket: The WebSocket connection
            user_id: User identifier
            session_id: Session identifier
            is_audio: Whether to use audio mode
        """
        await websocket.accept()

        # Create runner and queue
        runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
        )
        live_queue = LiveRequestQueue()

        # Select configuration based on mode
        if is_audio:
            run_config = StreamingPresets.voice_only()
        else:
            run_config = StreamingPresets.text_and_audio()

        # Store connection info
        conn_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            runner=runner,
            queue=live_queue,
            is_audio_mode=is_audio,
        )
        self.sessions[session_id] = conn_info

        # Notify connection
        if self.on_connect:
            await self.on_connect(conn_info)

        print(f"Client connected: user={user_id}, session={session_id}, audio={is_audio}")

        # Run bidirectional tasks
        async def upstream_task():
            """Client -> Agent: Receive messages from WebSocket and forward to agent."""
            try:
                while True:
                    message = await websocket.receive()
                    conn_info.message_count += 1

                    if "bytes" in message:
                        # Binary audio data
                        audio_blob = types.Blob(
                            mime_type="audio/pcm;rate=16000",
                            data=message["bytes"]
                        )
                        live_queue.send_realtime(audio_blob)

                    elif "text" in message:
                        # JSON text message
                        try:
                            data = json.loads(message["text"])
                            await self._process_text_message(data, live_queue, conn_info)
                        except json.JSONDecodeError:
                            # Plain text
                            content = types.Content(
                                role="user",
                                parts=[types.Part(text=message["text"])]
                            )
                            live_queue.send_content(content)

                    # Callback
                    if self.on_message:
                        await self.on_message(conn_info, message)

            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"Upstream error: {e}")

        async def downstream_task():
            """Agent -> Client: Stream events from agent to WebSocket."""
            try:
                async for event in runner.run_live(
                    user_id=user_id,
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    # Send event to client
                    await websocket.send_text(
                        event.model_dump_json(exclude_none=True, by_alias=True)
                    )
            except Exception as e:
                print(f"Downstream error: {e}")

        try:
            await asyncio.gather(upstream_task(), downstream_task())
        finally:
            # Cleanup
            live_queue.close()
            if session_id in self.sessions:
                del self.sessions[session_id]

            # Notify disconnection
            if self.on_disconnect:
                await self.on_disconnect(conn_info)

            print(f"Client disconnected: user={user_id}, session={session_id}")

    async def _process_text_message(
        self,
        data: Dict[str, Any],
        queue: LiveRequestQueue,
        conn_info: ConnectionInfo,
    ) -> None:
        """Process a JSON text message."""
        msg_type = data.get("type", "text")

        if msg_type == "text":
            # Text content
            content = types.Content(
                role="user",
                parts=[types.Part(text=data.get("text", ""))]
            )
            queue.send_content(content)

        elif msg_type == "audio":
            # Base64-encoded audio
            audio_data = base64.b64decode(data.get("data", ""))
            mime_type = data.get("mime_type", "audio/pcm;rate=16000")
            audio_blob = types.Blob(mime_type=mime_type, data=audio_data)
            queue.send_realtime(audio_blob)

        elif msg_type == "image":
            # Base64-encoded image
            image_data = base64.b64decode(data.get("data", ""))
            mime_type = data.get("mime_type", "image/jpeg")
            image_blob = types.Blob(mime_type=mime_type, data=image_data)
            queue.send_realtime(image_blob)

        elif msg_type == "activity_start":
            queue.send_activity_start()

        elif msg_type == "activity_end":
            queue.send_activity_end()

    def get_active_sessions(self) -> Dict[str, dict]:
        """Get information about all active sessions."""
        return {
            session_id: {
                "user_id": info.user_id,
                "connected_at": info.connected_at.isoformat(),
                "message_count": info.message_count,
                "is_audio_mode": info.is_audio_mode,
            }
            for session_id, info in self.sessions.items()
        }

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        for conn_info in self.sessions.values():
            try:
                await conn_info.websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Broadcast error to {conn_info.session_id}: {e}")

    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific session."""
        if session_id not in self.sessions:
            return False
        try:
            await self.sessions[session_id].websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            print(f"Send error to {session_id}: {e}")
            return False


def create_websocket_app(
    agent: Agent,
    app_name: str = "bidi_agent",
    static_dir: Optional[str] = None,
) -> FastAPI:
    """
    Create a FastAPI application with WebSocket support for ADK agents.

    Args:
        agent: The ADK agent to serve
        app_name: Application name
        static_dir: Optional directory for static files

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(title=app_name)
    server = MultiAgentWebSocketServer(agent, app_name)

    if static_dir:
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        import os

        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/")
        async def root():
            return FileResponse(os.path.join(static_dir, "index.html"))

    @app.websocket("/ws/{user_id}/{session_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        user_id: str,
        session_id: str,
        is_audio: str = "false",
    ):
        await server.handle_connection(
            websocket,
            user_id,
            session_id,
            is_audio=is_audio.lower() == "true",
        )

    @app.get("/sessions")
    async def get_sessions():
        return server.get_active_sessions()

    @app.get("/health")
    async def health():
        return {"status": "healthy", "active_sessions": len(server.sessions)}

    return app
