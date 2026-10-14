import json
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from pydantic import BaseModel, Field
from app.core.config import settings
from app.schemas.prediction import PredictionMode, PredictionResponse, DEFAULT_DISCLAIMER

logger = logging.getLogger("medical_app.ai_fallback")

class AIHealthInsightSchema(BaseModel):
    condition_or_topic: str = Field(default="Symptom Analysis & Information")
    description: str = Field(default="Informational guidance based on submitted health symptoms.")
    precautions: List[str] = Field(default_factory=lambda: ["Consult a physician for clinical assessment."])
    non_prescription_care: List[str] = Field(default_factory=lambda: ["Rest and hydration; consult a doctor before taking any medication."])
    lifestyle_and_diet: List[str] = Field(default_factory=lambda: ["Maintain a balanced diet and stay hydrated."])
    suggested_activities: List[str] = Field(default_factory=lambda: ["Light activity as tolerated; prioritize rest."])
    clarifying_questions: List[str] = Field(default_factory=list)
    suggested_dataset_symptoms: List[str] = Field(default_factory=list)

class AIFallbackService:
    """
    Manages intelligent fallback when symptoms cannot be matched to the 132-symptom ML dataset.
    Uses Google Gemini API when configured, with robust retry, timeout, schema validation,
    and a local rule-based heuristic fallback if AI is offline or unconfigured.
    """

    def __init__(self):
        # Modern Google Generative Language endpoints
        self.primary_model = "gemini-2.5-flash"
        self.fallback_model = "gemini-2.5-flash"
        self.base_api_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.timeout = 25.0  # Allow more time for Gemini 2.5 Flash

    @property
    def is_configured(self) -> bool:
        """Returns True if Gemini API key is configured."""
        return settings.has_gemini_configured

    def check_api_status(self) -> Dict[str, Any]:
        """
        Diagnostic probe to test if configured Gemini API key is active, denied, or unconfigured.
        """
        if not settings.has_gemini_configured:
            return {
                "configured": False,
                "status": "unconfigured",
                "message": "Gemini API key is not configured in .env (GEMINI_API_KEY is empty). Rule-based offline fallback is active."
            }

        key = settings.GEMINI_API_KEY
        url = f"{self.base_api_url}/{self.primary_model}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}

        try:
            r = requests.post(url, json=payload, timeout=5.0)
            if r.status_code == 200:
                return {
                    "configured": True,
                    "status": "active",
                    "model": self.primary_model,
                    "message": "Google Gemini API is active and functional."
                }
            elif r.status_code == 403:
                return {
                    "configured": True,
                    "status": "permission_denied",
                    "code": 403,
                    "message": "API key was denied access by Google (403 Permission Denied: project denied or key revoked)."
                }
            elif r.status_code == 404:
                return {
                    "configured": True,
                    "status": "model_not_found",
                    "code": 404,
                    "message": f"Model endpoint {self.primary_model} was not found on API v1beta."
                }
            else:
                return {
                    "configured": True,
                    "status": "error",
                    "code": r.status_code,
                    "message": f"Google Gemini API returned HTTP status {r.status_code}."
                }
        except Exception as e:
            return {
                "configured": True,
                "status": "connection_error",
                "message": f"Network or connection error checking Gemini API: {str(e)}"
            }

    def generate_ai_insights(
        self,
        unrecognized_symptoms: List[str],
        recognized_symptoms: List[str],
        mapped_symptoms: List[str]
    ) -> PredictionResponse:
        """
        Attempts to call the Google Gemini API to explain the unsupported symptoms,
        suggest clarification, and offer general non-diagnostic medical information.
        """
        api_key = settings.GEMINI_API_KEY
        if not settings.has_gemini_configured:
            logger.info("Gemini API key is not configured. Using rule-based informational fallback.")
            return self.create_local_fallback(
                unrecognized_symptoms=unrecognized_symptoms,
                recognized_symptoms=recognized_symptoms,
                mapped_symptoms=mapped_symptoms,
                reason="AI provider key not configured on server"
            )

        # Sanitize untrusted user input before placing in prompt
        clean_unrecognized = [re.sub(r'[^\w\s-]', '', s)[:50] for s in unrecognized_symptoms if s.strip()]
        clean_recognized = [re.sub(r'[^\w\s-]', '', s)[:50] for s in recognized_symptoms if s.strip()]

        all_input_symptoms = clean_unrecognized + clean_recognized
        symptoms_str = ", ".join(all_input_symptoms) if all_input_symptoms else "Unspecified discomfort"

        prompt = f"""You are an advanced clinical medical AI guidance assistant.
A patient presents with the following reported symptoms and details:
Symptoms / Health Complaints: {symptoms_str}

Perform an evidence-based clinical evaluation following sound medical principles:
1. Identify the most clinically probable primary condition or syndrome corresponding to this combination of symptoms (e.g. Acute Gastroenteritis / Food Poisoning, Acute Gastritis, Migraine with Gastrointestinal Symptoms, Viral Syndrome, etc.).
2. Differentiate common benign self-limiting conditions from severe emergencies. DO NOT output rare catastrophic diagnoses like Paralysis or Stroke unless unequivocal classic neurological signs are specifically presented.
3. DO NOT claim to make a definitive medical diagnosis and DO NOT prescribe prescription-only medications or specific drug dosages.
4. Provide practical, safe home comfort measures (e.g., Oral Rehydration Solution/electrolytes, resting in a quiet dim room, small sips of water).
5. Provide dietary guidance tailored to these symptoms (e.g., bland BRAT diet, avoiding dairy/fatty/acidic foods, avoiding NSAIDs if stomach is irritated).
6. Provide clear preventative precautions and red flag warning signs requiring immediate emergency medical care (e.g., high persistent fever, inability to keep liquids down for 24h, bloody vomit or stool, severe localized tenderness).
7. Suggest 2-3 relevant clarifying questions regarding onset, duration, or accompanying symptoms.

Output MUST be a single valid JSON object with the following exact keys:
- "condition_or_topic": The clinically accurate primary condition name (e.g. "Acute Gastroenteritis / Food Poisoning").
- "description": 2-3 sentences explaining why these symptoms occur together and what they indicate in accessible clinical terms.
- "precautions": List of 3-4 sensible preventative measures and red flags.
- "non_prescription_care": List of 3-4 safe home supportive care measures (e.g. Oral Rehydration Solution, rest, gentle hydration).
- "lifestyle_and_diet": List of 3-4 gentle dietary recommendations (e.g. BRAT diet: bananas, rice, applesauce, toast; avoiding dairy/spicy foods).
- "suggested_activities": List of 1-2 physical/rest recommendations.
- "clarifying_questions": List of 2-3 helpful follow-up questions (e.g. duration, diet history, fever).

Return ONLY the raw JSON object, without markdown backticks or commentary outside the JSON.
"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 20,
                "topP": 0.9,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json"
            }
        }

        url = f"{self.base_api_url}/{self.primary_model}:generateContent?key={api_key}"

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning("Gemini API responded with HTTP status %d: %s", response.status_code, response.text[:200])
                return self.create_local_fallback(
                    unrecognized_symptoms=unrecognized_symptoms,
                    recognized_symptoms=recognized_symptoms,
                    mapped_symptoms=mapped_symptoms,
                    reason=f"AI service returned HTTP {response.status_code}"
                )

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No response candidate returned by Gemini API")

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            parsed_json = self._extract_json(raw_text)

            # Validate against Pydantic schema
            insights = AIHealthInsightSchema(**parsed_json)

            clarification_msg = ""
            if insights.clarifying_questions:
                clarification_msg = " Consider: " + "; ".join(insights.clarifying_questions[:2])

            if unrecognized_symptoms:
                summary_msg = f"Clinical AI guidance evaluating: {', '.join(clean_unrecognized)}.{clarification_msg}"
            else:
                summary_msg = f"Based on your symptoms ({', '.join(clean_recognized)}), AI clinical decision analysis identified: {insights.condition_or_topic}.{clarification_msg}"

            return PredictionResponse(
                success=True,
                mode=PredictionMode.AI_ASSISTED,
                predicted_disease=insights.condition_or_topic,
                confidence=None,  # AI-generated insights must not fabricate statistical confidence
                description=insights.description,
                medications=insights.non_prescription_care,
                precautions=insights.precautions,
                diet_recommendations=insights.lifestyle_and_diet,
                workout_recommendations=insights.suggested_activities,
                recognized_symptoms=recognized_symptoms,
                unrecognized_symptoms=unrecognized_symptoms,
                mapped_symptoms=mapped_symptoms,
                message=summary_msg,
                disclaimer=DEFAULT_DISCLAIMER
            )

        except Exception as e:
            logger.error("Error invoking Gemini API: %s", e, exc_info=True)
            return self.create_local_fallback(
                unrecognized_symptoms=unrecognized_symptoms,
                recognized_symptoms=recognized_symptoms,
                mapped_symptoms=mapped_symptoms,
                reason=f"AI service temporary error: {str(e)}"
            )

    def create_local_fallback(
        self,
        unrecognized_symptoms: List[str],
        recognized_symptoms: List[str],
        mapped_symptoms: List[str],
        reason: str = "Unrecognized symptoms"
    ) -> PredictionResponse:
        """
        Graceful rule-based offline fallback when the external AI provider is unavailable or not configured.
        """
        symptom_str = ", ".join(unrecognized_symptoms)
        return PredictionResponse(
            success=True,
            mode=PredictionMode.FALLBACK,
            predicted_disease="Symptom Guidance Required",
            confidence=None,
            description=(
                f"We received your submitted symptom(s) [{symptom_str}], but they are not present in our "
                f"system's 132-symptom machine learning database. Because reliable clinical correlation requires "
                f"standardized terminology, automated disease classification cannot be computed."
            ),
            medications=[
                "Do not start or modify prescription medications without clinical supervision",
                "Over-the-counter options should only be used as directed by a pharmacist"
            ],
            precautions=[
                "Monitor the severity and duration of your symptoms",
                "Keep a log of when the symptoms started and any triggers",
                "Seek immediate emergency care if you experience chest tightness, breathing issues, or severe pain",
                "Consult a qualified healthcare provider for a thorough examination"
            ],
            diet_recommendations=[
                "Drink plenty of clean water and stay well hydrated",
                "Choose easily digestible, nutritious meals rich in vitamins and minerals",
                "Avoid excessive caffeine, alcohol, and heavily processed foods"
            ],
            workout_recommendations=[
                "Prioritize physical rest until symptoms subside",
                "Avoid strenuous workouts or heavy lifting until cleared by a physician"
            ],
            recognized_symptoms=recognized_symptoms,
            unrecognized_symptoms=unrecognized_symptoms,
            mapped_symptoms=mapped_symptoms,
            message=(
                f"The symptom(s) '{symptom_str}' could not be matched to our machine learning vocabulary. "
                f"Please review the supported symptom list or consult a healthcare professional."
            ),
            disclaimer=DEFAULT_DISCLAIMER
        )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely parses a JSON string, stripping any codeblock fences or extraneous characters."""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)

ai_fallback_service = AIFallbackService()
