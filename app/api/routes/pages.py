from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.services.prediction_service import prediction_service
from app.schemas.prediction import PredictionRequest
from app.ml.preprocessing import get_all_supported_symptoms

router = APIRouter(include_in_schema=False)

templates_dir = settings.BASE_DIR / "app" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Demo user credentials for authentication
DEMO_USER = {
    'email': 'demo@example.com',
    'password': 'password123',
    'name': 'Demo User'
}

def get_base_context(request: Request) -> Dict[str, Any]:
    """Helper to inject shared session and application context into templates."""
    user_id = request.session.get("user_id")
    return {
        "app_name": settings.APP_NAME,
        "user_name": request.session.get("user_name"),
        "user_id": user_id,
        "is_authenticated": bool(user_id),
    }

def require_auth(request: Request) -> Optional[RedirectResponse]:
    """Returns a redirect to login if user is not authenticated, else None."""
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return None

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Renders the main dashboard and symptom checker."""
    redirect = require_auth(request)
    if redirect:
        return redirect

    all_symptoms = get_all_supported_symptoms()
    ctx = get_base_context(request)
    ctx.update({
        "all_symptoms": all_symptoms,
        "result": None,
        "recent_searches": request.session.get("recent_searches", []),
    })
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)

@router.post("/predict", response_class=HTMLResponse)
async def predict_page_post(request: Request, symptoms: str = Form(...)):
    """Form submission handler for traditional (non-AJAX) browser submissions."""
    redirect = require_auth(request)
    if redirect:
        return redirect

    all_symptoms = get_all_supported_symptoms()
    symptoms_list = [s.strip() for s in symptoms.split(",") if s.strip()]

    result = None
    error_message = None

    if not symptoms_list:
        error_message = "Please enter or select at least one symptom."
    else:
        try:
            req = PredictionRequest(symptoms=symptoms_list, allow_ai_fallback=True)
            result = prediction_service.predict_disease(req)
            # Store in session search history
            searches = request.session.get("recent_searches", [])
            if symptoms not in searches:
                searches.insert(0, symptoms)
                request.session["recent_searches"] = searches[:5]
        except Exception as e:
            error_message = f"Error processing symptoms: {str(e)}"

    ctx = get_base_context(request)
    ctx.update({
        "all_symptoms": all_symptoms,
        "result": result,
        "error_message": error_message,
        "submitted_symptoms": symptoms,
    })
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)

# Authentication Routes: Login, Register, Logout, Profile
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, next: Optional[str] = None):
    """Renders the login form."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    ctx = get_base_context(request)
    ctx.update({
        "error": None,
        "message": None,
        "next_url": next or "/",
    })
    return templates.TemplateResponse(request=request, name="login.html", context=ctx)

@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_url: Optional[str] = Form(default="/")
):
    """Processes user login credentials."""
    email_clean = email.strip()
    target_url = next_url if next_url and next_url.startswith("/") else "/"

    # Demo user check or standard valid credential demo login
    if email_clean == DEMO_USER["email"] and password == DEMO_USER["password"]:
        request.session["user_id"] = email_clean
        request.session["user_name"] = DEMO_USER["name"]
        return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    elif "@" in email_clean and len(password) >= 6:
        # Accept valid email format and password >= 6 chars for testing/demo
        name = email_clean.split("@")[0].replace(".", " ").title()
        request.session["user_id"] = email_clean
        request.session["user_name"] = name
        return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    else:
        ctx = get_base_context(request)
        ctx.update({
            "error": "Invalid email or password. Password must be at least 6 characters.",
            "next_url": target_url,
        })
        return templates.TemplateResponse(request=request, name="login.html", context=ctx, status_code=400)

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request, next: Optional[str] = None):
    """Renders user registration form."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    ctx = get_base_context(request)
    ctx.update({
        "error": None,
        "next_url": next or "/",
    })
    return templates.TemplateResponse(request=request, name="register.html", context=ctx)

@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    next_url: Optional[str] = Form(default="/")
):
    """Processes new user account creation."""
    target_url = next_url if next_url and next_url.startswith("/") else "/"

    if not all([firstName.strip(), lastName.strip(), email.strip(), password]):
        error = "All fields are required."
    elif password != confirmPassword:
        error = "Passwords do not match."
    elif len(password) < 6:
        error = "Password must be at least 6 characters long."
    elif "@" not in email:
        error = "Please provide a valid email address."
    else:
        # Register user and log them in
        request.session["user_id"] = email.strip()
        request.session["user_name"] = f"{firstName.strip()} {lastName.strip()}"
        return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)

    ctx = get_base_context(request)
    ctx.update({
        "error": error,
        "next_url": target_url,
    })
    return templates.TemplateResponse(request=request, name="register.html", context=ctx, status_code=400)

@router.get("/logout")
async def logout(request: Request):
    """Clears user session and redirects to login page."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Renders user profile and search activity."""
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login?next=/profile", status_code=status.HTTP_303_SEE_OTHER)

    ctx = get_base_context(request)
    user_name = ctx["user_name"] or "User"
    parts = user_name.split()
    first_name = parts[0] if parts else user_name
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    ctx.update({
        "first_name": first_name,
        "last_name": last_name,
        "email": ctx["user_id"],
        "join_date": "October 2026",
        "recent_searches": request.session.get("recent_searches", []),
    })
    return templates.TemplateResponse(request=request, name="profile.html", context=ctx)

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Renders the about page."""
    redirect = require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context=get_base_context(request)
    )

@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Renders the contact page."""
    redirect = require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context=get_base_context(request)
    )

@router.get("/developer", response_class=HTMLResponse)
async def developer_page(request: Request):
    """Renders the developer page."""
    redirect = require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="developer.html",
        context=get_base_context(request)
    )

@router.get("/blog", response_class=HTMLResponse)
async def blog_page(request: Request):
    """Renders the blog page."""
    redirect = require_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="blog.html",
        context=get_base_context(request)
    )

