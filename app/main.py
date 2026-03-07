from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.endpoints import router as api_router
from app.api.endpoints import history
from app.core.config import settings
import os

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api")

# Ensure templates and static directories exist
os.makedirs("app/templates", exist_ok=True)
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def landing(request: Request):
    """
    Renders the landing page.
    """
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/upload-mode")
async def upload_mode(request: Request):
    """
    Renders the file upload tool, passing reversed history (latest first).
    """
    return templates.TemplateResponse("upload_mode.html", {
        "request": request,
        "history": list(reversed(history))
    })

@app.get("/live-mode")
async def live_mode(request: Request):
    """
    Renders the live generation editor tool.
    """
    return templates.TemplateResponse("live_mode.html", {
        "request": request,
        "history": list(reversed(history)) # We can share the same history or omit it
    })

@app.get("/repo-mode")
async def repo_mode(request: Request):
    """
    Renders the Repository Upload & Processing tool.
    """
    return templates.TemplateResponse("repo_mode.html", {
        "request": request
    })

if __name__ == "__main__":
    import uvicorn
    # Make sure to run this file from the project root!
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
