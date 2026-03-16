# Services

Overview

1. Purpose: The services directory contains domain logic and integrations that the API uses. Each service is responsible for a specific concern such as LLM calls, repository processing, parser logic, or RPA typing.

Key modules in this repository

1. `app/services/llm_service.py` handles LLM prompts and responses.
2. `app/services/git_service.py` handles repository job lifecycle and git operations.
3. `app/services/parser_service.py` extracts functions and classes from Python code using AST heuristics.
4. `app/services/rpa_service.py` simulates ghost typing or automations.
5. `app/services/sidebar_service.py` exposes heuristics for extracting concepts and similarity analysis.

Design recommendations

1. Keep each service focused and single responsibility.
2. Expose async functions where IO is expected.
3. Encapsulate external calls and make them mockable for tests.

Testing and maintenance

1. Unit tests should mock network and local runtime dependencies.
2. For `git_service.py` create integration tests that use a temporary repository created at test time.

Error handling and logging

1. Use the standard Python `logging` module across services to provide consistent logs.
2. Catch and surface errors in a way that API endpoints can return meaningful messages while avoiding leaking internal details.

Extensibility

1. To add a new integration, add a new file under `app/services` and document its public functions here.
2. Ensure new services register no global side effects at import time to keep tests predictable.
