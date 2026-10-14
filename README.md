# Personalized Medical Recommendation System with Machine Learning

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-SVC-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

A state-of-the-art clinical intelligence platform modernizing personalized healthcare recommendations. The platform uses a high-precision **Support Vector Classifier (SVC)** trained on physiological symptom patterns to evaluate conditions, supplemented by **Google Gemini AI fallback** for handling unsupported or colloquial symptoms, and structured tabular databases for preventative precautions, dietary guidance, medications, and physical activity.

---

## Architecture Overview

```text
personalized-medical-recommendation-system/
├── app/
│   ├── main.py                     # FastAPI application factory, lifespan startup, CORS & routes
│   ├── core/
│   │   ├── config.py               # Centralized settings via pydantic-settings (.env)
│   ├── api/
│   │   └── routes/
│   │       ├── health.py           # GET /api/health (System status & metadata)
│   │       ├── symptoms.py         # GET /api/symptoms (List of 132 supported symptoms & search)
│   │       ├── predictions.py      # POST /api/predict (Pydantic-validated prediction pipeline)
│   │       └── pages.py            # HTML dashboard & pages (Home, About, Contact, Developer, Blog)
│   ├── schemas/
│   │   ├── symptom.py              # Symptom list & search schemas
│   │   └── prediction.py           # Unified request/response schemas (ML, AI, Clarification)
│   ├── services/
│   │   ├── prediction_service.py   # SVC inference engine with feature preservation
│   │   ├── recommendation_service.py# CSV retrieval with robust whitespace & typo tolerance
│   │   └── ai_fallback_service.py  # Google Gemini AI fallback with strict timeout & validation
│   ├── ml/
│   │   ├── model_loader.py         # Singleton model & dataset loader during startup
│   │   └── preprocessing.py        # Vectorization, normalization, & symptom mapping
│   ├── templates/
│   │   ├── base.html               # Shared layout, navbar, emergency banner, footer
│   │   ├── index.html              # Modern dashboard: Hero, interactive symptom picker, cards
│   │   ├── about.html              # About project & safety
│   │   ├── contact.html            # Contact & feedback
│   │   ├── developer.html          # Developer portfolio
│   │   └── blog.html               # Healthcare & ML articles
│   └── static/
│       ├── css/
│       │   └── style.css           # Premium custom styles (glassmorphism, healthcare design system)
│       ├── js/
│       │   └── app.js              # Fetch-based async symptom search, tags, submission & TTS
│       └── images/
├── models/
│   └── svc.pkl                     # Active model file (132 features -> 41 conditions)
├── datasets/                       # 7 tabular datasets + Training.csv
├── tests/                          # 100% automated pytest test suite
├── .env.example                    # Clean environment configuration template
├── .gitignore                      # Standard Python, IDE, OS, and env ignores
├── requirements.txt                # Minimized modern dependencies (FastAPI, uvicorn, scikit-learn)
├── README.md                       # Comprehensive documentation
├── pytest.ini                      # Test runner configuration
└── run.py                          # Convenient root launcher script
```

---

## Key Features

1. **FastAPI Modernization:**
   - Asynchronous ASGI architecture powered by Uvicorn.
   - Pydantic models for strict type validation and serialized responses.
   - Interactive Swagger UI documentation at `/docs` and ReDoc at `/redoc`.
   - Health-check endpoint at `GET /api/health`.

2. **Machine Learning Preservation:**
   - Retained the trained Scikit-learn Support Vector Classifier (`SVC`) without destructive retraining.
   - Exact 132-dimension binary feature mapping preserving column alignment with `datasets/Training.csv`.
   - Explicit handling of model capabilities (confidence explicitly represented as `None` since the deterministic SVC model operates without calibrated probability scores).

3. **Intelligent AI Fallback (Google Gemini):**
   - Automatically detects when symptoms fall outside the 132-item dataset vocabulary.
   - Normalizes whitespace, case, and aliases (e.g., `joint pain` -> `joint_pain`, `fever` -> `high_fever`).
   - If completely unknown, calls Google Gemini API (when configured) with strict 8-second bounded timeout, sanitization, and structured Pydantic response validation.
   - If AI is unavailable or unconfigured, gracefully falls back to clear rule-based health guidance without crashing or fabricating clinical diagnoses.

4. **Preserved Informational Recommendations:**
   - Top-5 medicines preserved from `datasets/medications.csv` and clearly labeled as educational information.
   - Preventative precautions retrieved from `datasets/precautions_df.csv`.
   - Dietary guidelines retrieved from `datasets/diets.csv`.
   - Exercise recommendations retrieved from `datasets/workout_df.csv`.

