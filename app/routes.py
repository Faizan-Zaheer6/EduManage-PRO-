import csv
import io
import os 
from datetime import date as date_type

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fpdf import FPDF

from .course_manager import StudentManager, CourseManager
from .attendance_manager import AttendanceManager
import time
from .database import SessionLocal
from .db_models import Student, User
from .auth import (
    UserManager,
    get_current_user,
    create_session_cookie,
    clear_session_cookie,
    get_csrf_token,
    validate_csrf,
    ANON_CSRF_COOKIE_NAME,
)
from .models import grade_from_marks

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_path = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_path)

student_mgr    = StudentManager()
course_mgr     = CourseManager()
user_mgr       = UserManager()
attendance_mgr = AttendanceManager()

# very small in-memory limiter (works per-process)
_login_attempts: dict[str, list[float]] = {}
_LOGIN_WINDOW_SECONDS = 60.0
_LOGIN_MAX_ATTEMPTS = 8


# ── Helpers ──────────────────────────────────────────────────────────────────

def redirect_login():
    return RedirectResponse(url="/login", status_code=302)

def redirect_home():
    return RedirectResponse(url="/home", status_code=302)

def flash_redirect(url: str, msg: str, msg_type: str = "success"):
    sep = "&" if "?" in url else "?"
    return RedirectResponse(url=f"{url}{sep}msg={msg}&type={msg_type}", status_code=302)

