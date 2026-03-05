from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.endpoints import router as api_router
from app.api.endpoints import history
from app.core.config import settings
import os

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api")

# Ensure templates directory exists for Jinja2
os.makedirs("app/templates", exist_ok=True)
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def dashboard(request: Request):
    """
    Renders the lightweight HTML dashboard using Jinja2 templates,
    passing reversed history (latest first).
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": list(reversed(history))
    })

if __name__ == "__main__":
    import uvicorn
    # Make sure to run this file from the project root!
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
