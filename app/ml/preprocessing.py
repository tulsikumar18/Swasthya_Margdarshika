import re
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Exact symptom dictionary with 132 symptoms and their feature column index
SYMPTOMS_DICT: Dict[str, int] = {
    'itching': 0, 'skin_rash': 1, 'nodal_skin_eruptions': 2, 'continuous_sneezing': 3,
    'shivering': 4, 'chills': 5, 'joint_pain': 6, 'stomach_pain': 7, 'acidity': 8,
    'ulcers_on_tongue': 9, 'muscle_wasting': 10, 'vomiting': 11, 'burning_micturition': 12,
    'spotting_ urination': 13, 'fatigue': 14, 'weight_gain': 15, 'anxiety': 16,
    'cold_hands_and_feets': 17, 'mood_swings': 18, 'weight_loss': 19, 'restlessness': 20,
    'lethargy': 21, 'patches_in_throat': 22, 'irregular_sugar_level': 23, 'cough': 24,
    'high_fever': 25, 'sunken_eyes': 26, 'breathlessness': 27, 'sweating': 28,
    'dehydration': 29, 'indigestion': 30, 'headache': 31, 'yellowish_skin': 32,
    'dark_urine': 33, 'nausea': 34, 'loss_of_appetite': 35, 'pain_behind_the_eyes': 36,
    'back_pain': 37, 'constipation': 38, 'abdominal_pain': 39, 'diarrhoea': 40,
    'mild_fever': 41, 'yellow_urine': 42, 'yellowing_of_eyes': 43, 'acute_liver_failure': 44,
    'fluid_overload': 45, 'swelling_of_stomach': 46, 'swelled_lymph_nodes': 47,
    'malaise': 48, 'blurred_and_distorted_vision': 49, 'phlegm': 50, 'throat_irritation': 51,
    'redness_of_eyes': 52, 'sinus_pressure': 53, 'runny_nose': 54, 'congestion': 55,
    'chest_pain': 56, 'weakness_in_limbs': 57, 'fast_heart_rate': 58,
    'pain_during_bowel_movements': 59, 'pain_in_anal_region': 60, 'bloody_stool': 61,
    'irritation_in_anus': 62, 'neck_pain': 63, 'dizziness': 64, 'cramps': 65,
    'bruising': 66, 'obesity': 67, 'swollen_legs': 68, 'swollen_blood_vessels': 69,
    'puffy_face_and_eyes': 70, 'enlarged_thyroid': 71, 'brittle_nails': 72,
    'swollen_extremeties': 73, 'excessive_hunger': 74, 'extra_marital_contacts': 75,
    'drying_and_tingling_lips': 76, 'slurred_speech': 77, 'knee_pain': 78,
    'hip_joint_pain': 79, 'muscle_weakness': 80, 'stiff_neck': 81, 'swelling_joints': 82,
    'movement_stiffness': 83, 'spinning_movements': 84, 'loss_of_balance': 85,
    'unsteadiness': 86, 'weakness_of_one_body_side': 87, 'loss_of_smell': 88,
    'bladder_discomfort': 89, 'foul_smell_of urine': 90, 'continuous_feel_of_urine': 91,
    'passage_of_gases': 92, 'internal_itching': 93, 'toxic_look_(typhos)': 94,
    'depression': 95, 'irritability': 96, 'muscle_pain': 97, 'altered_sensorium': 98,
    'red_spots_over_body': 99, 'belly_pain': 100, 'abnormal_menstruation': 101,
    'dischromic _patches': 102, 'watering_from_eyes': 103, 'increased_appetite': 104,
    'polyuria': 105, 'family_history': 106, 'mucoid_sputum': 107, 'rusty_sputum': 108,
    'lack_of_concentration': 109, 'visual_disturbances': 110,
    'receiving_blood_transfusion': 111, 'receiving_unsterile_injections': 112,
    'coma': 113, 'stomach_bleeding': 114, 'distention_of_abdomen': 115,
    'history_of_alcohol_consumption': 116, 'fluid_overload.1': 117, 'blood_in_sputum': 118,
    'prominent_veins_on_calf': 119, 'palpitations': 120, 'painful_walking': 121,
    'pus_filled_pimples': 122, 'blackheads': 123, 'scurring': 124, 'skin_peeling': 125,
    'silver_like_dusting': 126, 'small_dents_in_nails': 127, 'inflammatory_nails': 128,
    'blister': 129, 'red_sore_around_nose': 130, 'yellow_crust_ooze': 131
}