def render(request: Request, template_name: str, context: dict, status_code: int = 200):
    context = dict(context)
    context.setdefault("request", request)
    context.setdefault("csrf_token", get_csrf_token(request))
    resp = templates.TemplateResponse(template_name, context, status_code=status_code)
    # Ensure anonymous visitors can pass CSRF on login/signup
    if not get_current_user(request):
        token = context["csrf_token"]
        resp.set_cookie(
            key=ANON_CSRF_COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return resp

def require_csrf_or_403(request: Request, form):
    if not validate_csrf(request, form):
        return render(request, "error.html", {"status_code": 403, "detail": "Invalid CSRF token."}, status_code=403)
    return None

def linked_student_for_user(user: dict):
    if not user or user.get("role") != "user":
        return None
    sid = user.get("student_id")
    if not sid:
        return None
    return student_mgr.get_by_id(int(sid))

def course_label(student: dict) -> str:
    return (student.get("course") or student.get("course_name") or "").strip()

def _pdf_bytes(pdf: FPDF) -> bytes:
    try:
        out = pdf.output(dest="S")
    except TypeError:
        out = pdf.output()
    return out if isinstance(out, (bytes, bytearray)) else str(out).encode("latin-1", errors="ignore")

def _latin1(text) -> str:
    return (str(text) if text is not None else "").encode("latin-1", errors="replace").decode("latin-1")

def build_transcript_pdf(student: dict, att: dict, generated_by: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 10, _latin1("EduManage Pro - Transcript"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, _latin1(f"Generated: {date_type.today().strftime('%B %d, %Y')}  |  By: {generated_by}"), ln=True, align="C")
    pdf.ln(6)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _latin1("Student Info"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _latin1(f"Name: {student.get('name','')}"), ln=True)
    pdf.cell(0, 6, _latin1(f"Roll No: {student.get('roll_no','')}"), ln=True)
    pdf.cell(0, 6, _latin1(f"Course: {student.get('course_name') or student.get('course') or ''}"), ln=True)
    pdf.cell(0, 6, _latin1(f"Email: {student.get('email','')}"), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _latin1("Attendance Summary"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _latin1(f"Present: {att.get('present',0)}  |  Absent: {att.get('absent',0)}  |  Attendance %: {att.get('pct',0)}%"), ln=True)
    pdf.ln(4)

    results = student.get("results", []) or []
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _latin1("Academic Results"), ln=True)

    cols = [("Subject", 55), ("Marks", 25), ("Total", 18), ("Grade", 18), ("GPA", 18)]
    pdf.set_fill_color(30, 27, 75)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for title, w in cols:
        pdf.cell(w, 7, _latin1(title), fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    fill = False
    for r in results:
        pdf.set_fill_color(245, 245, 255) if fill else pdf.set_fill_color(255, 255, 255)
        vals = [
            r.get("subject", "-"),
            str(r.get("marks", "-")),
            str(r.get("total", "-")),
            str(r.get("grade", "-")),
            str(r.get("gpa", "-")),
        ]
        for v, (_, w) in zip(vals, cols):
            pdf.cell(w, 7, _latin1(v)[:28], fill=True)
        pdf.ln()
        fill = not fill

    # CGPA simple (avg of GPA points)
    gpas = [float(r.get("gpa", 0) or 0) for r in results if str(r.get("gpa", "")).strip() != ""]
    cgpa = round(sum(gpas) / len(gpas), 2) if gpas else 0.0
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, _latin1(f"CGPA: {cgpa}"), ln=True)

    return _pdf_bytes(pdf)


# ── Public Landing Page ───────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    if get_current_user(request):
        return redirect_home()
    return render(request, "index.html", {})


# ── Auth Routes ───────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_current_user(request):
        return redirect_home()
    return render(request, "login.html", {"error": None})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err

    ip = (request.client.host if request.client else "unknown")
    now = time.time()
    bucket = [t for t in _login_attempts.get(ip, []) if (now - t) <= _LOGIN_WINDOW_SECONDS]
    if len(bucket) >= _LOGIN_MAX_ATTEMPTS:
        return render(request, "login.html", {"error": "Too many login attempts. Please wait 1 minute."}, status_code=429)
    bucket.append(now)
    _login_attempts[ip] = bucket

    user = user_mgr.authenticate(username, password)
    if not user:
        return render(request, "login.html", {"error": "Invalid username or password. Please try again."})
    response = RedirectResponse(url="/home", status_code=302)
    create_session_cookie(response, user)
    return response


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    if get_current_user(request):
        return redirect_home()
    # offer roll numbers for linking (optional)
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        linked_ids = {u.student_id for u in db.query(User).filter(User.student_id.isnot(None)).all()}
        choices = [{"id": s.id, "roll_no": s.roll_no, "name": s.name} for s in students if s.id not in linked_ids]
    finally:
        db.close()
    return render(request, "signup.html", {"error": None, "student_choices": choices})


@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user")
):
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err

    if len(username) < 3:
        return render(request, "signup.html", {"error": "Username must be at least 3 characters."})
    if len(password) < 6:
        return render(request, "signup.html", {"error": "Password must be at least 6 characters."})
    if role not in ("user", "admin"):
        role = "user"
    student_id = None
    if role == "user":
        student_id_raw = form.get("student_id")
        if student_id_raw:
            try:
                student_id = int(student_id_raw)
            except ValueError:
                student_id = None
    new_user = user_mgr.register_linked(username, password, role, student_id=student_id)
    if not new_user:
        return render(request, "signup.html", {"error": f"Username '{username}' is already taken. Please choose another."})
    response = RedirectResponse(url="/home", status_code=302)
    create_session_cookie(response, new_user)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(response)
    return response


# ── Post-Login Home Dashboard ─────────────────────────────────────────────────

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, msg: str = None, type: str = "success"):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    visible_students = student_mgr.students
    linked_student = None
    if user.get("role") == "user":
        linked_student = linked_student_for_user(user)
        visible_students = [linked_student] if linked_student else []

    student_ids = [s["id"] for s in visible_students]
    today_att   = attendance_mgr.today_summary(student_ids)
    # Per-course student count for charts
    course_counts = {}
    for s in visible_students:
        course = course_label(s)
        if not course:
            course = "Unassigned"
        course_counts[course] = course_counts.get(course, 0) + 1
    
    return templates.TemplateResponse("home.html", {
        "request":       request,
        "current_user":  user,
        "total_students": len(visible_students),
        "total_courses":  len(course_mgr.courses),
        "today_att":      today_att,
        "course_counts":  course_counts,
        "linked_student": linked_student,
        "msg":            msg,
        "msg_type":       type,
        "csrf_token":     get_csrf_token(request),
    })


# ── Enroll (login required) ───────────────────────────────────────────────────

