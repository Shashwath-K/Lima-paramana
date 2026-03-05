from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.llm_service import generate_docstring
from app.services.rpa_service import type_docstring
from app.services.parser_service import extract_functions_and_classes
from datetime import datetime
import subprocess
import tempfile
import os

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

class ExtractRequest(BaseModel):
    code: str

@router.post("/extract-symbols")
async def api_extract_symbols(req: ExtractRequest):
    """
    Parses full python code and returns functions/classes without docstrings.
    """
    items = extract_functions_and_classes(req.code)
    return {"items": items}

class GenerateCommentRequest(BaseModel):
    code_snippet: str
    indentation: str
    is_inline: bool = False

class GenerateCommentResponse(BaseModel):
    docstring: str

@router.post("/generate-comment", response_model=GenerateCommentResponse)
async def api_generate_comment(req: GenerateCommentRequest):
    """
    Generates a docstring for a specific code chunk and formats it with indentation.
    """
    try:
        raw_docstring = await generate_docstring(req.code_snippet, is_inline=req.is_inline)
        
        # Format with quotes and indentation
        lines = raw_docstring.split('\n')
        indented_lines = [req.indentation + line if line.strip() else "" for line in lines]
        
        if req.is_inline:
            # Format as a single-line comment (e.g. # This is a comment)
            # Take just the first line if it somehow generated more
            comment_text = indented_lines[0].strip()
            formatted_docstring = f'{req.indentation}# {comment_text}\n'
        else:
            formatted_docstring = f'{req.indentation}"""\n' + '\n'.join(indented_lines) + f'\n{req.indentation}"""\n'
        
        # Record history for preview
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "code": (req.code_snippet[:150] + "...") if len(req.code_snippet) > 150 else req.code_snippet,
            "docstring": (formatted_docstring[:150] + "...") if len(formatted_docstring) > 150 else formatted_docstring
        })
        
        return GenerateCommentResponse(docstring=formatted_docstring)
    except Exception as e:
        return GenerateCommentResponse(docstring=f"{req.indentation}\"\"\"\n{req.indentation}Error generating docstring: {str(e)}\n{req.indentation}\"\"\"\n")

class RunRequest(BaseModel):
    code: str

class RunResponse(BaseModel):
    output: str
    error: str

@router.post("/run-code", response_model=RunResponse)
async def api_run_code(req: RunRequest):
    """
    Executes the provided python code in a temporary file and captures stdout/stderr.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(req.code)
        temp_file = f.name
        
    try:
        result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)
        return RunResponse(output=result.stdout, error=result.stderr)
    except subprocess.TimeoutExpired:
        return RunResponse(output="", error="Execution timed out (10s limit).")
    except Exception as e:
        return RunResponse(output="", error=str(e))
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
