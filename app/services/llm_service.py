import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_docstring(code_snippet: str, is_inline: bool = False) -> str:
    """
    Calls the LLM to generate a comment or docstring for the provided code.
    If is_inline is True, generates a single-line `#` comment.
    Otherwise, generates a concise PEP 257 docstring without repeating the code.
    Returns only the raw text.
    """
    if is_inline:
        prompt = f"""
        You are an expert Python developer. I will provide you with a Python snippet (usually a variable assignment or conditional block).
        Your task is to write a SINGLE, concise inline comment explaining WHY this code exists or its high-level purpose.
        
        CRITICAL: 
        1. DO NOT simply repeat what the code says. Explain its intent.
        2. Respond ONLY with the comment text itself.
        3. Keep it to one single short sentence.
        4. DO NOT wrap the response in markdown code blocks.
        5. DO NOT include the `#` character in your response, just the raw text.
        
        Here is the code:
        {code_snippet}
        """
    else:
        prompt = f"""
        You are an expert Python developer. I will provide you with a Python function or class.
        Your task is to write a concise, PEP 257 compliant docstring for it.
        
        CRITICAL: 
        1. DO NOT simply repeat the code logic line by line. Give a high-level summary of its purpose.
        2. Keep the docstring extremely concise to avoid overcrowding the file.
        3. Respond ONLY with the docstring text itself.
        4. DO NOT wrap the response in markdown code blocks (e.g., ```python).
        5. DO NOT include the \"\"\" quotes at the beginning or end of your response.
        
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