@router.get("/enroll-page", response_class=HTMLResponse)
async def enroll_page(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    return render(request, "enroll_student.html", {"courses": course_mgr.courses, "current_user": user})


@router.post("/enroll")
async def enroll(
    request: Request,
    name:    str = Form(...),
    email:   str = Form(...),
    course:  str = Form(...),
    roll_no: str = Form(...),
):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.enroll_student(name, email, course, roll_no)
    return flash_redirect("/view-records", f"{name} enrolled successfully!")


# ── Records (login required) ──────────────────────────────────────────────────

@router.get("/view-records", response_class=HTMLResponse)
async def view_records(
    request: Request,
    search:  str = "",
    course:  str = "",
    roll_no: str = "",
    page:    int = Query(1, ge=1),
    msg:     str = None,
    type:    str = "success",
):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if user.get("role") == "user":
        linked = linked_student_for_user(user)
        filtered = [linked] if linked else []
        # Ignore filters for normal users (privacy)
        search = ""
        course = ""
        roll_no = ""
    else:
        filtered = student_mgr.search(name=search, course=course, roll_no=roll_no)
    page_items, current_page, total_pages = student_mgr.paginate(filtered, page)
    return render(request, "records.html", {
        "students":     page_items,
        "current_user": user,
        "courses":      course_mgr.courses,
        "search":       search,
        "filter_course": course,
        "filter_roll":   roll_no,
        "current_page":  current_page,
        "total_pages":   total_pages,
        "total_count":   len(filtered),
        "msg":           msg,
        "msg_type":      type,
    })


# ── Edit Student (admin) ──────────────────────────────────────────────────────

@router.get("/student/{student_id}/edit", response_class=HTMLResponse)
async def edit_student_page(request: Request, student_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    student = student_mgr.get_by_id(student_id)
    if not student:
        return render(request, "error.html", {"status_code": 404, "detail": "Student not found."}, status_code=404)
    return render(request, "edit_student.html", {
        "student":      student,
        "courses":      course_mgr.courses,
        "current_user": user,
    })


@router.post("/student/{student_id}/edit")
async def edit_student(
    request:    Request,
    student_id: int,
    name:       str = Form(...),
    email:      str = Form(...),
    course:     str = Form(...),
    roll_no:    str = Form(...),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.update_student(student_id, name, email, course, roll_no)
    return flash_redirect("/view-records", f"Student updated successfully!")


# ── Student Profile ───────────────────────────────────────────────────────────

@router.get("/student/{student_id}", response_class=HTMLResponse)
async def student_profile(request: Request, student_id: int):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if user.get("role") == "user":
        linked = linked_student_for_user(user)
        if not linked or int(linked.get("id")) != int(student_id):
            return render(request, "error.html", {"status_code": 403, "detail": "Access denied. You can only view your own profile."}, status_code=403)
    student = student_mgr.get_by_id(student_id)
    if not student:
        return render(request, "error.html", {"status_code": 404, "detail": "Student not found."}, status_code=404)
    att_summary = attendance_mgr.get_student_summary(student_id)
    results = student.get("results", [])
    avg_gpa = round(sum(r["gpa"] for r in results) / len(results), 2) if results else 0
    return render(request, "student_profile.html", {
        "student":      student,
        "att":          att_summary,
        "avg_gpa":      avg_gpa,
        "current_user": user,
    })

@router.get("/my/transcript/pdf")
async def my_transcript_pdf(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if user.get("role") != "user":
        return render(request, "error.html", {"status_code": 403, "detail": "Only users can access this transcript."}, status_code=403)
    student = linked_student_for_user(user)
    if not student:
        return render(request, "error.html", {"status_code": 404, "detail": "No linked student record."}, status_code=404)
    att = attendance_mgr.get_student_summary(int(student["id"]))
    pdf_bytes = build_transcript_pdf(student, att, generated_by=user.get("username","user"))
    filename = f"transcript_{student.get('roll_no','student')}.pdf"
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

@router.get("/student/{student_id}/transcript/pdf")
async def student_transcript_pdf(request: Request, student_id: int):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if user.get("role") not in ("admin", "teacher"):
        return render(request, "error.html", {"status_code": 403, "detail": "Access denied."}, status_code=403)
    student = student_mgr.get_by_id(student_id)
    if not student:
        return render(request, "error.html", {"status_code": 404, "detail": "Student not found."}, status_code=404)
    att = attendance_mgr.get_student_summary(int(student_id))
    pdf_bytes = build_transcript_pdf(student, att, generated_by=user.get("username","staff"))
    filename = f"transcript_{student.get('roll_no','student')}.pdf"
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


# ── Marks Entry (admin) ───────────────────────────────────────────────────────

@router.get("/student/{student_id}/marks", response_class=HTMLResponse)
async def marks_page(request: Request, student_id: int, msg: str = None, type: str = "success"):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    student = student_mgr.get_by_id(student_id)
    if not student:
        return render(request, "error.html", {"status_code": 404, "detail": "Student not found."}, status_code=404)
    return render(request, "marks_entry.html", {
        "student":      student,
        "current_user": user,
        "msg":          msg,
        "msg_type":     type,
    })


@router.post("/student/{student_id}/marks")
async def add_marks(
    request:    Request,
    student_id: int,
    subject:    str   = Form(...),
    marks:      float = Form(...),
    total:      float = Form(100),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.add_result(student_id, subject, marks, total)
    return flash_redirect(f"/student/{student_id}/marks", f"Result for '{subject}' saved!")


@router.post("/student/{student_id}/marks/delete")
async def delete_marks(request: Request, student_id: int, subject: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.delete_result(student_id, subject)
    return flash_redirect(f"/student/{student_id}/marks", f"'{subject}' result deleted.")

@router.get("/cgpa", response_class=HTMLResponse)
async def cgpa_page(request: Request, msg: str = None, type: str = "success"):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    linked = linked_student_for_user(user) if user.get("role") == "user" else None
    return render(request, "cgpa.html", {
        "current_user": user,
        "linked_student": linked,
        "computed": None,
        "msg": msg,
        "msg_type": type,
    })

@router.post("/cgpa", response_class=HTMLResponse)
async def cgpa_calculate(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_login()

    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    subjects = form.getlist("subject")
    marks_list = form.getlist("marks")
    totals_list = form.getlist("total")
    credits_list = form.getlist("credits")

    rows = []
    total_quality_points = 0.0
    total_credits = 0.0

    for subj, m, t, c in zip(subjects, marks_list, totals_list, credits_list):
        subj = (subj or "").strip()
        if not subj:
            continue
        try:
            marks = float(m)
            total = float(t) if str(t).strip() else 100.0
            credits = float(c) if str(c).strip() else 3.0
        except ValueError:
            continue
        g = grade_from_marks(marks, total)
        qp = g["gpa"] * credits
        total_quality_points += qp
        total_credits += credits
        rows.append({
            "subject": subj,
            "marks": marks,
            "total": total,
            "credits": credits,
            "grade": g["grade"],
            "gpa": g["gpa"],
            "qp": round(qp, 2),
        })

    cgpa = round((total_quality_points / total_credits), 2) if total_credits > 0 else 0.0

    linked = linked_student_for_user(user) if user.get("role") == "user" else None
    return render(request, "cgpa.html", {
        "current_user": user,
        "linked_student": linked,
        "computed": {
            "rows": rows,
            "total_credits": round(total_credits, 2),
            "total_qp": round(total_quality_points, 2),
            "cgpa": cgpa,
        },
        "msg": None,
        "msg_type": "success",
    })


# Legacy add-result route (from old records.html inline form)
@router.post("/add-result/{student_id}")
async def add_result_legacy(
    request:    Request,
    student_id: int,
    subject:    str   = Form(...),
    marks:      float = Form(...),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.add_result(student_id, subject, marks, 100)
    return flash_redirect("/view-records", f"Result added!")


# ── Attendance ────────────────────────────────────────────────────────────────

@router.get("/attendance", response_class=HTMLResponse)
async def attendance_page(
    request:  Request,
    date_str: str = Query(None, alias="date"),
    msg:      str = None,
    type:     str = "success",
):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if not date_str:
        date_str = str(date_type.today())
    day_records = attendance_mgr.get_for_date(date_str)
    visible_students = student_mgr.students
    if user.get("role") == "user":
        linked = linked_student_for_user(user)
        visible_students = [linked] if linked else []
    student_ids = [s["id"] for s in visible_students]
    today_summary = attendance_mgr.today_summary(student_ids)
    all_dates = attendance_mgr.all_dates()
    return render(request, "attendance.html", {
        "students":     visible_students,
        "day_records":  day_records,
        "date_str":     date_str,
        "today":        str(date_type.today()),
        "today_summary": today_summary,
        "all_dates":    all_dates[:30],
        "current_user": user,
        "msg":          msg,
        "msg_type":     type,
    })


@router.post("/attendance/mark")
async def mark_attendance(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    date_str = form.get("date_str", str(date_type.today()))
    records = {}
    for s in student_mgr.students:
        sid = str(s["id"])
        records[sid] = form.get(f"status_{sid}", "absent")
    attendance_mgr.mark_bulk(date_str, records)
    return flash_redirect(f"/attendance?date={date_str}", "Attendance saved!")


# ── Admin Panel ───────────────────────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, msg: str = None, type: str = "success"):
    user = get_current_user(request)
    if not user:
        return redirect_login()
    if user["role"] != "admin":
        return render(request, "error.html", {"status_code": 403, "detail": "Access Denied — Admins only! 🛡️"}, status_code=403)
    # Per-course counts for chart
    course_counts = {}
    for s in student_mgr.students:
        course = (s.get("course") or s.get("course_name") or "").strip()
        if not course:
            course = "Unassigned"
        course_counts[course] = course_counts.get(course, 0) + 1

    student_ids   = [s["id"] for s in student_mgr.students]
    today_att     = attendance_mgr.today_summary(student_ids)

    return render(request, "admin.html", {
        "total_students": len(student_mgr.students),
        "total_courses":  len(course_mgr.courses),
        "recent_students": student_mgr.students[-5:],
        "courses":        course_mgr.courses,
        "current_user":   user,
        "course_counts":  course_counts,
        "today_att":      today_att,
        "msg":            msg,
        "msg_type":       type,
    })


@router.post("/add-course")
async def add_course(request: Request, title: str = Form(...), teacher: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    course_mgr.add_course(title, teacher)
    return flash_redirect("/admin", f"Course '{title}' added!")


@router.post("/course/{course_id}/delete")
async def delete_course(request: Request, course_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    course = course_mgr.get_by_id(course_id)
    name = course["title"] if course else "Course"
    course_mgr.remove_course(course_id)
    return flash_redirect("/admin", f"Course '{name}' deleted.")


@router.post("/remove/{student_id}")
async def remove_student(request: Request, student_id: int):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    form = await request.form()
    csrf_err = require_csrf_or_403(request, form)
    if csrf_err:
        return csrf_err
    student_mgr.remove_student(student_id)
    return flash_redirect("/view-records", "Student record removed.")


# ── Export ────────────────────────────────────────────────────────────────────

@router.get("/export/csv")
async def export_csv(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()
    rows = student_mgr.get_all_flat()
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_report.csv"},
    )


@router.get("/export/pdf")
async def export_pdf(request: Request):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return redirect_login()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def _latin1(text) -> str:
        return (str(text) if text is not None else "").encode("latin-1", errors="replace").decode("latin-1")

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 12, _latin1("EduManage Pro - Student Report"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0,
        8,
        _latin1(f"Generated: {date_type.today().strftime('%B %d, %Y')}  |  Total Students: {len(student_mgr.students)}"),
        ln=True,
        align="C",
    )
    pdf.ln(4)

    # Table header
    pdf.set_fill_color(30, 27, 75)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    cols = [("ID", 12), ("Name", 38), ("Roll No", 22), ("Course", 32),
            ("Subject", 28), ("Marks", 18), ("Grade", 16), ("GPA", 14)]
    for col, w in cols:
        pdf.cell(w, 8, col, border=0, fill=True)
    pdf.ln()

    # Rows
    pdf.set_font("Helvetica", "", 8)
    fill = False
    for row in student_mgr.get_all_flat():
        pdf.set_text_color(30, 30, 30)
        pdf.set_fill_color(240, 240, 255) if fill else pdf.set_fill_color(255, 255, 255)
        values = [
            str(row["ID"]), row["Name"], row["Roll No"], row["Course"],
            row["Subject"], str(row["Marks"]), row["Grade"], str(row["GPA"]),
        ]
        for val, (_, w) in zip(values, cols):
            pdf.cell(w, 7, _latin1(val)[:20], border=0, fill=True)
        pdf.ln()
        fill = not fill

    # fpdf2: output(dest="S") returns bytes; pyfpdf: returns a (latin-1) string for dest="S"
    try:
        pdf_out = pdf.output(dest="S")
    except TypeError:
        pdf_out = pdf.output()
    pdf_bytes = pdf_out if isinstance(pdf_out, (bytes, bytearray)) else str(pdf_out).encode("latin-1", errors="ignore")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=students_report.pdf"},
    )