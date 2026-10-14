import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import prediction_service

logger = logging.getLogger("medical_app.routes.predictions")

router = APIRouter(prefix="/api", tags=["Predictions"])

@router.post("/predict", response_model=PredictionResponse, summary="Analyze Symptoms and Predict Condition")
async def predict_condition(request: PredictionRequest):
    """
    Analyzes submitted symptoms:
    - Normalizes input safely.
    - If symptoms belong to the 132-symptom vocabulary: executes trained Scikit-learn SVC model
      and retrieves matching description, top-5 medications, precautions, diet, and workouts.
    - If symptoms are outside the vocabulary: calls server-side AI fallback (Gemini) or rule-based guidance.
    - Returns standardized response with explicit mode and medical safety disclaimer.
    """
    try:
        response = prediction_service.predict_disease(request)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error processing symptom prediction: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating symptoms. Please try again later."
        )
