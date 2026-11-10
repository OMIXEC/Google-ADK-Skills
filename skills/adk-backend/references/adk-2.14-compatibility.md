# ADK 2.14 backend (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. Build an App with cross-cutting plugins and pass it to Runner(app=...). Runner(plugins=...) is deprecated; supplying both app and plugins raises ValueError. Legacy Runner(app_name, agent) remains but bypasses stricter App validation.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py ; https://github.com/google/adk-python/blob/v2.14.0/pyproject.toml
