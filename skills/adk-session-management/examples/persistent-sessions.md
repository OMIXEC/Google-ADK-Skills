# Persistent Session Examples

Complete examples for implementing persistent sessions in production applications.

## Example 1: Web Application with Database Sessions

```python
from flask import Flask, request, jsonify, session
from google.adk.agents import LlmAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
import os

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Configure session service
session_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
    pool_size=10,
)

# Configure memory service
memory_service = VertexAiMemoryBankService(
    project_id=os.environ["GCP_PROJECT_ID"],
    location="us-central1",
    memory_bank_id="user_memories",
)

# Create agent
def get_user_data(user_id: str) -> dict:
    """Get user account data."""
    # Implementation
    return {"user_id": user_id, "tier": "premium", "joined": "2024-01-01"}

user_data_tool = FunctionTool(get_user_data)

agent = LlmAgent(
    name="customer_assistant",
    model="gemini-2.0-flash-exp",
    tools=[user_data_tool],
    system_instruction="""You are a helpful customer service assistant.
    Remember user preferences and conversation context.
    Provide personalized assistance based on user history.""",
)

# Create runner
runner = Runner(
    agent=agent,
    app_name="customer_support",
    session_service=session_service,
    memory_service=memory_service,
)

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    data = request.json

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    message = data.get("message")
    if not message:
        return jsonify({"error": "Message required"}), 400

    # Generate session ID for this user
    session_id = f"{user_id}_web_session"

    # Run agent
    response = runner.run(
        user_input=message,
        session_id=session_id,
        user_id=user_id,  # For memory storage
        metadata={
            "user_id": user_id,
            "source": "web",
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
        },
    )

    return jsonify({
        "response": response.text,
        "session_id": session_id,
    })

@app.route("/history", methods=["GET"])
def get_history():
    """Get conversation history."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    session_id = f"{user_id}_web_session"

    # Get session data
    session_data = session_service.get_session(session_id)

    return jsonify({
        "session_id": session_id,
        "conversation": session_data["conversation_history"],
        "created_at": session_data["created_at"],
    })

@app.route("/clear-history", methods=["POST"])
def clear_history():
    """Clear conversation history."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    session_id = f"{user_id}_web_session"

    # Delete session
    session_service.delete_session(session_id)

    return jsonify({"message": "History cleared"})

if __name__ == "__main__":
    app.run(debug=False, port=5000)
```

## Example 2: Multi-Channel Bot (Web, Slack, SMS)

```python
from google.adk.agents import LlmAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner

# Shared session service across all channels
session_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
)

# Create agent
agent = LlmAgent(
    name="support_bot",
    model="gemini-2.0-flash-exp",
    system_instruction="You are a helpful support bot available on multiple channels.",
)

runner = Runner(
    agent=agent,
    app_name="multi_channel_bot",
    session_service=session_service,
)

# Web channel handler
def handle_web_message(user_id: str, message: str) -> str:
    """Handle message from web interface."""
    session_id = f"{user_id}_web"

    response = runner.run(
        user_input=message,
        session_id=session_id,
        metadata={
            "channel": "web",
            "user_id": user_id,
        },
    )

    return response.text

# Slack channel handler
def handle_slack_message(user_id: str, message: str, channel_id: str) -> str:
    """Handle message from Slack."""
    session_id = f"{user_id}_slack_{channel_id}"

    response = runner.run(
        user_input=message,
        session_id=session_id,
        metadata={
            "channel": "slack",
            "slack_user": user_id,
            "slack_channel": channel_id,
        },
    )

    return response.text

# SMS channel handler
def handle_sms_message(phone_number: str, message: str) -> str:
    """Handle message from SMS."""
    # Normalize phone number
    normalized_phone = phone_number.replace("+", "").replace("-", "")
    session_id = f"sms_{normalized_phone}"

    response = runner.run(
        user_input=message,
        session_id=session_id,
        metadata={
            "channel": "sms",
            "phone": phone_number,
        },
    )

    return response.text

# User can switch between channels, conversation continues
user_id = "user_123"

# Start on web
response = handle_web_message(user_id, "I need help with my order")
print(f"Web: {response}")

# Continue on Slack
response = handle_slack_message(user_id, "What's the status?", "C123456")
print(f"Slack: {response}")
# Agent remembers the order conversation from web

# Each channel maintains separate session, but could be unified:
def get_unified_session_id(user_id: str) -> str:
    """Get single session ID for user across all channels."""
    return f"{user_id}_unified"

# Then all channels would share the same conversation
```

## Example 3: Session Cleanup Worker

