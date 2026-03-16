# Frontend

Overview

1. Purpose: The frontend provides the browser user interface for interacting with the application features such as live generation, repository processing, and file upload.

2. Primary responsibilities:
   1. Render pages and UI controls.
   2. Send user requests to the backend API.
   3. Present LLM results and previews to the user.

Repository layout and key files

1. Templates and pages are located under `app/templates`.
2. Static assets are located under `app/static` and `app/static/css`.
3. Common pages to review or edit:
   1. `app/templates/landing.html`
   2. `app/templates/live_mode.html`
   3. `app/templates/upload_mode.html`
   4. `app/templates/repo_mode.html`

How to run locally

1. Ensure the backend is running. Use the command below from the project root:

   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Open a browser and go to `http://127.0.0.1:8000/` to view the landing page.

Development notes

1. Template rendering is performed by Jinja2 via `app/main.py`.
2. To change styling, edit files in `app/static/css` and then reload the browser.
3. The UI expects API endpoints to be available under the `/api` prefix. These endpoints are defined in `app/api/endpoints.py`.

Testing and verification

1. Verify templates load correctly by visiting the root route.
2. Use browser developer tools to inspect network requests to `/api` endpoints when interacting with the UI.

Troubleshooting

1. If templates do not render, confirm `app/templates` exists and contains the expected files.
2. If static files do not load, confirm `app/static` exists and the server mounted static files. See `app/main.py` for static mount configuration.

Notes for contributors

1. Keep markup semantic and accessible.
2. Keep CSS modular under `app/static/css/components` for component level styles.
