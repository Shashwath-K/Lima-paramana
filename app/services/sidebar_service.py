import httpx
import json
import ast

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b" # Adjust based on environment

async def extract_concepts(code: str) -> list[str]:
    """
    Analyzes code to extract 3-5 core programming concepts.
    Returns a list of strings natively (e.g. ['File I/O', 'Async/Await']).
    """
    if not code or not code.strip():
        return ["No Code Provided"]

    prompt = f"""
    You are an expert programming analyzer. Look at the following code snippet and identify 3 to 5 core high-level programming concepts used (e.g., Recursion, Async/Await, File I/O, REST APIs, Object-Oriented, etc.). 
    
    CRITICAL INSTRUCTION: Your output MUST be ONLY a raw JSON array of strings. Do not include markdown formatting, backticks, conversational text, or anything else. Just the JSON array. Example: ["File I/O", "Async/Await", "Event Loop"]

    Code:
    {code}
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "system": "You are a specialized code analysis API. You only output valid JSON arrays. You never output conversational text."
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_API_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            
            result_text = response.json().get("response", "").strip()
            
            # Clean up the response in case the LLM returned markdown blocks anyway
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Attempt parsing
            concepts = json.loads(result_text)
            
            if isinstance(concepts, list) and all(isinstance(c, str) for c in concepts):
                return concepts[:5] # Max 5
            return ["Parsing Error"]

    except Exception as e:
        print(f"Error extracting concepts: {e}")
        return ["Analysis Failed"]


async def analyze_similarity(code: str) -> dict:
    """
    Predicts if the code matches known open source patterns.
    Returns a dict with 'score' (0-100 int) and 'source' (string URL/name).
    """
    if not code or len(code.strip()) < 15:
        return {"score": 0, "source": "Not Enough Context"}

    prompt = f"""
    You are an expert software archivist. Analyze the following code snippet and determine if it closely resembles a known open-source library, a famous boilerplate template, a standard architectural pattern, or a well-known algorithm.
    
    If it is highly custom logic that doesn't strongly resemble a specific source, give it a low score and say "Custom Implementation".
    If it is standard boilerplate for a popular framework (like Express, FastAPI, React), give it a high score and list the framework/library.

    CRITICAL INSTRUCTION: Your output MUST be ONLY a raw JSON object with exactly two keys: "score" (an integer from 0 to 100) and "source" (a short string identifying the likely inspiration or 'Custom Implementation'). Do not include markdown formatting, backticks, or conversational text.

    Example: {{"score": 92, "source": "github.com/pallets/flask patterns"}}
    Example: {{"score": 15, "source": "Custom Implementation"}}

    Code:
    {code}
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "system": "You are a specialized code heuristic API. You only output valid strictly formatted JSON objects. You never output conversational text."
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_API_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            
            result_text = response.json().get("response", "").strip()
            
            # Clean up the response in case the LLM returned markdown blocks anyway
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            result_text = result_text.strip()
            
            # Attempt parsing
            data = json.loads(result_text)
            
            if "score" in data and "source" in data:
                # Ensure types are correct
                score = min(max(int(data["score"]), 0), 100)
                return {"score": score, "source": str(data["source"])}
                
            return {"score": 0, "source": "Parse Error"}

    except Exception as e:
        print(f"Error determining similarity: {e}")
        return {"score": 0, "source": "Analysis Failed"}
