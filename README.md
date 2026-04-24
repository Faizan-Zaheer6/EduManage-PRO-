<<<<<<< HEAD
🎓 EduManage Pro - Student & Course Management System
EduManage Pro is a modern web application built with FastAPI, designed to streamline administrative tasks for educational institutes. It features a high-performance dashboard and a dedicated Admin Panel for efficient management of students and courses.

✨ Key Features
Glassmorphism Dashboard: A stunning, modern UI providing real-time statistics and an intuitive user experience.

🛡️ Robust Admin Panel: A professional sidebar-based interface for managing curricula and adding new courses.

📝 Seamless Enrollment: A simplified registration system for onboarding new students.

📊 Advanced Records Management: Centralized data storage with powerful search and viewing capabilities.

📱 Fully Responsive: Optimized with Tailwind CSS to ensure a flawless experience across mobile, tablet, and desktop devices.

🛠️ Tech Stack
Backend: FastAPI (Python)
=======
# ⚡ EduManage Pro

**EduManage Pro** is a premium, feature-rich Student Administration System built with **FastAPI**. It provides a comprehensive solution for educational institutions to manage enrollments, academic performance, attendance, and institutional analytics.

---

## 🚀 Core Features

### 🔐 Advanced Authentication
- **Role-Based Access Control (RBAC):** Admins get full system control; Users (Students/Staff) get restricted personal views.
- **Secure Sessions:** Cookie-based session management with encrypted passwords.

### 📊 Institutional Analytics (Admin Only)
- **Live Charts:** Real-time visualization of student distribution per course and daily attendance trends using **Chart.js**.
- **System Stats:** Quick overview of total strength, active courses, and daily engagement.

### 🎓 Academic Excellence
- **Smart Grading Engine:** Automatically calculates Letter Grades (A+ to F), GPA points, and percentages from marks.
- **Results Management:** Dedicated interface for admins to enter, update, and delete subject-wise marks.
- **Personal Profiles:** Detailed student pages with result tables and academic summaries.

### 📅 Attendance Intelligence
- **Daily Tracker:** Bulk attendance marking for administrators with historical date support.
- **Personal Stats:** Automated attendance percentage and "Donut Chart" visualization for every student.

### 📁 Professional Exports
- **PDF Reports:** Generate branded, formatted academic reports in one click.
- **CSV Data:** Export student records to spreadsheets for external processing.

### 🎨 Premium UI/UX
- **Modern Aesthetic:** Built with Glassmorphism, smooth CSS gradients, and the elegant **Outfit** typography.
- **Responsive Design:** Fully optimized for both desktop and mobile viewing.
>>>>>>> 4653798 (EduManage update)

---

## 🛠️ Tech Stack
- **Backend:** Python (FastAPI)
- **Templating:** Jinja2
- **Persistence:** SQLAlchemy (SQLite local dev / Postgres e.g. Neon)
- **Charts:** Chart.js
- **PDF Generation:** FPDF2
- **Styling:** TailwindCSS (via CDN) & Custom Vanilla CSS

<<<<<<< HEAD
Core Logic: Python-based CRUD operations for reliable data handling.

🚀 Local Setup Guide
Clone the Repository:

Bash
git clone https://github.com/Faizan-Zaheer6/FastAPI-Student-Admin.git
cd FastAPI-Student-Admin
Install Dependencies:

Bash
pip install fastapi uvicorn jinja2 python-multipart
Launch the Server:

Bash
uvicorn main:app --reload
Access the App:
Open your browser and navigate to http://127.0.0.1:8000.

📂 Project Architecture
main.py: The main entry point of the application.

app/routes.py: Handles API endpoints, URL routing, and business logic.

templates/: Contains Jinja2 HTML templates for the Dashboard, Admin Panel, and Student Records.

app/course_manager.py: Core Python logic for managing the student and course lifecycles.

👨‍💻 Author
Faizan Zaheer 8th Semester BSCS Student at NUML FSD Python & FastAPI Developer | Backend Enthusiast
=======
---

## 📦 Installation & Setup

1. **Clone the project:**
   ```bash
   git clone <your-repo-link>
   cd FastAPI-Student-Admin
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file (recommended):**

   - `DATABASE_URL`: Postgres URL for production (Neon etc). If not set, app uses SQLite local file.
   - `SESSION_SECRET`: random long secret for signed sessions
   - `COOKIE_SECURE`: set `True` on HTTPS deployments (Vercel)
   - `SESSION_MAX_AGE_SECONDS`: optional, default 86400

4. **Run migrations (production-style):**

   ```bash
   python -m alembic upgrade head
   ```

5. **Run the application:**
   ```bash
   python -m uvicorn main:app --reload
   ```

6. **Access the Dashboard:**
   Open `http://127.0.0.1:8000` in your browser.

---

## 🔑 Default Credentials
- **Admin Username:** `admin`
- **Admin Password:** `admin123`
*(New users can be registered via the Signup page)*

---

## 📂 Project Structure
- `app/` - Core logic, managers, and routes.
- `alembic/` - Database migrations.
- `api/index.py` - Vercel entrypoint.
- `templates/` - Premium UI templates.
- `main.py` - Application entry point.

---

## 🚀 Deploy (Vercel)

This repo includes `vercel.json` configured for FastAPI.

In Vercel, set environment variables:
- `DATABASE_URL`
- `SESSION_SECRET`
- `COOKIE_SECURE=True`

---
© 2026 EduManage Pro · Built for Efficiency.
>>>>>>> 4653798 (EduManage update)
