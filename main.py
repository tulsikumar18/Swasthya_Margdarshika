"""
Personalized Medical Recommendation System
Modern FastAPI Application Entry Point

This file serves as the root entry point for the modernized FastAPI application.
Run using:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Or:
    python main.py
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)