# Client Integration Examples

**Client implementations for connecting to ADK streaming agents.**

## Overview

Examples for:
- JavaScript/TypeScript web clients
- Python asyncio clients
- React integration
- Mobile clients (React Native)
- Reconnection handling
- Audio capture/playback

## JavaScript Web Client

### Basic Text Client

```javascript
/**
 * Simple text streaming client for web browsers.
 */
class TextStreamingClient {
    constructor(userId, sessionId, options = {}) {
        this.userId = userId;
        this.sessionId = sessionId;
        this.serverUrl = options.serverUrl || 'ws://localhost:8000';
        this.mode = options.mode || 'text';
        this.ws = null;
        this.connected = false;
    }

    connect() {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.serverUrl}/ws/${this.userId}/${this.sessionId}?mode=${this.mode}`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('Connected to streaming agent');
                this.connected = true;
                resolve();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('Disconnected from streaming agent');
                this.connected = false;
                this.handleDisconnect();
            };
        });
    }

    sendMessage(text) {
        if (!this.connected) {
            throw new Error('Not connected to server');
        }

        this.ws.send(JSON.stringify({
            type: 'message',
            text: text,
        }));
    }

    close() {
        if (this.ws) {
            this.ws.send(JSON.stringify({ type: 'close' }));
            this.ws.close();
        }
    }

    // Override these methods in your implementation
    handleMessage(data) {
        if (data.type === 'text') {
            console.log('Agent:', data.text);
        } else if (data.type === 'error') {
            console.error('Error:', data.error);
        }
    }

    handleDisconnect() {
        // Override to handle disconnection
    }
}

// Usage
const client = new TextStreamingClient('user_123', 'session_456');

client.handleMessage = (data) => {
    if (data.type === 'text') {
        document.getElementById('chat').innerHTML += `<p>Agent: ${data.text}</p>`;
    }
};

await client.connect();
client.sendMessage('Hello, how are you?');
```

### Audio Streaming Client

```javascript
/**
 * Audio streaming client with microphone capture.
 */
class AudioStreamingClient {
    constructor(userId, sessionId, options = {}) {
        this.userId = userId;
        this.sessionId = sessionId;
        this.serverUrl = options.serverUrl || 'ws://localhost:8000';
        this.ws = null;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 24000
        });
        this.mediaStream = null;
        this.mediaRecorder = null;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.serverUrl}/ws/${this.userId}/${this.sessionId}?mode=audio`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = async () => {
                console.log('Audio connection established');
                await this.startAudioCapture();
                resolve();
            };

            this.ws.onmessage = async (event) => {
                // Audio response from agent
                if (event.data instanceof Blob) {
                    await this.playAudio(event.data);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('Audio connection closed');
                this.stopAudioCapture();
            };
        });
    }

    async startAudioCapture() {
        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                }
            });

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.mediaStream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
                    // Send audio to server
                    this.ws.send(event.data);
                }
            };

            // Start recording (send chunks every 100ms)
            this.mediaRecorder.start(100);
            console.log('Audio capture started');

        } catch (error) {
            console.error('Failed to start audio capture:', error);
            throw error;
        }
    }

    async playAudio(audioBlob) {
        try {
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start(0);

        } catch (error) {
            console.error('Failed to play audio:', error);
        }
    }

    stopAudioCapture() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }

        console.log('Audio capture stopped');
    }

    close() {
        this.stopAudioCapture();
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const audioClient = new AudioStreamingClient('user_123', 'session_456');
await audioClient.connect();

// Audio will stream automatically
// Close when done
// audioClient.close();
```

## React Integration

### Text Chat Component

```typescript
/**
 * React component for text streaming chat.
 */
import React, { useState, useEffect, useRef } from 'react';

interface Message {
  type: 'user' | 'agent';
  text: string;
  timestamp: Date;
}

const StreamingChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/user_123/session_456?mode=text');

    ws.onopen = () => {
      console.log('Connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'text') {
        setMessages(prev => [
          ...prev,
          {
            type: 'agent',
            text: data.text,
            timestamp: new Date(),
          }
        ]);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected');
      setConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return;

    // Add user message to UI
    setMessages(prev => [
      ...prev,
      {
        type: 'user',
        text: input,
        timestamp: new Date(),
      }
    ]);

    // Send to agent
    wsRef.current.send(JSON.stringify({
      type: 'message',
      text: input,
    }));

    setInput('');
  };

  return (
    <div className="streaming-chat">
      <div className="chat-header">
        <h2>Streaming Agent Chat</h2>
        <span className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <div className="message-content">{msg.text}</div>
            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={!connected}
        />
        <button onClick={sendMessage} disabled={!connected}>
          Send
        </button>
      </div>
    </div>
  );
};

export default StreamingChat;
```

### Custom Hook for WebSocket

