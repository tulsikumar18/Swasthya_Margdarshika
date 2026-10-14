import ast
import re
import logging
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from app.ml.model_loader import model_registry

logger = logging.getLogger("medical_app.recommendation_service")

def _normalize_name_for_lookup(name: str) -> str:
    """Standardizes condition name for matching across varying dataset spellings."""
    if not name:
        return ""
    # Collapse multiple spaces and lowercase
    s = re.sub(r'\s+', ' ', name).strip().lower()
    # Normalize common dataset typo
    if "peptic ulcer" in s:
        return "peptic ulcer disease"
    if "vertigo" in s:
        return "vertigo paroxysmal positional vertigo"
    return s

def _parse_list_field(val: Any) -> List[str]:
    """Safely extracts a list of strings from either a Python list, stringified list, or string."""
    if val is None or pd.isna(val):
        return []
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if x and str(x).strip()]

    str_val = str(val).strip()
    if not str_val:
        return []

    # If it looks like a stringified Python list "['item1', 'item2']"
    if (str_val.startswith("[") and str_val.endswith("]")) or (str_val.startswith("(") and str_val.endswith(")")):
        try:
            parsed = ast.literal_eval(str_val)
            if isinstance(parsed, (list, tuple)):
                return [str(x).strip() for x in parsed if x and str(x).strip()]
        except Exception:
            # Fallback to comma split if ast fails
            cleaned = str_val.strip("[]()'")
            return [x.strip().strip("'\"") for x in cleaned.split(",") if x.strip()]

    return [str_val]

class RecommendationService:
    """Service to look up descriptions, top medications, precautions, diet, and workouts from datasets."""

    @staticmethod
    def get_recommendations_for_disease(disease: str) -> Dict[str, Any]:
        """
        Retrieves complete structured recommendation profile for a predicted condition.
        Returns description, precautions, top medications (top-5 preserved), diet, and workouts.
        """
        registry = model_registry
        norm_target = _normalize_name_for_lookup(disease)

        # 1. Description
        description = "No detailed description available in local medical records."
        if registry.description_df is not None:
            df = registry.description_df
            match = df[df['Disease'].apply(lambda d: _normalize_name_for_lookup(str(d)) == norm_target)]
            if not match.empty:
                val = match.iloc[0]['Description']
                if pd.notna(val) and str(val).strip():
                    description = str(val).strip()

        # 2. Precautions (Precaution_1 .. Precaution_4)
        precautions: List[str] = []
        if registry.precautions_df is not None:
            df = registry.precautions_df
            match = df[df['Disease'].apply(lambda d: _normalize_name_for_lookup(str(d)) == norm_target)]
            if not match.empty:
                row = match.iloc[0]
                for col in ['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        val = str(row[col]).strip().capitalize()
                        if val and val not in precautions:
                            precautions.append(val)

        # 3. Medications (Top-5 informational medication list)
        medications: List[str] = []
        if registry.medications_df is not None:
            df = registry.medications_df
            match = df[df['Disease'].apply(lambda d: _normalize_name_for_lookup(str(d)) == norm_target)]
            if not match.empty:
                raw_med = match.iloc[0]['Medication']
                medications = _parse_list_field(raw_med)

        # 4. Dietary recommendations
        diet: List[str] = []
        if registry.diets_df is not None:
            df = registry.diets_df
            match = df[df['Disease'].apply(lambda d: _normalize_name_for_lookup(str(d)) == norm_target)]
            if not match.empty:
                raw_diet = match.iloc[0]['Diet']
                diet = _parse_list_field(raw_diet)

        # 5. Workout / Exercise recommendations
        workouts: List[str] = []
        if registry.workout_df is not None:
            df = registry.workout_df
            disease_col = 'Disease' if 'Disease' in df.columns else 'disease'
            match = df[df[disease_col].apply(lambda d: _normalize_name_for_lookup(str(d)) == norm_target)]
            if not match.empty:
                for _, row in match.iterrows():
                    val = row.get('workout') or row.get('Workout')
                    if pd.notna(val) and str(val).strip():
                        w = str(val).strip()
                        if w not in workouts:
                            workouts.append(w)

        # Ensure fallbacks if any list is empty
        if not precautions:
            precautions = ["Consult a certified healthcare provider for clinical evaluation."]
        if not medications:
            medications = ["Consult a physician or licensed pharmacist for prescription guidelines."]
        if not diet:
            diet = ["Maintain adequate hydration and a nutrient-rich, balanced diet."]
        if not workouts:
            workouts = ["Engage in light physical activity as tolerated; avoid excessive strain."]

        return {
            "disease": disease.strip(),
            "description": description,
            "precautions": precautions,
            "medications": medications[:5],  # Preserve top-5 medications
            "diet": diet,
            "workouts": workouts
        }

recommendation_service = RecommendationService()
