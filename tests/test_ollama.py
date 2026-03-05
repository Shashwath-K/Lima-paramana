import os
import sys
import asyncio

# Add the project root to the sys.path so we can import 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.services.llm_service import generate_docstring
from app.core.config import settings

async def main():
    print(f"Testing Ollama Connection using model: {settings.OLLAMA_MODEL}")
    print(f"LLM Provider set in config: {settings.LLM_PROVIDER}")
    
    sample_path = os.path.join(project_root, 'sample.py')
    try:
        with open(sample_path, 'r') as f:
            code_snippet = f.read()
    except FileNotFoundError:
        print(f"Error: {sample_path} not found.")
        return

    print("--- Code Snippet to Analyze ---")
    print(code_snippet)
    print("-------------------------------")
    print("Sending request to LLM (this may take a moment)...")

    try:
        docstring = await generate_docstring(code_snippet)
        print("\n--- Generated Docstring ---")
        print(docstring)
        print("---------------------------")
        print("\nConnection and inference successful!")
    except Exception as e:
        print(f"\nFailed to generate docstring: {e}")

if __name__ == "__main__":
    asyncio.run(main())
