import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment variables
load_dotenv()

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

# 🛡️ Security Middleware: Basic Header Protection
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# --- Routes ko "Include" karna ---
app.include_router(router)

# Error handler
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("error.html", {"request": request, "status_code": 404, "detail": "Page Not Found!"})