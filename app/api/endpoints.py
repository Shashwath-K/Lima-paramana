from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
from app.services.llm_service import generate_docstring
from app.services.rpa_service import type_docstring
from datetime import datetime

router = APIRouter()

# In-memory history for the dashboard view
history: List[Dict] = []

class GenerationRequest(BaseModel):
    code_snippet: str

class GenerationResponse(BaseModel):
    status: str
    message: str
    docstring: str = ""

@router.post("/generate-doc", response_model=GenerationResponse)
async def api_generate_doc(req: GenerationRequest, background_tasks: BackgroundTasks):
    """
    Receives code snippet, creates docstring using LLM, and triggers RPA typing in the background.
    """
    try:
        # Generate docstring
        docstring = await generate_docstring(req.code_snippet)
        
        # Record history
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "code": (req.code_snippet[:150] + "...") if len(req.code_snippet) > 150 else req.code_snippet,
            "docstring": (docstring[:150] + "...") if len(docstring) > 150 else docstring
        })
        
        # We process typing in the background so the endpoint returns immediately
        background_tasks.add_task(type_docstring, docstring)
        
        return GenerationResponse(status="success", message="Ghost-typing initiated", docstring=docstring)
    except Exception as e:
        return GenerationResponse(status="error", message=str(e))
