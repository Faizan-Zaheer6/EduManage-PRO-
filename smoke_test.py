import re
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from datetime import datetime


BASE = "http://127.0.0.1:8000"


def extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    if not m:
        raise RuntimeError("CSRF token not found in HTML")
    return m.group(1)


def opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def get(op, path: str) -> tuple[int, str]:
    r = op.open(BASE + path)
    body = r.read().decode("utf-8", "ignore")
    return r.status, body


def post(op, path: str, data: dict) -> tuple[int, str]:
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=encoded, method="POST")
    r = op.open(req)
    body = r.read().decode("utf-8", "ignore")
    return r.status, body


def main():
    op = opener()

    # login as admin (csrf protected)
    s, html = get(op, "/login")
    assert s == 200
    csrf = extract_csrf(html)
    post(op, "/login", {"username": "admin", "password": "admin123", "csrf_token": csrf})

    # admin page (csrf in forms)
    s, admin_html = get(op, "/admin")
    assert s == 200
    csrf2 = extract_csrf(admin_html)
    unique = "SmokeCourse_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    post(op, "/add-course", {"title": unique, "teacher": "SmokeTeacher", "csrf_token": csrf2})

    # attendance mark should require csrf (we just check it doesn't 403 when provided)
    s, att_html = get(op, "/attendance")
    assert s == 200
    csrf3 = extract_csrf(att_html)
    post(op, "/attendance/mark", {"csrf_token": csrf3, "date_str": "2026-04-24"})

    # cgpa calculate
    s, cgpa_html = get(op, "/cgpa")
    assert s == 200
    csrf4 = extract_csrf(cgpa_html)
    post(
        op,
        "/cgpa",
        {
            "csrf_token": csrf4,
            "subject": "Math",
            "marks": "80",
            "total": "100",
            "credits": "3",
        },
    )

    print("smoke_test: OK")


if __name__ == "__main__":
    main()