```python
from google.adk.sessions import DatabaseSessionService
from datetime import datetime, timedelta
import schedule
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionCleanupWorker:
    """Background worker for session maintenance."""

    def __init__(self, session_service: DatabaseSessionService):
        self.session_service = session_service

    def cleanup_old_sessions(self, days: int = 30):
        """Delete sessions older than N days."""
        logger.info(f"Starting cleanup of sessions older than {days} days")

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get old sessions
        old_sessions = self.session_service.list_sessions(
            before_date=cutoff_date,
        )

        logger.info(f"Found {len(old_sessions)} old sessions")

        # Delete sessions
        deleted_count = 0
        for session in old_sessions:
            try:
                self.session_service.delete_session(session["session_id"])
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete session {session['session_id']}: {e}")

        logger.info(f"Deleted {deleted_count} old sessions")

    def archive_inactive_sessions(self, days: int = 7):
        """Archive sessions inactive for N days."""
        logger.info(f"Archiving sessions inactive for {days} days")

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get inactive sessions
        inactive_sessions = self.session_service.list_sessions(
            updated_before=cutoff_date,
        )

        archived_count = 0
        for session in inactive_sessions:
            # Move to cold storage (e.g., S3, Cloud Storage)
            try:
                import json
                archive_data = {
                    "session_id": session["session_id"],
                    "data": session,
                    "archived_at": datetime.now().isoformat(),
                }

                # Save to archive (example: file storage)
                archive_path = f"archives/{session['session_id']}.json"
                with open(archive_path, 'w') as f:
                    json.dump(archive_data, f)

                # Delete from active database
                self.session_service.delete_session(session["session_id"])
                archived_count += 1

            except Exception as e:
                logger.error(f"Failed to archive session {session['session_id']}: {e}")

        logger.info(f"Archived {archived_count} inactive sessions")

    def vacuum_database(self):
        """Run database maintenance."""
        logger.info("Running database vacuum")

        # PostgreSQL-specific
        try:
            from sqlalchemy import text
            with self.session_service.engine.connect() as conn:
                conn.execute(text("VACUUM ANALYZE agent_sessions"))
            logger.info("Database vacuum complete")
        except Exception as e:
            logger.error(f"Vacuum failed: {e}")

# Create cleanup worker
session_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
)

worker = SessionCleanupWorker(session_service)

# Schedule cleanup jobs
schedule.every().day.at("02:00").do(worker.cleanup_old_sessions, days=30)
schedule.every().day.at("03:00").do(worker.archive_inactive_sessions, days=7)
schedule.every().sunday.at("04:00").do(worker.vacuum_database)

# Run scheduler
logger.info("Session cleanup worker started")
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## Example 4: Session Migration

```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
import logging

logger = logging.getLogger(__name__)

class SessionMigrator:
    """Migrate sessions between services."""

    def __init__(
        self,
        source_service,
        target_service,
    ):
        self.source = source_service
        self.target = target_service

    def migrate_all_sessions(self):
        """Migrate all sessions from source to target."""
        logger.info("Starting session migration")

        # Get all sessions from source
        sessions = self.source.list_sessions()

        logger.info(f"Found {len(sessions)} sessions to migrate")

        migrated = 0
        failed = 0

        for session in sessions:
            try:
                # Create session in target
                self.target.create_session(
                    session_id=session["session_id"],
                    app_name=session["app_name"],
                    agent_name=session["agent_name"],
                    metadata=session.get("metadata"),
                )

                # Update conversation history
                self.target.update_session(
                    session_id=session["session_id"],
                    conversation_history=session["conversation_history"],
                )

                migrated += 1

                if migrated % 100 == 0:
                    logger.info(f"Migrated {migrated} sessions")

            except Exception as e:
                logger.error(f"Failed to migrate session {session['session_id']}: {e}")
                failed += 1

        logger.info(f"Migration complete: {migrated} migrated, {failed} failed")

# Example: Migrate from in-memory to database
in_memory_service = InMemorySessionService()
db_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
)

migrator = SessionMigrator(in_memory_service, db_service)
migrator.migrate_all_sessions()
```

## Example 5: Session Analytics

```python
from google.adk.sessions import DatabaseSessionService
from datetime import datetime, timedelta
from collections import Counter
import statistics

