import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

# 1. Load environment variables
load_dotenv()

# 2. Path Setup (Vercel/Railway ke liye absolute path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates") 

templates = Jinja2Templates(directory=TEMPLATES_DIR)

from app.database import engine, Base, ensure_schema
from app import db_models
from app.routes import router

# 3. FastAPI Instance Setup
app = FastAPI(
    title="EduManage Pro",
    debug=os.getenv("DEBUG", "False") == "True"
)

# 4. Database Setup (Modern Way - No more @app.on_event)
# Startup par tables banane ke liye direct call karein
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    print("✅ Database tables created successfully.")
except Exception as e:
    print(f"❌ Database error: {e}")

# 5. 🛡️ Security Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 6. Routes ko Include karna
app.include_router(router)

# 7. Favicon Fix (Vercel 500 error se bachne ke liye)
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(BASE_DIR, "static", "favicon.ico"))

# 8. 404 Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request, 
        name="error.html", 
        context={
            "request": request, 
            "status_code": 404, 
            "detail": "Page Not Found!"
        }
    )

