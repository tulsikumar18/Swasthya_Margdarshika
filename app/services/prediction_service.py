import logging
from typing import List, Optional
import numpy as np
import pandas as pd

from app.ml.model_loader import model_registry
from app.ml.preprocessing import (
    analyze_symptom_list,
    build_feature_vector,
    DISEASES_LIST,
    SYMPTOMS_DICT,
    get_readable_symptom_name
)
from app.services.recommendation_service import recommendation_service
from app.services.ai_fallback_service import ai_fallback_service
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionMode,
    DEFAULT_DISCLAIMER
)

logger = logging.getLogger("medical_app.prediction_service")

# Minimum number of recognized symptoms required before running the SVC model.
# With fewer symptoms the model's 132-feature space is too sparse to be reliable.
MIN_SYMPTOMS_FOR_ML = 4

class PredictionService:
    """
    Coordinates symptom analysis, ML classification, recommendation retrieval,
    and intelligent AI fallback routing.
    """

    @staticmethod
    def predict_disease(request: PredictionRequest) -> PredictionResponse:
        """
        Executes prediction workflow:
        1. Validates and normalizes symptoms.
        2. Categorizes into recognized, mapped, and unknown.
        3. If 100% recognized (or cleanly mapped): uses trained SVC model and CSV recommendations.
        4. If unknown symptoms exist: routes to AI fallback service or offline guidance.
        """
        raw_symptoms = request.symptoms
        if not raw_symptoms:
            raise ValueError("No symptoms provided for diagnosis.")

        # Ensure model is ready
        if not model_registry.is_loaded or model_registry.model is None:
            logger.warning("Model registry not loaded, attempting load...")
            model_registry.load_all()

        recognized_keys, mapped_notes, unknown_symptoms = analyze_symptom_list(raw_symptoms)

        logger.info(
            "Symptom analysis result: recognized=%s, mapped=%s, unknown=%s",
            recognized_keys, mapped_notes, unknown_symptoms
        )

        # Case 1: Unrecognized symptoms present
        if unknown_symptoms:
            if request.allow_ai_fallback:
                return ai_fallback_service.generate_ai_insights(
                    unrecognized_symptoms=unknown_symptoms,
                    recognized_symptoms=recognized_keys,
                    mapped_symptoms=mapped_notes
                )
            else:
                return ai_fallback_service.create_local_fallback(
                    unrecognized_symptoms=unknown_symptoms,
                    recognized_symptoms=recognized_keys,
                    mapped_symptoms=mapped_notes
                )

        # Case 2: No valid recognized symptoms were identified at all
        if not recognized_keys:
            return PredictionResponse(
                success=False,
                mode=PredictionMode.CLARIFICATION_REQUIRED,
                predicted_disease=None,
                confidence=None,
                description="Unable to recognize any valid clinical symptoms in your submission.",
                medications=[],
                precautions=["Please select or type recognized symptoms such as headache, fever, cough, or fatigue."],
                diet_recommendations=[],
                workout_recommendations=[],
                recognized_symptoms=[],
                unrecognized_symptoms=raw_symptoms,
                mapped_symptoms=[],
                message="Please choose one or more symptoms from our recognized symptom list.",
                disclaimer=DEFAULT_DISCLAIMER
            )

        # Case 3: Fewer than 4 symptoms provided - require at least MIN_SYMPTOMS_FOR_ML (4) symptoms
        if len(recognized_keys) < MIN_SYMPTOMS_FOR_ML:
            readable = [get_readable_symptom_name(k) for k in recognized_keys]
            readable_str = ", ".join(readable)
            needed_count = MIN_SYMPTOMS_FOR_ML - len(recognized_keys)
            return PredictionResponse(
                success=False,
                mode=PredictionMode.CLARIFICATION_REQUIRED,
                predicted_disease=None,
                confidence=None,
                description=(
                    f"You have provided {len(recognized_keys)} symptom(s): {readable_str}. "
                    f"To ensure an accurate and reliable diagnosis, at least {MIN_SYMPTOMS_FOR_ML} symptoms are required. "
                    "Common symptoms overlap across multiple conditions, so additional health markers are needed."
                ),
                medications=[],
                precautions=[
                    f"Please enter or select at least {needed_count} more symptom(s) to proceed.",
                    "Consider: Any fever, chills, fatigue, dizziness, or stomach discomfort?",
                    "You can type naturally in the search box or select from the common symptom chips below."
                ],
                diet_recommendations=[],
                workout_recommendations=[],
                recognized_symptoms=recognized_keys,
                unrecognized_symptoms=[],
                mapped_symptoms=mapped_notes,
                message=(
                    f"At least {MIN_SYMPTOMS_FOR_ML} symptoms are required for analysis. "
                    f"You entered {len(recognized_keys)} ({readable_str}) — please add at least {needed_count} more."
                ),
                disclaimer=DEFAULT_DISCLAIMER
            )

        # Case 4: All symptoms are recognized in our ML model's vocabulary
        feature_vector = build_feature_vector(recognized_keys)

        # Run trained ML classifier model
        model = model_registry.model
        feature_df = pd.DataFrame([feature_vector], columns=list(SYMPTOMS_DICT.keys()))
        prediction_index_array = model.predict(feature_df)
        predicted_class_id = int(prediction_index_array[0])

        predicted_disease_raw = DISEASES_LIST.get(predicted_class_id, "Unknown Condition")
        predicted_disease = predicted_disease_raw.strip()

        # Query recommendation datasets
        recs = recommendation_service.get_recommendations_for_disease(predicted_disease)

        readable_symptoms = [get_readable_symptom_name(k) for k in recognized_keys]

        message = f"Based on your symptoms ({', '.join(readable_symptoms)}), our machine learning model identified {predicted_disease}."
        if mapped_notes:
            message += f" Note: Matched aliases: {', '.join(mapped_notes)}."

        return PredictionResponse(
            success=True,
            mode=PredictionMode.ML_PREDICTION,
            predicted_disease=predicted_disease,
            confidence=None,  # SVC was trained with probability=False; explicit None avoids false values
            description=recs["description"],
            medications=recs["medications"],
            precautions=recs["precautions"],
            diet_recommendations=recs["diet"],
            workout_recommendations=recs["workouts"],
            recognized_symptoms=recognized_keys,
            unrecognized_symptoms=[],
            mapped_symptoms=mapped_notes,
            message=message,
            disclaimer=DEFAULT_DISCLAIMER
        )

prediction_service = PredictionService()
