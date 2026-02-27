from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys
from io import StringIO
import traceback
import os
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

def execute_python_code(code: str):
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code)
        output = sys.stdout.getvalue()
        return True, output
    except Exception:
        output = traceback.format_exc()
        return False, output
    finally:
        sys.stdout = old_stdout

def analyze_error_with_ai(code, traceback_text):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Find the exact line number where the Python error occurred.

CODE:
{code}

TRACEBACK:
{traceback_text}

Return only a Python list of integers.
Example: [3]
"""

    response = model.generate_content(prompt)

    try:
        lines = eval(response.text.strip())
        return lines
    except:
        return []

@app.post("/code-interpreter")
def code_interpreter(request: CodeRequest):

    success, output = execute_python_code(request.code)

    if success:
        return {"error": [], "result": output}

    error_lines = analyze_error_with_ai(request.code, output)

    return {"error": error_lines, "result": output}