5. **Security & Privacy Safeguards:**
   - Centralized environment configuration via `pydantic-settings`.
   - All credentials removed from source code; stored exclusively in `.env`.
   - Automated tests confirm credentials and API keys are never leaked in API responses or templates.
   - Red banner emergency warnings advising users with critical symptoms to seek urgent emergency care immediately.

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed on your system.

### 2. Create and Activate Virtual Environment
```bash
# Create a virtual environment
python3 -m venv .venv

# Activate on macOS / Linux:
source .venv/bin/activate

# Activate on Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and customize your settings:
```bash
cp .env.example .env
```

Edit `.env` to configure your settings:
```dotenv
APP_NAME="Personalized Medical Recommendation System"
APP_ENV=development
HOST=127.0.0.1
PORT=8000
DEBUG=false
SECRET_KEY=your_cryptographically_secure_random_key_here

# Optional: Google Gemini API Key for intelligent fallback
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: The system works completely out-of-the-box even without a Gemini API key using rule-based local fallbacks!)*

### 5. Run the Application
You can start the application using either the root `run.py` script or directly with Uvicorn:

**Option A (Recommended):**
```bash
python run.py
```

**Option B (Direct Uvicorn):**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## API Endpoints & Usage

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Responsive healthcare landing page and interactive symptom checker |
| `GET` | `/docs` | Interactive Swagger UI API documentation |
| `GET` | `/redoc` | ReDoc OpenAPI documentation |
| `GET` | `/api/health` | System health check, model readiness, and dataset metrics |
| `GET` | `/api/symptoms` | Complete list of all 132 supported symptoms with display labels |
| `GET` | `/api/symptoms/search?q={query}` | Autocomplete search for symptoms |
| `POST` | `/api/predict` | JSON prediction endpoint (accepts `{"symptoms": [...]}`) |
| `POST` | `/predict` | Traditional form submission handler with HTML response |

### Example API Request:
```bash
curl -X POST "http://127.0.0.1:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"],
       "allow_ai_fallback": true
     }'
```

### Example API Response:
```json
{
  "success": true,
  "mode": "ml_prediction",
  "predicted_disease": "Fungal infection",
  "confidence": null,
  "description": "Fungal infection is a common skin condition caused by fungi...",
  "medications": [
    "Antifungal Cream",
    "Fluconazole",
    "Terbinafine",
    "Clotrimazole",
    "Ketoconazole"
  ],
  "precautions": [
    "Bath twice",
    "Use dettol or antiseptic in bath water",
    "Keep infected area clean and dry",
    "Do not share towels or clothing"
  ],
  "diet_recommendations": [
    "Antifungal Diet",
    "Probiotics",
    "Garlic",
    "Coconut oil",
    "Turmeric"
  ],
  "workout_recommendations": [
    "Avoid sugary foods",
    "Consume probiotics",
    "Increase intake of garlic",
    "Follow a healthy lifestyle"
  ],
  "recognized_symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"],
  "unrecognized_symptoms": [],
  "mapped_symptoms": [],
  "message": "Based on your symptoms (Itching, Skin Rash, Nodal Skin Eruptions), our machine learning model identified Fungal infection.",
  "disclaimer": "Disclaimer: This application provides informational assistance using machine learning and AI. It is NOT a substitute for professional medical advice..."
}
```

---

## Running the Automated Test Suite

The project includes an end-to-end automated test suite built with `pytest` and FastAPI's `TestClient`, covering 100% of functional requirements:
- Application startup and graceful shutdown
- System health checks
- Template rendering and navigation
- Valid ML predictions and recommendation dataset lookups
- Duplicate symptom handling and alias normalization
- Empty and invalid symptom validation
- AI fallback handling with simulated API responses
- Graceful offline fallback when no AI key is configured
- Provider timeouts and malformed JSON response handling
- Verification that sensitive credentials are never leaked

Run the tests with:
```bash
pytest -v
```

---

## Medical Disclaimer

> **IMPORTANT:** This software is an experimental, educational informatics platform designed to demonstrate machine learning applications in medicine. It is **not clinically certified** and must **not** be used for clinical diagnosis, treatment decisions, or emergency care. If you are experiencing serious or worsening symptoms, consult a qualified physician or contact local emergency medical services immediately.

---

## Developer Attribution & Copyright

&copy; 2026 Personalized Medical Recommendation System. All rights reserved. Developed by tulsikumr18.
