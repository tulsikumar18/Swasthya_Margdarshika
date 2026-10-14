from typing import List
from pydantic import BaseModel, Field

class SymptomItem(BaseModel):
    key: str = Field(..., description="Internal normalized symptom key matching the model vocabulary")
    label: str = Field(..., description="Human readable display label for the symptom")
    index: int = Field(..., description="Feature index in the 132-dimension vector")

class SymptomListResponse(BaseModel):
    total: int = Field(..., description="Total number of supported symptoms")
    symptoms: List[SymptomItem] = Field(..., description="Alphabetically sorted list of supported symptoms")
