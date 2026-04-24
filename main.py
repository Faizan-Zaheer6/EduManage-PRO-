import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates # Upar hi import kar lein

# Load environment variables
load_dotenv()

# --- Path Fix for Vercel ---
# Is se templates folder ka sahi path milega chahe code kahin bhi ho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Agar templates folder app folder se bahar hai (root par)
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "templates") 

from app.database import engine, Base
from app import db_models

# Create tables on startup
Base.metadata.create_all(bind=engine)
from app.database import ensure_schema
ensure_schema()

from app.routes import router

app = FastAPI(
    title="EduManage Pro",
    debug=os.getenv("DEBUG", "False") == "True"
)

# 🛡️ Security Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Routes ko include karna
app.include_router(router)

# Error handler fixed for Vercel
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    return templates.TemplateResponse("error.html", {"request": request, "status_code": 404, "detail": "Page Not Found!"})