```typescript
/**
 * Custom React hook for WebSocket streaming.
 */
import { useEffect, useRef, useState } from 'react';

interface UseStreamingOptions {
  userId: string;
  sessionId: string;
  mode?: 'text' | 'audio' | 'multimodal';
  serverUrl?: string;
  autoReconnect?: boolean;
}

export const useStreaming = (options: UseStreamingOptions) => {
  const {
    userId,
    sessionId,
    mode = 'text',
    serverUrl = 'ws://localhost:8000',
    autoReconnect = true,
  } = options;

  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = () => {
    const wsUrl = `${serverUrl}/ws/${userId}/${sessionId}?mode=${mode}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnected(false);

      // Auto-reconnect
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [userId, sessionId, mode]);

  const sendMessage = (text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        text: text,
      }));
    }
  };

  const sendAudio = (audioData: Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData);
    }
  };

  return {
    connected,
    messages,
    sendMessage,
    sendAudio,
  };
};

// Usage
const ChatComponent = () => {
  const { connected, messages, sendMessage } = useStreaming({
    userId: 'user_123',
    sessionId: 'session_456',
    mode: 'text',
  });

  return (
    <div>
      <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>
      {messages.map((msg, i) => (
        <div key={i}>{msg.text}</div>
      ))}
      <button onClick={() => sendMessage('Hello')}>
        Send
      </button>
    </div>
  );
};
```

## Python Client

### Asyncio Client

```python
"""Python asyncio client for streaming agent."""
import asyncio
import websockets
import json

class StreamingClient:
    """Async Python client for ADK streaming agent."""

    def __init__(self, user_id: str, session_id: str, mode: str = "text"):
        self.user_id = user_id
        self.session_id = session_id
        self.mode = mode
        self.server_url = "ws://localhost:8000"
        self.ws = None

    async def connect(self):
        """Connect to WebSocket server."""
        uri = f"{self.server_url}/ws/{self.user_id}/{self.session_id}?mode={self.mode}"
        self.ws = await websockets.connect(uri)
        print(f"Connected to {uri}")

    async def send_message(self, text: str):
        """Send text message to agent."""
        if not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "message",
            "text": text,
        }))

    async def receive_messages(self):
        """Receive messages from agent."""
        if not self.ws:
            raise RuntimeError("Not connected")

        async for message in self.ws:
            data = json.loads(message)
            if data["type"] == "text":
                print(f"Agent: {data['text']}")
                yield data["text"]

    async def close(self):
        """Close connection."""
        if self.ws:
            await self.ws.send(json.dumps({"type": "close"}))
            await self.ws.close()

# Usage
async def main():
    client = StreamingClient("user_123", "session_456", mode="text")

    await client.connect()

    # Send message and receive response
    await client.send_message("Hello, how are you?")

    async for response in client.receive_messages():
        print(f"Received: {response}")
        break  # Exit after first response

    await client.close()

asyncio.run(main())
```

### Interactive Python Client

```python
"""Interactive command-line streaming client."""
import asyncio
import websockets
import json
import sys

async def interactive_client():
    """Run interactive streaming session."""
    uri = "ws://localhost:8000/ws/user_123/session_456?mode=text"

    async with websockets.connect(uri) as websocket:
        print("Connected! Type 'exit' to quit.")

        async def send_messages():
            """Handle user input."""
            while True:
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "\nYou: "
                    )

                    if user_input.lower() in ['exit', 'quit']:
                        await websocket.send(json.dumps({"type": "close"}))
                        break

                    await websocket.send(json.dumps({
                        "type": "message",
                        "text": user_input,
                    }))

                except Exception as e:
                    print(f"Input error: {e}")
                    break

        async def receive_messages():
            """Handle agent responses."""
            async for message in websocket:
                try:
                    data = json.loads(message)

                    if data["type"] == "text":
                        print(f"\nAgent: {data['text']}")

                except Exception as e:
                    print(f"Receive error: {e}")

        # Run both tasks
        await asyncio.gather(send_messages(), receive_messages())

asyncio.run(interactive_client())
```

## Reconnection Handling

### JavaScript Auto-Reconnect

```javascript
/**
 * WebSocket client with automatic reconnection.
 */
class ReconnectingWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectDelay = options.reconnectDelay || 3000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectAttempts = 0;
        this.ws = null;
        this.shouldReconnect = true;
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('Connected');
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('Connection closed');

                if (this.shouldReconnect &&
                    this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);

                    setTimeout(() => {
                        this.connect();
                    }, this.reconnectDelay);
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    console.error('Max reconnection attempts reached');
                    this.handleMaxReconnectAttemptsReached();
                }
            };
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.error('WebSocket is not connected');
        }
    }

    close() {
        this.shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
        }
    }

    // Override these methods
    handleMessage(data) {
        console.log('Received:', data);
    }

    handleMaxReconnectAttemptsReached() {
        console.error('Failed to reconnect');
    }
}

// Usage
const client = new ReconnectingWebSocket(
    'ws://localhost:8000/ws/user_123/session_456?mode=text',
    {
        reconnectDelay: 3000,
        maxReconnectAttempts: 5,
    }
);

client.handleMessage = (data) => {
    const parsed = JSON.parse(data);
    console.log('Agent:', parsed.text);
};

await client.connect();
```

## See Also

- FastAPI WebSocket Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/fastapi-websocket.md
- Text Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/text-streaming.md
- Audio Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md
