 # backend/main.py

import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gemini_prompt_engine import generate_table_from_prompt
import fitz  # PyMuPDF

# --- Configuration ---
load_dotenv()
app = FastAPI()
API_KEY = os.getenv("GOOGLE_API_KEY")

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Pydantic Models ---
class PromptRequest(BaseModel):
    prompt: str

class Student(BaseModel):
    name: str
    usn: str

# --- API Endpoints ---

@app.post("/generate-table")
async def generate_table(req: PromptRequest):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Server is missing GOOGLE_API_KEY configuration.")
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        parsed_json = await generate_table_from_prompt(req.prompt, API_KEY)
        return parsed_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-roster")
async def upload_roster(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        students = []
        
        # --- START OF NEW FLEXIBLE LOGIC ---
        # Define the USN pattern once. Let's assume 10-12 alphanumeric characters.
        usn_pattern = r"[A-Z0-9]{10,12}"
        # Define a flexible name pattern.
        name_pattern = r"[A-Za-z\s\.]+"

        # Regex that finds either "USN Name" OR "Name USN" on a line.
        # It uses named capture groups (?P<usn>...) and (?P<name>...) to make processing easier.
        combined_pattern = re.compile(
            r"^\s*(?:"
            r"(?P<usn1>" + usn_pattern + r")\s+(?P<name1>" + name_pattern + r"?)"  # USN then Name
            r"|"
            r"(?P<name2>" + name_pattern + r")\s+(?P<usn2>" + usn_pattern + r")"   # Name then USN
            r")\s*$",
            re.MULTILINE
        )

        for match in combined_pattern.finditer(full_text):
            # The finditer method gives us a match object where we can check which named group was successful.
            if match.group("usn1"): # If the first pattern (USN then Name) matched
                usn = match.group("usn1").strip()
                name = match.group("name1").strip()
            else: # Otherwise, the second pattern (Name then USN) must have matched
                usn = match.group("usn2").strip()
                name = match.group("name2").strip()
            
            # Clean up the name by removing any trailing numbers (from marks)
            name = re.sub(r'\s*\d+$', '', name).strip()

            if name and usn and "student name" not in name.lower() and "total" not in name.lower():
                students.append(Student(name=name, usn=usn))
        # --- END OF NEW FLEXIBLE LOGIC ---

        if not students:
            raise HTTPException(status_code=400, detail="Could not find any student names and USNs in the PDF. Please check the PDF format. The pattern might need adjustment.")

        return students

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF file: {e}")

@app.get("/")
def read_root():
    return {"message": "Acharya Connect Marks Table Generator API is running."}