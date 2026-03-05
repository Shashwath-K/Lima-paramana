from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.llm_service import generate_docstring, explain_code
from app.services.rpa_service import type_docstring
from app.services.parser_service import extract_functions_and_classes
from app.services.sidebar_service import extract_concepts, analyze_similarity
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
    language: str = "python"
    doc_level: str = "maximum"

@router.post("/extract-symbols")
async def api_extract_symbols(req: ExtractRequest):
    """
    Parses code and returns items needing documentation.
    For Python, uses AST to find specific functions/classes.
    For other languages (C++, JS, IPYNB), treating the entire block as one item
    to let the LLM handle the commenting directly.
    """
    if req.language.lower() == "python":
        items = extract_functions_and_classes(req.code, req.doc_level)
    else:
        # For non-python, we pass the entire code block to the LLM
        # rather than writing a heavy parser for every language
        items = [{
            "name": f"{req.language.upper()} File",
            "type": "RawBlock",
            "start_line": 1,
            "insert_line": 1,
            "indentation": "",
            "snippet": req.code,
            "is_inline": False,
            "full_replace": True # flag to tell frontend to replace everything
        }]
    return {"items": items}

class GenerateCommentRequest(BaseModel):
    code_snippet: str
    indentation: str
    is_inline: bool = False
    language: str = "python"
    doc_level: str = "maximum"
    full_replace: bool = False

class GenerateCommentResponse(BaseModel):
    docstring: str

@router.post("/generate-comment", response_model=GenerateCommentResponse)
async def api_generate_comment(req: GenerateCommentRequest):
    """
    Generates a docstring for a specific code chunk and formats it with indentation.
    If full_replace is True, returns the generated commented code in its entirety.
    """
    try:
        raw_docstring = await generate_docstring(
            req.code_snippet, 
            is_inline=req.is_inline, 
            language=req.language.lower(), 
            doc_level=req.doc_level
        )
        
        # If the LLM returned the fully commented code block (for non-Python)
        if hasattr(req, 'full_replace') and getattr(req, 'full_replace', False):
            # For this scenario, raw_docstring IS the new code block
            formatted_docstring = raw_docstring
            
        else:
            # Python AST snippet logic
            lines = raw_docstring.split('\n')
            indented_lines = [req.indentation + line if line.strip() else "" for line in lines]
            
            if req.is_inline:
                # Format as a single-line python comment
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

class ExplainRequest(BaseModel):
    code: str
    user_input: Optional[str] = None

class ExplainResponse(BaseModel):
    explanation: str

@router.post("/explain-code", response_model=ExplainResponse)
async def api_explain_code(req: ExplainRequest):
    """
    Explains a chunk of code via the LLM context menu feature.
    """
    try:
        explanation = await explain_code(req.code, req.user_input)
        return ExplainResponse(explanation=explanation)
    except Exception as e:
        return ExplainResponse(explanation=f"Error generating explanation: {str(e)}")

class AnalysisRequest(BaseModel):
    code: str

@router.post("/analyze-concepts", response_model=Dict[str, Any])
async def api_analyze_concepts(req: AnalysisRequest):
    """
    Extracts high-level programming concepts from the code snippet using the LLM heuristic engine.
    """
    if not req.code.strip():
        return {"concepts": []}
    
    concepts = await extract_concepts(req.code)
    return {"concepts": concepts}

@router.post("/analyze-similarity", response_model=Dict[str, Any])
async def api_analyze_similarity(req: AnalysisRequest):
    """
    Determines open-source heuristic similarity using the LLM heuristic engine.
    """
    if not req.code.strip():
        return {"score": 0, "source": "Unknown"}
    
    result = await analyze_similarity(req.code)
    return result
