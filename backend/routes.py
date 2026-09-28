import os, re
from fastapi import APIRouter
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# FIXED LINE 9 - use new model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class DocumentRequest(BaseModel):
    document_type: str
    parties: str
    terms: str
    dates: str = Field(default="", alias="effective_date")
    effective_date: str = ""

    class Config:
        populate_by_name = True

def sanitize(t): 
    return re.sub(r'[^\x00-\x7F]+',' ',t).strip()

@router.post("/generate")
async def generate(req: DocumentRequest):
    try:
        final_date = req.effective_date or req.dates or "Today"
        print(f"Request: {req.document_type} | Date: {final_date}")
        
        if not GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY missing in .env file")

        terms_list = [x.strip() for x in req.terms.split(";") if x.strip()]
        terms_fmt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(terms_list)])
        
        prompt = f"You are expert legal drafter. Draft formal {req.document_type}. Parties: {req.parties}. Date: {final_date}. Terms: {terms_fmt}. Include Preamble, Definitions, Terms, Confidentiality, Termination, Governing Law, Signatures. Use professional legal language."
        
        # FIXED - Try 3 new models
        text = None
        for model_name in [GEMINI_MODEL, "gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt)
                text = res.text
                break
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                continue
        
        if not text:
            raise Exception("All Gemini models failed - check API key")
            
        return {"document": sanitize(text), "status": "success"}
        
    except Exception as e:
        print(f"ERROR: {e}")
        fallback = f"""
{req.document_type.upper()} - DRAFT (AI Error: {str(e)})

Effective Date: {final_date if 'final_date' in locals() else 'N/A'}
Parties: {req.parties}

TERMS:
{req.terms}

This is a fallback document because Gemini API failed.
Check your .env file.

1. Confidentiality clause
2. Payment: 30 days
3. Termination: 15 days notice
"""
        return {"document": fallback, "status": "fallback", "error": str(e)}