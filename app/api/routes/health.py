from fastapi import APIRouter
from app.core.config import settings
from app.ml.model_loader import model_registry
from app.schemas.prediction import HealthCheckResponse
from app.services.ai_fallback_service import ai_fallback_service

router = APIRouter(prefix="/api", tags=["System"])

@router.get("/health", response_model=HealthCheckResponse, summary="System Health Check")
async def health_check():
    """
    Returns system status, model availability, AI configuration status,
    and metadata regarding supported datasets.
    """
    model_status = model_registry.get_status()
    is_healthy = model_status["loaded"]

    return HealthCheckResponse(
        status="healthy" if is_healthy else "degraded",
        app_name=settings.APP_NAME,
        version="2.0.0",
        environment=settings.APP_ENV,
        model_loaded=model_status["loaded"],
        gemini_configured=settings.has_gemini_configured,
        supported_symptoms_count=132,
        supported_diseases_count=41
    )

@router.get("/ai/status", summary="Check Gemini AI Key and Provider Status")
async def ai_status():
    """
    Probes Google Gemini API to test if the key is valid, unconfigured, or denied access.
    """
    return ai_fallback_service.check_api_status()
