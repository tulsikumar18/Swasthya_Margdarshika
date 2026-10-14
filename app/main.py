import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.ml.model_loader import model_registry
from app.api.routes.health import router as health_router
from app.api.routes.symptoms import router as symptoms_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.pages import router as pages_router

# Setup structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medical_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager:
    Loads machine learning models and datasets into memory once on application startup.
    Cleans up resources gracefully on shutdown.
    """
    logger.info("Initializing %s in %s mode...", settings.APP_NAME, settings.APP_ENV)
    try:
        model_registry.load_all()
        logger.info("Machine learning model and datasets ready.")
    except Exception as e:
        logger.error("Startup Warning: Could not pre-load model/datasets: %s", e)

    yield

    logger.info("Application shutting down. Releasing resources...")

def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Modernized Personalized Medical Recommendation System utilizing Machine Learning "
            "(Scikit-learn SVC) and intelligent AI fallback (Google Gemini) for clinical guidance."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Session middleware for user login & authentication
    from starlette.middleware.sessions import SessionMiddleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="swasthya_session",
        max_age=14 * 24 * 3600  # 14 days
    )

    # Enable CORS for local development and dashboard access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Validation exception handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error on %s: %s", request.url.path, exc)
        formatted_errors = [
            {"loc": err.get("loc", ()), "msg": str(err.get("msg", "")), "type": err.get("type", "")}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation Error",
                "details": formatted_errors,
                "message": "Invalid request parameters. Please verify your symptom input."
            }
        )

    # Static files mounting
    # Check if app/static exists, otherwise use root static
    static_path = settings.BASE_DIR / "app" / "static"
    if not static_path.exists():
        static_path = settings.BASE_DIR / "static"

    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info("Static files mounted from: %s", static_path)

    # Register API Routers
    app.include_router(health_router)
    app.include_router(symptoms_router)
    app.include_router(predictions_router)
    app.include_router(pages_router)

    return app

app = create_app()
