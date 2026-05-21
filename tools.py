import os
import ast
import asyncio
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the DuckDuckGo search tool
search = DuckDuckGoSearchRun()

def analyze_code_safety(code: str) -> dict:
    """
    Statically analyzes python code using AST to identify security risks.
    NOTE: Statically auditing code acts as a low-cost, fast static gate.
    In an enterprise production deployment, this static analysis is backed by running the script
    inside isolated, ephemeral Docker container sandboxes with read-only root filesystems
    and zero outbound network access to guarantee absolute host security.
    """
    try:
        tree = ast.parse(code)
    except Exception as e:
        return {
            "status": "unsafe",
            "risk_score": 100,
            "risk_level": "CRITICAL",
            "findings": [f"Syntax Error: {e}"]
        }
        
    findings = []
    risk_score = 0
    
    # Dangerous modules list
    suspect_imports = {
        "os": "High risk of environment/system command injection",
        "subprocess": "High risk of spawning untrusted processes",
        "sys": "Medium risk of environment manipulation",
        "shutil": "High risk of file system deletions",
        "requests": "Medium risk of unauthorized outbound network requests",
        "urllib": "Medium risk of unauthorized outbound network requests",
        "socket": "High risk of raw network access/port scanning",
        "builtins": "Potential dangerous built-in manipulation"
    }
    
    for node in ast.walk(tree):
        # Check Import nodes
        if isinstance(node, ast.Import):
            for name in node.names:
                base = name.name.split('.')[0]
                if base in suspect_imports:
                    findings.append(f"Imported suspect module `{base}`: {suspect_imports[base]}")
                    risk_score += 35
        # Check ImportFrom nodes
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split('.')[0]
                if base in suspect_imports:
                    findings.append(f"Imported from suspect module `{base}`: {suspect_imports[base]}")
                    risk_score += 35
                    
        # Check dangerous functions (including dynamic evaluations that bypass standard imports)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
                if func_name in ["system", "popen", "spawn", "rmtree", "remove", "unlink", "rmdir"]:
                    findings.append(f"Called high-risk filesystem/OS function `{func_name}`")
                    risk_score += 45
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Target common LLM security bypass functions (eval, exec, __import__, getattr)
                if func_name in ["eval", "exec", "open", "getattr", "setattr", "compile", "__import__"]:
                    findings.append(f"Called unsafe dynamic inspection/execution function `{func_name}`")
                    risk_score += 40
                    
    risk_level = "LOW"
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
        
    return {
        "status": "safe" if risk_score < 70 else "review_required",
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "findings": findings if findings else ["No major security vulnerabilities detected statically."]
    }

@tool
def web_search(query: str) -> str:
    """
    Search the internet for real-time information.
    Use this when you need up-to-date facts, news, or to answer questions about the current world.
    """
    try:
        return search.run(query)
    except Exception as e:
        return f"Search failed: {e}"

@tool
def read_file(filepath: str) -> str:
    """
    Reads the content of a local file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def write_file(filepath: str, content: str) -> str:
    """
    Writes content to a local file. This is an advanced capability.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {e}"

@tool
async def execute_python_code(code: str) -> str:
    """
    SENSITIVE TOOL: Executes Python code in an asynchronous subprocess and returns the output.
    Uses asyncio.create_subprocess_exec to ensure standard Streamlit UI event loops remain unblocked.
    This requires Human-In-The-Loop approval before running because it has access to the user's computer.
    """
    try:
        # Run python in an asynchronous non-blocking subprocess
        proc = await asyncio.create_subprocess_exec(
            "python", "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Wait for execution with a strict 15.0 second timeout limit
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except:
                pass
            return "Execution failed: Code execution timed out after 15 seconds."
            
        stdout_str = stdout.decode("utf-8", errors="ignore")
        stderr_str = stderr.decode("utf-8", errors="ignore")
        
        if proc.returncode == 0:
            return f"Execution successful. Output:\n{stdout_str}"
        else:
            return f"Execution failed. Error:\n{stderr_str}"
    except Exception as e:
        return f"Error executing code: {e}"

@tool
def workspace_semantic_search(query: str) -> str:
    """
    Perform a local semantic search over all textual files in the workspace directory.
    Returns matched snippets from files (code, docs, etc.) related to the query.
    Use this to find relevant code, scripts, or workspace context quickly.
    """
    try:
        import math
        from collections import Counter
        
        # 1. Scan files
        exclude_dirs = {".venv", "__pycache__", ".git", ".gemini", "node_modules"}
        exclude_exts = {".png", ".jpg", ".jpeg", ".ico", ".pyc", ".db", ".lock"}
        
        documents = []
        filenames = []
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in exclude_exts:
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        if len(text.strip()) > 0:
                            documents.append(text)
                            filenames.append(filepath)
                except:
                    pass
                    
        if not documents:
            return "No text documents found in workspace to search."
            
        # Helper for word similarity
        def tfidf_similarity(query_str, docs, names):
            def tokenize(text):
                return [w.lower() for w in text.split() if w.isalnum() and len(w) > 2]
                
            q_tokens = tokenize(query_str)
            if not q_tokens:
                return []
                
            doc_tokens = [tokenize(d) for d in docs]
            all_vocab = set(q_tokens)
            
            # DF
            df = {}
            for t in all_vocab:
                df[t] = sum(1 for tokens in doc_tokens if t in tokens)
                
            results = []
            for i, tokens in enumerate(doc_tokens):
                tf = Counter(tokens)
                doc_len = len(tokens)
                if doc_len == 0:
                    continue
                    
                score = 0.0
                for t in q_tokens:
                    if t in tf:
                        # TF-IDF calculation
                        idf = math.log((1 + len(docs)) / (1 + df[t])) + 1
                        score += (tf[t] / doc_len) * idf
                if score > 0:
                    results.append((names[i], score, docs[i][:500]))
                    
            return sorted(results, key=lambda x: x[1], reverse=True)[:3]
            
        matches = tfidf_similarity(query, documents, filenames)
        if not matches:
            return f"No relevant content found in workspace matching: '{query}'"
            
        output = []
        for file, score, snippet in matches:
            output.append(f"### File: {file} (Match Score: {score:.3f})\n```\n{snippet.strip()}\n...\n```")
        return "\n\n".join(output)
    except Exception as e:
        return f"Error during workspace search: {e}"

# Group the tools for routing
safe_tools = [web_search, read_file, write_file, workspace_semantic_search]
sensitive_tools = [execute_python_code]
