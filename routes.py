import os, re
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

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
    final_date = req.effective_date or req.dates or "27-09-2026"

    terms_list = [x.strip() for x in req.terms.split(";") if x.strip()]
    terms_formatted = "\n".join([f" {i+1}. {t};" for i,t in enumerate(terms_list)])

    document = f"""
EMPLOYMENT AGREEMENT

This Employment Agreement is made and entered into on this {final_date}, by and between:

{req.parties}

1. PREAMBLE
This Agreement sets forth the terms and conditions under which the Employee shall be employed by the Employer.

2. DEFINITIONS
   a) "Company" means {req.parties.split('and')[-1] if 'and' in req.parties else 'XYZ Company'}.
   b) "Employee" means {req.parties.split('and')[0] if 'and' in req.parties else 'Amit Sharma'}.
   c) "Effective Date" means {final_date}.

3. APPOINTMENT AND DUTIES
The Employer hereby appoints the Employee and the Employee agrees to serve the Company diligently and faithfully.

4. TERMS AND CONDITIONS
{terms_formatted}

5. CONFIDENTIALITY
The Employee agrees to keep all confidential information of the Company secret during and after employment.

6. COMPENSATION
As mentioned in Terms, salary shall be payable monthly by bank transfer.

7. TERMINATION
Either party may terminate this agreement with 30 days written notice, or as per terms mentioned.

8. GOVERNING LAW
This Agreement shall be governed by the laws of India.

9. ENTIRE AGREEMENT
This document constitutes the entire agreement between parties.

IN WITNESS WHEREOF, the parties have executed this Agreement on {final_date}.

For Employer: _________________________ For Employee: _________________________
Name: Name: {req.parties.split('(')[0]}

"""

    return {"document": sanitize(document), "status": "success"}