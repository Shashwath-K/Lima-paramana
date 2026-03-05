import ast
from typing import List, Dict, Any

def extract_functions_and_classes(code: str) -> List[Dict[str, Any]]:
    """
    Parses Python code and extracts functions and classes, 
    returning their structure for docstring generation.
    If no functions or classes are found, returns a module-level item to document the whole script.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    lines = code.split('\n')
    items = []

    # First check if the module itself already has a docstring at the very top
    module_has_docstring = ast.get_docstring(tree) is not None

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if it already has a docstring
            has_docstring = ast.get_docstring(node) is not None
            
            if has_docstring:
                continue # Skip items that already have docstrings
            
            # Start and end lines of the node
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            
            # Extract the actual code snippet for context for the LLM
            snippet = '\n'.join(lines[start_line-1:end_line])
            
            # Find insertion point and indentation base
            if node.body:
                insert_line = node.body[0].lineno
                # Get the indentation string from the first line of the body
                body_line = lines[insert_line-1]
                indentation = body_line[:len(body_line) - len(body_line.lstrip())]
                # If first line of body is empty or malformed, fallback to 4 spaces more than def
                if not indentation:
                    def_line = lines[start_line-1]
                    def_indent = def_line[:len(def_line) - len(def_line.lstrip())]
                    indentation = def_indent + "    "
            else:
                insert_line = start_line + 1
                def_line = lines[start_line-1]
                def_indent = def_line[:len(def_line) - len(def_line.lstrip())]
                indentation = def_indent + "    " # Default 4 spaces
                
            items.append({
                "name": node.name,
                "type": type(node).__name__,
                "start_line": start_line,
                "insert_line": insert_line,
                "indentation": indentation,
                "snippet": snippet,
                "is_inline": False
            })
            
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.If, ast.For, ast.While, ast.With, ast.AsyncFor, ast.AsyncWith)):
            # Only consider top-level nodes or significant nested blocks to avoid massive spam
            # We determine depth based on indentation
            start_line = node.lineno
            def_line = lines[start_line-1]
            indentation = def_line[:len(def_line) - len(def_line.lstrip())]
            
            # Skip if it already has a comment right above it
            if start_line > 1:
                line_above = lines[start_line-2].strip()
                if line_above.startswith('#'):
                    continue
            
            end_line = getattr(node, 'end_lineno', start_line)
            # Bound the snippet to max 10 lines to prevent overwhelming the LLM with massive nested blocks
            max_end_line = min(end_line, start_line + 10)
            snippet = '\n'.join(lines[start_line-1:max_end_line])
            
            name = type(node).__name__
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = getattr(node, 'targets', [getattr(node, 'target', None)])
                var_names = []
                for t in targets:
                    if isinstance(t, ast.Name):
                        var_names.append(t.id)
                if var_names:
                    name = f"Variable '{', '.join(var_names)}'"
                else:
                    name = "Assignment"
            
            items.append({
                "name": name,
                "type": type(node).__name__,
                "start_line": start_line,
                "insert_line": start_line, # Insert ABOVE the statement
                "indentation": indentation,
                "snippet": snippet,
                "is_inline": True
            })
            
    # Fallback for plain scripts (like test_ollama.py or sample.py) that have no functions/classes
    if len(items) == 0 and not module_has_docstring and code.strip() != "":
        # We find the first line that is not an import or a comment to insert before
        insert_line = 1
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('import') and not line.strip().startswith('from'):
                insert_line = i + 1
                break
                
        items.append({
            "name": "Module Script",
            "type": "ModuleContent",
            "start_line": 1,
            "insert_line": 1, # Always insert at the very top of the script
            "indentation": "",
            "snippet": code # Send the entire code snippet for context
        })
            
    # Sort backwards by start_line so that inserting text doesn't mess up subsequent insertion line numbers!
    items.sort(key=lambda x: x['start_line'], reverse=True)
    return items
