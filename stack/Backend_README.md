# Backend

Overview

1. Purpose: The backend provides API endpoints for code analysis, LLM integration, repository processing, and background tasks.

Key components

1. Application entry point: `app/main.py`.
2. API routes and business logic: `app/api/endpoints.py`.
3. Configuration: `app/core/config.py`.
4. Background services and utilities: `app/services/`.

How the server runs

1. The project uses FastAPI and Uvicorn. Run the server from the project root with:

   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Configuration values are provided by `app/core/config.py` and can be overridden using a `.env` file in the project root. Typical entries:

   1. `PROJECT_NAME`
   2. `HOST`
   3. `PORT`
   4. `LLM_PROVIDER`
   5. `OLLAMA_MODEL`

API surface highlights

1. Generation and document flow is exposed under the `/api` prefix.
2. Important endpoints and their responsibilities are in `app/api/endpoints.py`:
   1. `/api/generate-doc` to generate docstrings and initiate background typing.
   2. `/api/extract-symbols` to parse code and return items to document.
   3. `/api/generate-comment` to request a formatted docstring or commented block.
   4. `/api/explain-code` to request an explanation of a code snippet.
   5. `/api/repo/*` endpoints to manage repo upload, status, diffs, and commit download.

Background processing

1. Endpoints use FastAPI `BackgroundTasks` to offload long running work such as repository processing and RPA typing.

Security and sandboxing

1. The `/api/run-code` endpoint executes code in a temporary file using the host Python interpreter and limits execution time to protect the server. Treat this area carefully when running untrusted input.

Testing and debugging

1. Unit tests and integration tests should call endpoints using the FastAPI test client.
2. There is a test in `tests/test_ollama.py` which demonstrates an external LLM integration test pattern.

Deployment notes

1. For production expose the app behind a reverse proxy.
2. Configure environment variables for `HOST` and `PORT` and set `LLM_PROVIDER` appropriately.
3. Consider worker queues for large repo jobs rather than in process background tasks for scale.