# Exact disease mapping from trained SVC model classes
DISEASES_LIST: Dict[int, str] = {
    15: 'Fungal infection', 4: 'Allergy', 16: 'GERD', 9: 'Chronic cholestasis',
    14: 'Drug Reaction', 33: 'Peptic ulcer diseae', 1: 'AIDS', 12: 'Diabetes ',
    17: 'Gastroenteritis', 6: 'Bronchial Asthma', 23: 'Hypertension ', 30: 'Migraine',
    7: 'Cervical spondylosis', 32: 'Paralysis (brain hemorrhage)', 28: 'Jaundice',
    29: 'Malaria', 8: 'Chicken pox', 11: 'Dengue', 37: 'Typhoid', 40: 'hepatitis A',
    19: 'Hepatitis B', 20: 'Hepatitis C', 21: 'Hepatitis D', 22: 'Hepatitis E',
    3: 'Alcoholic hepatitis', 36: 'Tuberculosis', 10: 'Common Cold', 34: 'Pneumonia',
    13: 'Dimorphic hemmorhoids(piles)', 18: 'Heart attack', 39: 'Varicose veins',
    26: 'Hypothyroidism', 24: 'Hyperthyroidism', 25: 'Hypoglycemia', 31: 'Osteoarthristis',
    5: 'Arthritis', 0: '(vertigo) Paroymsal  Positional Vertigo', 2: 'Acne',
    38: 'Urinary tract infection', 35: 'Psoriasis', 27: 'Impetigo'
}

# Common user-friendly aliases mapped safely to exact dataset feature keys
SYMPTOM_ALIASES: Dict[str, str] = {
    'stomach ache': 'stomach_pain',
    'stomachache': 'stomach_pain',
    'stomach pain': 'stomach_pain',
    'belly ache': 'belly_pain',
    'belly pain': 'belly_pain',
    'head ache': 'headache',
    'high temp': 'high_fever',
    'fever': 'high_fever',
    'high temperature': 'high_fever',
    'runny nose': 'runny_nose',
    'skin rash': 'skin_rash',
    'rash': 'skin_rash',
    'joint pain': 'joint_pain',
    'chest pain': 'chest_pain',
    'back pain': 'back_pain',
    'neck pain': 'neck_pain',
    'knee pain': 'knee_pain',
    'muscle pain': 'muscle_pain',
    'shortness of breath': 'breathlessness',
    'difficulty breathing': 'breathlessness',
    'breathless': 'breathlessness',
    'rapid heartbeat': 'fast_heart_rate',
    'fast heartbeat': 'fast_heart_rate',
    'heart palpitations': 'palpitations',
    'tiredness': 'fatigue',
    'exhaustion': 'fatigue',
    'throwing up': 'vomiting',
    'vomit': 'vomiting',
    'nauseous': 'nausea',
    'feeling sick': 'nausea',
    'loose motion': 'diarrhoea',
    'loose motions': 'diarrhoea',
    'loose stools': 'diarrhoea',
    'diarrhea': 'diarrhoea',
    'gas': 'passage_of_gases',
    'gases': 'passage_of_gases',
    'acidity': 'acidity',
    'acid reflux': 'acidity',
    'heartburn': 'acidity',
    'ulcers on tongue': 'ulcers_on_tongue',
    'tongue ulcers': 'ulcers_on_tongue',
    'mouth ulcers': 'ulcers_on_tongue',
    'bloating': 'distention_of_abdomen',
    'blurred vision': 'blurred_and_distorted_vision',
    'sneezing': 'continuous_sneezing',
    'sneeze': 'continuous_sneezing',
    'yellow eyes': 'yellowing_of_eyes',
    'yellow skin': 'yellowish_skin',
    'dark urine': 'dark_urine',
    'loss of appetite': 'loss_of_appetite',
    'no appetite': 'loss_of_appetite',
    'swollen joints': 'swelling_joints',
    'throat pain': 'throat_irritation',
    'sore throat': 'throat_irritation',
    'coughing': 'cough',
}

def clean_symptom_text(text: str) -> str:
    """Safely cleans and standardizes user text input."""
    if not text:
        return ""
    # Strip brackets, quotes, and punctuation
    cleaned = text.strip("[]'\" \t\n\r")
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.lower()

def normalize_symptom_to_key(symptom: str) -> Optional[str]:
    """
    Attempts to match a user symptom to an exact key in SYMPTOMS_DICT.
    Supports exact match, underscore/space variations, and known aliases.
    """
    raw = clean_symptom_text(symptom)
    if not raw:
        return None

    # Check exact key directly
    if raw in SYMPTOMS_DICT:
        return raw

    # Convert spaces to underscores and check
    with_underscores = raw.replace(' ', '_')
    if with_underscores in SYMPTOMS_DICT:
        return with_underscores

    # Check known aliases
    if raw in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[raw]
    if with_underscores in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[with_underscores]

    # Check reverse: if user entered underscore format, check alias map for space
    with_spaces = raw.replace('_', ' ')
    if with_spaces in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[with_spaces]

    return None

