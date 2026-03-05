import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_docstring(code_snippet: str) -> str:
    """
    Calls the LLM to generate a PEP 257 docstring for the provided code.
    Returns only the docstring content without any extra formatting.
    """
    prompt = f"""
    You are an expert Python developer. I will provide you with a Python function or class.
    Your task is to write a comprehensive, PEP 257 compliant docstring for it.
    
    CRITICAL: 
    1. Respond ONLY with the docstring text itself.
    2. DO NOT wrap the response in markdown code blocks (e.g., ```python).
    3. DO NOT include the \"\"\" quotes at the beginning or end of your response.
    4. Provide just the raw text that should go inside the quotes.
    
    Here is the code:
    {code_snippet}
    """
    
    if settings.LLM_PROVIDER == "ollama":
        try:
            import ollama
            response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
                {'role': 'user', 'content': prompt}
            ])
            docstring = response['message']['content'].strip()
            
            # Clean up potential markdown formatting
            if docstring.startswith("```"):
                lines = docstring.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                docstring = '\n'.join(lines).strip()
            
            # Clean up quotes if the model disobeys
            if docstring.startswith('"""') and docstring.endswith('"""'):
                docstring = docstring[3:-3].strip()
            
            return docstring
            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"Error generating docstring: {e}"
    else:
        # Dummy implementation if not using local ollama
        return "This is a dummy PEP 257 compliant docstring generated because Ollama is not available or configured."
