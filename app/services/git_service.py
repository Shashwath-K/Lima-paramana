import os
import shutil
import subprocess
import uuid
import datetime
import asyncio
from typing import Dict, Any

# In-memory store for tracking repository processing jobs.
# Format: { "session_id": { "status": "processing|completed|failed", "total_files": 10, "files_done": 2, "current_file": "main.py", "error": "", "repo_path": "/path..." } }
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}

def init_job() -> str:
    """Creates a new job session and returns the session_id."""
    session_id = str(uuid.uuid4())
    ACTIVE_JOBS[session_id] = {
        "status": "extracting",
        "total_files": 0,
        "files_done": 0,
        "current_file": "",
        "error": "",
        "repo_path": ""
    }
    return session_id

def get_job_status(session_id: str) -> Dict[str, Any]:
    """Returns the current status of a job."""
    return ACTIVE_JOBS.get(session_id, {"status": "not_found"})

async def process_repo_background(session_id: str, zip_path: str, extract_path: str, doc_level: str):
    """
    Background task that:
    1. Unzips the repository.
    2. Initializes git if needed.
    3. Finds valid files.
    4. Runs LLM extraction & generation on them.
    5. Marks job as completed.
    """
    job = ACTIVE_JOBS[session_id]
    job["repo_path"] = extract_path
    
    try:
        # 1. Unzip the repository
        job["status"] = "extracting"
        job["current_file"] = "Extracting ZIP archive..."
        shutil.unpack_archive(zip_path, extract_path)
        
        # 2. Initialize Git if not present
        job["status"] = "initializing_git"
        job["current_file"] = "Setting up Git repository..."
        
        git_dir = os.path.join(extract_path, ".git")
        if not os.path.exists(git_dir):
            subprocess.run(["git", "init"], cwd=extract_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=extract_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit before AI generated docs"], cwd=extract_path, capture_output=True)
        else:
            # If it is a git repo, ensure we have a clean working tree or commit unstaged changes
            subprocess.run(["git", "add", "."], cwd=extract_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Commit existing changes before AI docs"], cwd=extract_path, capture_output=True)

        # 3. Find valid files
        job["status"] = "scanning"
        job["current_file"] = "Scanning for code files..."
        
        valid_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".cpp", ".c", ".java"}
        blacklist_dirs = {"node_modules", "venv", ".git", "dist", "build", "__pycache__", ".next"}
        
        target_files = []
        for root, dirs, files in os.walk(extract_path):
            # Remove blacklisted dirs so os.walk doesn't traverse them
            dirs[:] = [d for d in dirs if d not in blacklist_dirs]
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_extensions:
                    target_files.append(os.path.join(root, f))
                    
        job["total_files"] = len(target_files)
        job["status"] = "processing"
        
        if len(target_files) == 0:
            job["status"] = "completed"
            job["current_file"] = "No valid code files found."
            return

        # 4. Import LLM services locally to avoid circular imports if endpoints import this
        from app.api.endpoints import process_generation_queue
        from app.services.parser_service import extract_symbols_from_code
        from app.services.llm_service import generate_docstring
        import sys
        
        for file_path in target_files:
            rel_path = os.path.relpath(file_path, extract_path)
            job["current_file"] = rel_path
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                    
                ext = os.path.splitext(file_path)[1].lower()
                lang = "python"
                if ext in {".js", ".jsx"}: lang = "javascript"
                elif ext in {".ts", ".tsx"}: lang = "typescript"
                elif ext == ".html": lang = "html"
                elif ext == ".css": lang = "css"
                elif ext in {".cpp", ".c"}: lang = "cpp"
                elif ext == ".java": lang = "java"
                
                # Extract symbols
                symbols = extract_symbols_from_code(code, lang, doc_level)
                
                if symbols:
                    # Modify code bottom-up
                    modified_code = code
                    symbols = sorted(symbols, key=lambda x: x["insert_line"], reverse=True)
                    
                    code_lines = modified_code.split("\n")
                    
                    for sym in symbols:
                        raw_docstring = await generate_docstring(
                            sym["snippet"],
                            is_inline=sym.get("is_inline", False),
                            language=lang,
                            doc_level=doc_level,
                            is_markdown_cell=sym.get("is_markdown_cell", False)
                        )
                        
                        if sym.get("full_replace", False):
                            # Replace the entire file contents
                            code_lines = raw_docstring.split("\n")
                            # If it's full replace, we can just jump out since it handles the whole file
                            break
                        else:
                            indent = sym.get("indentation", "")
                            # Python AST snippet logic
                            lines = raw_docstring.split('\n')
                            formatted_docstring = '\n'.join([f"{indent}{line}" if line.strip() else "" for line in lines])

                            insert_idx = sym["insert_line"] - 1 # 0-indexed
                            # Ensure we don't insert out of bounds
                            if 0 <= insert_idx <= len(code_lines):
                                code_lines.insert(insert_idx, formatted_docstring)
                                
                    modified_code = "\n".join(code_lines)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(modified_code)
                        
            except Exception as e:
                print(f"Error processing {rel_path}: {e}")
                
            job["files_done"] += 1
            await asyncio.sleep(0.1) # Yield to event loop
            
        # 5. Mark as completed
        job["status"] = "completed"
        job["current_file"] = "All files processed."

    except Exception as e:
        import traceback
        traceback.print_exc()
        job["status"] = "failed"
        job["error"] = str(e)

def get_repo_diff(session_id: str) -> str:
    """Gets the git diff for the repository."""
    job = ACTIVE_JOBS.get(session_id)
    if not job or job["status"] not in ["completed", "failed"]:
        return "Repository not ready or not found."
        
    repo_path = job["repo_path"]
    try:
        # Get diff of unstaged and staged changes
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        res = subprocess.run(["git", "diff", "--staged"], cwd=repo_path, capture_output=True, text=True)
        # Unstage so user can commit normally later or so we have a clean state if they abort
        subprocess.run(["git", "restore", "--staged", "."], cwd=repo_path, capture_output=True)
        return res.stdout
    except subprocess.CalledProcessError as e:
        return f"Error gathering diff: {e.stderr}"

def commit_and_zip_repo(session_id: str, commit_message: str, output_zip_path: str):
    """Commits changes and zips the repository for download."""
    job = ACTIVE_JOBS.get(session_id)
    if not job or job["status"] not in ["completed", "failed"]:
        raise ValueError("Repository not ready or not found.")
        
    repo_path = job["repo_path"]
    try:
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, capture_output=True)
        
        # Create zip archive of the directory
        # shutil.make_archive adds the .zip extension automatically if format is zip
        base_name = os.path.splitext(output_zip_path)[0]
        shutil.make_archive(base_name, 'zip', repo_path)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git commit failed: {e.stderr}")