def extract_symptoms_from_natural_text(text: str) -> Dict[str, Any]:
    """
    Extracts symptoms from natural conversational language or comma-separated lists.
    For example: "i am feeling like stomach , ache, then headache , then vomiting , etc"
    Returns extracted symptoms, human-readable labels, and a user confirmation prompt.
    """
    if not text or not text.strip():
        return {
            "extracted_symptoms": [],
            "extracted_keys": [],
            "raw_text": text,
            "confirmation_message": "No symptoms detected in text."
        }

    # Normalize 'word , word' to 'word word' (e.g., 'stomach , ache' -> 'stomach ache')
    normalized = re.sub(r'(\w+)\s*,\s*(\w+)', r'\1 \2', text.lower())

    # Build candidates mapping: phrase -> canonical symptom key
    candidates: Dict[str, str] = {}
    for alias, key in SYMPTOM_ALIASES.items():
        candidates[alias] = key
        candidates[alias.replace('_', ' ')] = key
    for sym_key in SYMPTOMS_DICT.keys():
        candidates[sym_key] = sym_key
        candidates[sym_key.replace('_', ' ')] = sym_key

    # Sort candidate phrases by length descending to match longest phrases first
    sorted_phrases = sorted(candidates.keys(), key=lambda x: len(x), reverse=True)

    found_keys: List[str] = []
    seen = set()

    working_text = normalized
    for phrase in sorted_phrases:
        # Match as whole word / phrase
        pattern = rf'(?:\b|_){re.escape(phrase)}(?:\b|_)'
        if re.search(pattern, working_text):
            k = candidates[phrase]
            if k not in seen:
                seen.add(k)
                found_keys.append(k)
            # Mask out matched segment so it cannot trigger smaller substrings
            working_text = re.sub(pattern, ' ', working_text)

    # Format result with labels
    items = []
    for k in found_keys:
        items.append({
            "key": k,
            "label": get_readable_symptom_name(k)
        })

    labels_str = ", ".join([item["label"] for item in items])
    if items:
        msg = f"We identified {len(items)} symptom(s) from your input: {labels_str}."
    else:
        msg = "We could not find recognized clinical symptoms in your text. You can select symptoms directly from the suggestions."

    return {
        "extracted_symptoms": items,
        "extracted_keys": found_keys,
        "raw_text": text,
        "confirmation_message": msg
    }

def analyze_symptom_list(symptoms: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Analyzes submitted symptoms and categorizes them into:
    1. recognized_keys: Exact keys in SYMPTOMS_DICT ready for the ML model.
    2. mapped_from: Original terms that were successfully mapped via aliases/normalization.
    3. unknown_symptoms: Symptoms not recognized in the dataset vocabulary.

    Note: Automatically splits comma-separated or semicolon-separated strings if passed.
    """
    recognized_keys: List[str] = []
    mapped_from: List[str] = []
    unknown_symptoms: List[str] = []

    # Flatten any comma or semicolon separated entries
    flattened: List[str] = []
    for item in symptoms:
        if not item or not isinstance(item, str):
            continue
        # Split on commas, semicolons, or newlines
        parts = re.split(r'[,;\n]+', item)
        for p in parts:
            p_clean = p.strip()
            if p_clean:
                flattened.append(p_clean)

    seen = set()

    for item in flattened:
        cleaned = clean_symptom_text(item)
        if not cleaned:
            continue

        matched_key = normalize_symptom_to_key(cleaned)
        if matched_key:
            if matched_key not in seen:
                seen.add(matched_key)
                recognized_keys.append(matched_key)
                if matched_key != cleaned:
                    mapped_from.append(f"{cleaned} -> {matched_key.replace('_', ' ')}")
        else:
            # Try natural language extraction on the item if it looks like a phrase
            extracted = extract_symptoms_from_natural_text(cleaned)
            if extracted["extracted_keys"]:
                for k in extracted["extracted_keys"]:
                    if k not in seen:
                        seen.add(k)
                        recognized_keys.append(k)
                        mapped_from.append(f"Extracted from phrase: '{cleaned}' -> {get_readable_symptom_name(k)}")
            else:
                if cleaned not in unknown_symptoms:
                    unknown_symptoms.append(cleaned)

    return recognized_keys, mapped_from, unknown_symptoms

def build_feature_vector(recognized_keys: List[str]) -> np.ndarray:
    """
    Constructs a 132-dimension binary feature vector for the Scikit-learn SVC model.
    Feature order matches the exact training dataset.
    """
    vector = np.zeros(len(SYMPTOMS_DICT), dtype=float)
    for key in recognized_keys:
        if key in SYMPTOMS_DICT:
            vector[SYMPTOMS_DICT[key]] = 1.0
    return vector

def get_readable_symptom_name(key: str) -> str:
    """Converts a dataset symptom key to a human-readable title (e.g. skin_rash -> Skin Rash)."""
    return key.replace('_', ' ').strip().title()

def get_all_supported_symptoms() -> List[Dict[str, str]]:
    """Returns a sorted list of all 132 supported symptoms with key, display label, and index."""
    items = []
    for key, idx in sorted(SYMPTOMS_DICT.items(), key=lambda x: x[0]):
        items.append({
            "key": key,
            "label": get_readable_symptom_name(key),
            "index": idx
        })
    return items