class SessionAnalytics:
    """Analyze session data for insights."""

    def __init__(self, session_service: DatabaseSessionService):
        self.session_service = session_service

    def get_active_users(self, days: int = 7) -> int:
        """Count active users in last N days."""
        cutoff = datetime.now() - timedelta(days=days)

        sessions = self.session_service.list_sessions(
            updated_after=cutoff,
        )

        # Extract unique user IDs from metadata
        user_ids = set()
        for session in sessions:
            user_id = session.get("metadata", {}).get("user_id")
            if user_id:
                user_ids.add(user_id)

        return len(user_ids)

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics."""
        sessions = self.session_service.list_sessions()

        turn_counts = []
        session_durations = []

        for session in sessions:
            # Count turns
            turns = len(session["conversation_history"])
            turn_counts.append(turns)

            # Calculate duration
            created = datetime.fromisoformat(session["created_at"])
            updated = datetime.fromisoformat(session["updated_at"])
            duration = (updated - created).total_seconds()
            session_durations.append(duration)

        return {
            "total_sessions": len(sessions),
            "avg_turns_per_session": statistics.mean(turn_counts) if turn_counts else 0,
            "median_turns": statistics.median(turn_counts) if turn_counts else 0,
            "avg_duration_seconds": statistics.mean(session_durations) if session_durations else 0,
            "max_turns": max(turn_counts) if turn_counts else 0,
        }

    def get_channel_breakdown(self) -> dict:
        """Get usage by channel."""
        sessions = self.session_service.list_sessions()

        channels = Counter(
            session.get("metadata", {}).get("channel", "unknown")
            for session in sessions
        )

        return dict(channels)

    def get_peak_usage_hours(self) -> dict:
        """Identify peak usage hours."""
        sessions = self.session_service.list_sessions()

        hour_counts = Counter()

        for session in sessions:
            created = datetime.fromisoformat(session["created_at"])
            hour_counts[created.hour] += 1

        # Find peak hours
        peak_hours = hour_counts.most_common(5)

        return {
            "peak_hours": [
                {"hour": hour, "sessions": count}
                for hour, count in peak_hours
            ],
            "hourly_distribution": dict(hour_counts),
        }

# Use analytics
session_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
)

analytics = SessionAnalytics(session_service)

print(f"Active users (7 days): {analytics.get_active_users(7)}")
print(f"Conversation stats: {analytics.get_conversation_stats()}")
print(f"Channel breakdown: {analytics.get_channel_breakdown()}")
print(f"Peak hours: {analytics.get_peak_usage_hours()}")
```

## Example 6: Session Export/Import

```python
import json
from google.adk.sessions import DatabaseSessionService
from pathlib import Path

class SessionExporter:
    """Export and import sessions."""

    def __init__(self, session_service: DatabaseSessionService):
        self.session_service = session_service

    def export_sessions(self, output_dir: str, app_name: str = None):
        """Export sessions to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get sessions
        if app_name:
            sessions = self.session_service.list_sessions(app_name=app_name)
        else:
            sessions = self.session_service.list_sessions()

        # Export each session
        for session in sessions:
            session_file = output_path / f"{session['session_id']}.json"

            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2, default=str)

        print(f"Exported {len(sessions)} sessions to {output_dir}")

    def import_sessions(self, input_dir: str):
        """Import sessions from JSON files."""
        input_path = Path(input_dir)

        session_files = list(input_path.glob("*.json"))

        imported = 0
        for session_file in session_files:
            with open(session_file, 'r') as f:
                session = json.load(f)

            try:
                # Create session
                self.session_service.create_session(
                    session_id=session["session_id"],
                    app_name=session["app_name"],
                    agent_name=session["agent_name"],
                    metadata=session.get("metadata"),
                )

                # Update conversation history
                self.session_service.update_session(
                    session_id=session["session_id"],
                    conversation_history=session["conversation_history"],
                )

                imported += 1

            except Exception as e:
                print(f"Failed to import {session_file}: {e}")

        print(f"Imported {imported} sessions from {input_dir}")

# Usage
session_service = DatabaseSessionService(
    connection_string=os.environ["DATABASE_URL"],
)

exporter = SessionExporter(session_service)

# Export for backup
exporter.export_sessions("backups/2024-01-15", app_name="my_app")

# Import from backup
exporter.import_sessions("backups/2024-01-15")
```

## Best Practices

1. **Use database sessions in production** - Don't rely on in-memory
2. **Implement cleanup** - Remove old sessions regularly
3. **Add metadata** - Track user, channel, device for analytics
4. **Monitor performance** - Watch database query times
5. **Handle errors gracefully** - Session not found shouldn't crash app
6. **Backup sessions** - Export important conversations
7. **Scale horizontally** - Share database across instances
8. **Archive cold data** - Move inactive sessions to cheaper storage
9. **Track metrics** - Monitor active users, conversation length
10. **Secure data** - Encrypt sensitive conversation history
