import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_docstring(code_snippet: str, is_inline: bool = False, language: str = "python", doc_level: str = "maximum", is_markdown_cell: bool = False) -> str:
    """
    Calls the LLM to generate a comment or docstring for the provided code.
    Adjusts behavior based on the target programming language and doc_level (min/med/max).
    """
    
    # Configure Doc Level Instructions for Docstrings
    if doc_level == "minimum":
        level_instruction = "Focus on a high-level summary of the class or function."
    elif doc_level == "medium":
        level_instruction = "Provide a slightly more detailed explanation of the logic."
    else: # maximum
        level_instruction = "Provide a highly detailed step-by-step explanation of the internal logic."

    # Language Specific Overrides
    if language != "python":
        if is_markdown_cell or language == "md":
            prompt = f"""
            You are an expert technical writer. I will provide you with a raw snippet of Markdown text.
            Your task is to review the text and return it EXACTLY in the following custom format:
            
            [Preview]
            (Write a very brief 1-2 sentence summary of what this markdown text is about to give the user a preview)
            
            [Code (Raw)]
            (Return the EXACT original markdown text here, completely unmodified)
            
            CRITICAL:
            1. DO NOT wrap the response in markdown blocks like ```md.
            2. ONLY return the two sections exactly as described above.
            
            Text to review:
            {code_snippet}
            """
        else:
            if doc_level == "minimum":
                density = "Add a high-level block comment at the top, and ONLY comment class/function definitions."
            elif doc_level == "medium":
                density = "Add comments for functions, classes, and complex logic blocks or variable assignments."
            else:
                density = "Add short comments to almost every significant line to explain what it does step-by-step."
                
            # For non-python, we send the FULL block and expect the FULL block back properly commented
            prompt = f"""
        You are an expert developer. I will provide you with a raw snippet of {language.upper()} code.
        Your task is to return the exact same code, but with comments added according to the requested density.
        
        Density Requested: {density}
        
        CRITICAL:
        1. Use the correct comment syntax for {language.upper()} (e.g. `//` or `/*` for JS/C++, `#` for Bash/R, etc).
        2. Respond ONLY with the newly commented code. Do not wrap it in markdown blockticks like ```js.
        3. Do not change the original code logic, ONLY add comments.
        4. IF A LINE OR SNIPPET ALREADY HAS A COMMENT, DO NOT MODIFY IT OR ADD AN ADDITIONAL COMMENT. KEEP PRE-EXISTING COMMENTS EXACTLY AS THEY ARE.
        
        Code to comment:
        {code_snippet}
        """
    else:
        # Standard Python injection logic (snippet-based via AST)
        if is_inline:
            prompt = f"""
            You are an expert Python developer. I will provide you with a Python snippet (usually a variable assignment or conditional block).
            Your task is to write a SINGLE, concise inline comment explaining WHY this code exists or its high-level purpose.
            
            CRITICAL: 
            1. DO NOT simply repeat what the code says. Explain its intent.
            2. Respond ONLY with the comment text itself.
            3. Keep it short.
            4. DO NOT wrap the response in markdown code blocks.
            5. DO NOT include the `#` character in your response, just the raw text.
            6. IF THIS SNIPPET ALREADY CONTAINS A COMMENT, DO NOT MODIFY IT OR RETURN A NEW ONE. JUST RETURN THE EXISTING TEXT OR AN EMPTY STRING.
            
            Here is the code:
            {code_snippet}
            """
        else:
            prompt = f"""
            You are an expert Python developer. I will provide you with a Python function, class, or script.
            Your task is to write a PEP 257 compliant docstring for it.
            
            Context Level: {level_instruction}
            
            CRITICAL: 
            1. DO NOT regurgitate the code. Evaluate its intent based on the Context Level.
            2. Respond ONLY with the docstring text itself.
            3. DO NOT wrap the response in markdown code blocks (e.g., ```python).
            4. DO NOT include the \"\"\" quotes at the beginning or end of your response, just the inner text.
            5. IF THIS CLASS/FUNCTION ALREADY HAS A DOCSTRING, DO NOT MODIFY IT. RETURN IT EXACTLY AS IS.
            
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

async def explain_code(code_snippet: str, user_query: str = None) -> str:
    """
    Calls the LLM to explain the provided code snippet.
    Optionally incorporates a user_query to focus the explanation.
    """
    if user_query:
        prompt = f"""
        You are an expert Python developer and teacher.
        Explain the following code snippet. The user specifically asked: "{user_query}"
        
        Keep your explanation clear, concise, and formatted in markdown.
        Do not write overly long essays.
        
        Code:
        ```python
        {code_snippet}
        ```
        """
    else:
        prompt = f"""
        You are an expert Python developer and teacher.
        Explain the purpose and functionality of the following code snippet concisely.
        
        Keep your explanation clear, concise, and formatted in markdown.
        Do not write overly long essays.
        
        Code:
        ```python
        {code_snippet}
        ```
        """
        
    if settings.LLM_PROVIDER == "ollama":
        try:
            import ollama
            response = ollama.chat(model=settings.OLLAMA_MODEL, messages=[
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"Error calling Ollama for explanation: {e}")
            return f"Error generating explanation: {e}"
    else:
        return "This is a dummy explanation generated because Ollama is not available."
