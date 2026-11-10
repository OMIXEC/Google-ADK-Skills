# ADK 2.14 runtime (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. Register cross-cutting plugins on App and pass app=app to Runner; Runner(plugins=...) is deprecated, and combining app with plugins raises ValueError. Prefer App over the legacy Runner(app_name, agent) compatibility path, which has looser validation.

InMemorySessionService.append_event deduplicates equal redeliveries by event ID; current DatabaseSessionService does not. Do not assume persistent-session event-ID deduplication; make retry behavior explicit.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/sessions/in_memory_session_service.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/sessions/database_session_service.py
