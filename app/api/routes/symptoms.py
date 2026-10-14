from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.ml.preprocessing import get_all_supported_symptoms, SYMPTOMS_DICT, extract_symptoms_from_natural_text
from app.schemas.symptom import SymptomListResponse, SymptomItem

router = APIRouter(prefix="/api/symptoms", tags=["Symptoms"])

class ExtractSymptomsRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Conversational sentence or speech text describing symptoms")

class ExtractSymptomsResponse(BaseModel):
    extracted_symptoms: List[SymptomItem]
    extracted_keys: List[str]
    raw_text: str
    confirmation_message: str

@router.get("", response_model=SymptomListResponse, summary="List all supported symptoms")
async def list_symptoms():
    """Returns the complete list of 132 symptoms recognized by the trained machine learning model."""
    all_symptoms = get_all_supported_symptoms()
    return SymptomListResponse(
        total=len(all_symptoms),
        symptoms=[SymptomItem(**s) for s in all_symptoms]
    )

@router.get("/search", response_model=List[SymptomItem], summary="Search supported symptoms")
async def search_symptoms(q: Optional[str] = Query(default="", min_length=1, max_length=50)):
    """Search for symptoms by keyword for dynamic client-side autocomplete."""
    if not q or not q.strip():
        return []

    query = q.strip().lower()
    matched = []
    for item in get_all_supported_symptoms():
        if query in item["key"] or query in item["label"].lower():
            matched.append(SymptomItem(**item))

    return matched

@router.post("/extract", response_model=ExtractSymptomsResponse, summary="Extract symptoms from natural language text")
async def extract_symptoms(request: ExtractSymptomsRequest):
    """
    Parses conversational sentences or speech transcripts like:
    'i am feeling like stomach ache, then headache, then vomiting'
    and extracts matching clinical symptoms for user confirmation.
    """
    result = extract_symptoms_from_natural_text(request.text)
    items = []
    for s in result["extracted_symptoms"]:
        idx = SYMPTOMS_DICT.get(s["key"], -1)
        items.append(SymptomItem(key=s["key"], label=s["label"], index=idx))

    return ExtractSymptomsResponse(
        extracted_symptoms=items,
        extracted_keys=result["extracted_keys"],
        raw_text=result["raw_text"],
        confirmation_message=result["confirmation_message"]
    )
