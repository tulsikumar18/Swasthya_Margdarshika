from typing import List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class PredictionMode(str, Enum):
    ML_PREDICTION = "ml_prediction"
    AI_ASSISTED = "ai_assisted"
    CLARIFICATION_REQUIRED = "clarification_required"
    FALLBACK = "fallback"

DEFAULT_DISCLAIMER = (
    "Disclaimer: This application provides informational assistance using machine learning and AI. "
    "It is NOT a substitute for professional medical advice, clinical diagnosis, or treatment. "
    "Never disregard professional medical advice or delay seeking care because of something you have read here. "
    "If you are experiencing severe symptoms, chest pain, difficulty breathing, or a medical emergency, "
    "please call your local emergency services (e.g., 911 / 112 / 102) immediately."
)

class PredictionRequest(BaseModel):
    symptoms: List[str] = Field(
        ...,
        min_length=1,
        description="List of symptoms entered by the user (at least one symptom is required)"
    )
    allow_ai_fallback: bool = Field(
        default=True,
        description="Whether to use configured server-side AI fallback if symptoms are not recognized in ML vocabulary"
    )

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty symptom must be provided.")
        return cleaned

class PredictionResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was processed successfully")
    mode: PredictionMode = Field(..., description="Operating mode: ml_prediction, ai_assisted, clarification_required, or fallback")
    predicted_disease: Optional[str] = Field(None, description="Predicted condition or health insight title")
    confidence: Optional[float] = Field(None, description="Calibrated confidence score if provided by the model; None if unsupported")
    description: Optional[str] = Field(None, description="Overview or description of the condition")
    medications: List[str] = Field(default_factory=list, description="Informational medication list (top-5 preserved from dataset)")
    precautions: List[str] = Field(default_factory=list, description="Preventative measures and precautions")
    diet_recommendations: List[str] = Field(default_factory=list, description="Dietary guidelines and lifestyle nutrition")
    workout_recommendations: List[str] = Field(default_factory=list, description="Exercise and physical activity recommendations")
    recognized_symptoms: List[str] = Field(default_factory=list, description="Symptoms successfully matched to the ML vocabulary")
    unrecognized_symptoms: List[str] = Field(default_factory=list, description="Submitted symptoms that were outside the ML vocabulary")
    mapped_symptoms: List[str] = Field(default_factory=list, description="Symptoms resolved via synonyms or aliases")
    message: str = Field(..., description="Summary user-facing status message")
    disclaimer: str = Field(default=DEFAULT_DISCLAIMER, description="Mandatory medical and emergency safety disclaimer")

class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall service status (healthy, degraded, unhealthy)")
    app_name: str
    version: str = "2.0.0"
    environment: str
    model_loaded: bool
    gemini_configured: bool
    supported_symptoms_count: int = 132
    supported_diseases_count: int = 41
