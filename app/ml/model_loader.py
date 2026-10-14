import os
import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from app.core.config import settings

logger = logging.getLogger("medical_app.model_loader")

class ModelRegistry:
    """
    Singleton registry to load and hold the ML model and recommendation datasets in memory.
    Initialized once during application lifespan startup.
    """
    _instance: Optional["ModelRegistry"] = None

    def __init__(self):
        self.model: Optional[Any] = None
        self.description_df: Optional[pd.DataFrame] = None
        self.precautions_df: Optional[pd.DataFrame] = None
        self.medications_df: Optional[pd.DataFrame] = None
        self.diets_df: Optional[pd.DataFrame] = None
        self.workout_df: Optional[pd.DataFrame] = None
        self.severity_df: Optional[pd.DataFrame] = None
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def load_all(self) -> None:
        """Loads model file and CSV datasets into memory."""
        try:
            # 1. Load SVC Model
            model_file = None
            if settings.MODEL_PATH.exists():
                model_file = settings.MODEL_PATH
            elif settings.CHECKPOINT_MODEL_PATH.exists():
                model_file = settings.CHECKPOINT_MODEL_PATH
            else:
                raise FileNotFoundError(
                    f"SVC model file not found at {settings.MODEL_PATH} or {settings.CHECKPOINT_MODEL_PATH}"
                )

            logger.info("Loading SVC model from: %s", model_file)
            with open(model_file, "rb") as f:
                self.model = pickle.load(f)

            # 2. Load Datasets
            d_dir = settings.DATASETS_DIR
            if not d_dir.exists():
                raise FileNotFoundError(f"Datasets directory not found at: {d_dir}")

            self.description_df = pd.read_csv(d_dir / "description.csv")
            self.precautions_df = pd.read_csv(d_dir / "precautions_df.csv")
            self.medications_df = pd.read_csv(d_dir / "medications.csv")
            self.diets_df = pd.read_csv(d_dir / "diets.csv")
            self.workout_df = pd.read_csv(d_dir / "workout_df.csv")

            if (d_dir / "Symptom-severity.csv").exists():
                self.severity_df = pd.read_csv(d_dir / "Symptom-severity.csv")

            self.is_loaded = True
            self.load_error = None
            logger.info("ML Model and all datasets loaded successfully.")

        except Exception as e:
            self.is_loaded = False
            self.load_error = str(e)
            logger.error("Failed to load ML model or datasets: %s", e, exc_info=True)
            raise e

    def get_status(self) -> Dict[str, Any]:
        return {
            "loaded": self.is_loaded,
            "model_type": type(self.model).__name__ if self.model else None,
            "error": self.load_error,
            "datasets": {
                "description": self.description_df is not None,
                "precautions": self.precautions_df is not None,
                "medications": self.medications_df is not None,
                "diets": self.diets_df is not None,
                "workout": self.workout_df is not None,
                "severity": self.severity_df is not None,
            }
        }

model_registry = ModelRegistry.get_instance()
