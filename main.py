import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates

# Load environment variables
load_dotenv()

# --- Path Fix for Templates ---
# Railway ke liye absolute path lazmi hai taake Jinja2 ko templates mil sakein
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # __file_ ki spelling sahi ki
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates") # Agar templates app folder ke andar hain

templates = Jinja2Templates(directory=TEMPLATES_DIR)

app = FastAPI(
    title="EduManage Pro",
    debug=os.getenv("DEBUG", "False") == "True"
)

from app.database import engine, Base, ensure_schema
from app import db_models
from app.routes import router

# Startup event mein schema ensure karna behtar hota hai
@app.on_event("startup")
def startup_event():
    ensure_schema()

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

# 404 Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {"request": request, "status_code": 404, "detail": "Page Not Found!"})
