import re
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


BASE = "http://127.0.0.1:8000"


def extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    if not m:
        raise RuntimeError("CSRF token not found")
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

    # admin login
    _, login_html = get(op, "/login")
    csrf = extract_csrf(login_html)
    post(op, "/login", {"username": "admin", "password": "admin123", "csrf_token": csrf})

    # enroll a student
    _, enroll_html = get(op, "/enroll-page")
    csrf2 = extract_csrf(enroll_html)
    post(
        op,
        "/enroll",
        {
            "csrf_token": csrf2,
            "name": "Smoke Student",
            "roll_no": "SM-999",
            "email": "smoke@example.com",
            "course": "BSCS",
        },
    )

    # locate the student id (search by roll)
    _, records_html = get(op, "/view-records?roll_no=SM-999")
    m = re.search(r'/student/(\d+)" class="btn-sm btn-view"', records_html)
    if not m:
        raise RuntimeError("Newly enrolled student not found in records page")
    sid = int(m.group(1))

    # edit student
    _, edit_html = get(op, f"/student/{sid}/edit")
    csrf3 = extract_csrf(edit_html)
    post(
        op,
        f"/student/{sid}/edit",
        {
            "csrf_token": csrf3,
            "name": "Smoke Student",
            "roll_no": "SM-999",
            "email": "smoke2@example.com",
            "course": "BSCS",
        },
    )

    # add marks
    _, marks_html = get(op, f"/student/{sid}/marks")
    csrf4 = extract_csrf(marks_html)
    post(
        op,
        f"/student/{sid}/marks",
        {"csrf_token": csrf4, "subject": "Math", "marks": "80", "total": "100"},
    )

    # remove student (POST)
    _, records_html2 = get(op, "/view-records?roll_no=SM-999")
    csrf5 = extract_csrf(records_html2)
    post(op, f"/remove/{sid}", {"csrf_token": csrf5})

    print("smoke_test_extended: OK")


if __name__ == "__main__":
    main()

