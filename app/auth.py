import os
import json
import secrets
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# ─── Password Hashing ───────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── User Manager ───────────────────────────────────────────────────────────
from .database import SessionLocal
from .db_models import User

class UserManager:
    def __init__(self):
        self._seed_admin()

    def _seed_admin(self):
        """Create a default admin account if no users exist."""
        db = SessionLocal()
        try:
            if db.query(User).count() == 0:
                admin = User(
                    username="admin",
                    password=hash_password("admin@f10"),
                    role="admin"
                )
                db.add(admin)
                db.commit()
        finally:
            db.close()

    def find_by_username(self, username: str):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            db.close()

    def register(self, username: str, password: str, role: str = "user") -> dict | None:
        return self.register_linked(username=username, password=password, role=role, student_id=None)

    def register_linked(self, username: str, password: str, role: str = "user", student_id: int | None = None) -> dict | None:
        db = SessionLocal()
        try:
            if self.find_by_username(username):
                return None
            new_user = User(
                username=username,
                password=hash_password(password),
                role=role,
                student_id=student_id,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "student_id": new_user.student_id,
                "course_id": new_user.course_id,
            }
        finally:
            db.close()

    def authenticate(self, username: str, password: str) -> dict | None:
        user = self.find_by_username(username)
        if user and verify_password(password, user.password):
            return {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "student_id": user.student_id,
                "course_id": user.course_id,
            }
        return None


# ─── Session Helpers ─────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SESSION_SECRET", "fallback_secret_key_change_me_in_production")
SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_SECONDS", str(60 * 60 * 24)))
ANON_CSRF_COOKIE_NAME = "csrf_anon"

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="edumanage-session-v1")

def _new_csrf_token() -> str:
    return secrets.token_urlsafe(32)

def get_current_user(request) -> dict | None:
    """
    Reads the signed session cookie and returns user dict, or None.
    Cookie stores (signed): {id, username, role, student_id, csrf}
    """
    session = request.cookies.get(SESSION_COOKIE_NAME)
    if not session:
        return None
    try:
        data = _serializer.loads(session, max_age=SESSION_MAX_AGE_SECONDS)
        if not isinstance(data, dict):
            return None
        # Ensure csrf exists
        if not data.get("csrf"):
            data["csrf"] = _new_csrf_token()
        return data
    except (BadSignature, SignatureExpired, Exception):
        return None

def get_csrf_token(request) -> str:
    user = get_current_user(request)
    if user and user.get("csrf"):
        return user["csrf"]
    existing = request.cookies.get(ANON_CSRF_COOKIE_NAME)
    return existing or _new_csrf_token()

def validate_csrf(request, form) -> bool:
    """
    Validate CSRF token from submitted form against session.
    """
    user = get_current_user(request)
    expected = (user.get("csrf") if user else None) or request.cookies.get(ANON_CSRF_COOKIE_NAME)
    token = None
    try:
        token = form.get("csrf_token")
    except Exception:
        token = None
    return bool(expected and token and secrets.compare_digest(str(expected), str(token)))

def create_session_cookie(response, user: dict):
    """Write the signed session cookie onto a response."""
    payload = {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "student_id": user.get("student_id"),
        "course_id": user.get("course_id"),
        "csrf": user.get("csrf") or _new_csrf_token(),
    }
    secure_cookie = os.getenv("COOKIE_SECURE", "False") == "True"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=_serializer.dumps(payload),
        httponly=True,
        secure=secure_cookie,
        max_age=SESSION_MAX_AGE_SECONDS,
        samesite="lax",
        path="/",
    )

def clear_session_cookie(response):
    """Remove the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
