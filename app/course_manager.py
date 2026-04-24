from .database import SessionLocal
from .db_models import Student, Course, Result
from sqlalchemy.orm import joinedload


class StudentManager:
    def __init__(self):
        pass

    # ── CRUD ────────────────────────────────────────────────────────────────

    def enroll_student(self, name, email, course, roll_no):
        db = SessionLocal()
        try:
            new_student = Student(name=name, email=email, course_name=course, roll_no=roll_no)
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            return new_student.id
        finally:
            db.close()

    @property
    def students(self):
        """Property to mimic old list-based access for simple counts/iter."""
        db = SessionLocal()
        try:
            items = db.query(Student).options(joinedload(Student.results)).all()
            result_list = []
            for item in items:
                d = item.__dict__.copy()
                d.pop('_sa_instance_state', None)
                d['results'] = [r.__dict__.copy() for r in item.results]
                for r_dict in d['results']:
                    r_dict.pop('_sa_instance_state', None)
                result_list.append(d)
            return result_list
        finally:
            db.close()

    def get_by_id(self, student_id: int):
        db = SessionLocal()
        try:
            student = db.query(Student).options(joinedload(Student.results)).filter(Student.id == student_id).first()
            if student:
                d = student.__dict__.copy()
                d.pop('_sa_instance_state', None)
                d['results'] = [r.__dict__.copy() for r in student.results]
                for r_dict in d['results']:
                    r_dict.pop('_sa_instance_state', None)
                return d
            return None
        finally:
            db.close()

    def update_student(self, student_id: int, name: str, email: str, course: str, roll_no: str):
        db = SessionLocal()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                student.name = name
                student.email = email
                student.course_name = course
                student.roll_no = roll_no
                db.commit()
                return True
            return False
        finally:
            db.close()

    def remove_student(self, student_id: int):
        db = SessionLocal()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                db.delete(student)
                db.commit()
        finally:
            db.close()

    # ── Marks / Results ─────────────────────────────────────────────────────

    def add_result(self, student_id: int, subject: str, marks: float, total: float = 100):
        from .models import grade_from_marks
        grade_info = grade_from_marks(marks, total)
        
        db = SessionLocal()
        try:
            # Check if subject already exists for student
            existing = db.query(Result).filter(Result.student_id == student_id, Result.subject == subject).first()
            if existing:
                db.delete(existing)
            
            new_res = Result(
                student_id=student_id,
                subject=subject,
                marks=marks,
                total=total,
                grade=grade_info["grade"],
                gpa=grade_info["gpa"],
                pct=grade_info["pct"]
            )
            db.add(new_res)
            db.commit()
            return new_res
        finally:
            db.close()

    def delete_result(self, student_id: int, subject: str):
        db = SessionLocal()
        try:
            res = db.query(Result).filter(Result.student_id == student_id, Result.subject == subject).first()
            if res:
                db.delete(res)
                db.commit()
                return True
            return False
        finally:
            db.close()

    # ── Export helper ───────────────────────────────────────────────────────

    def get_all_flat(self):
        db = SessionLocal()
        try:
            students = db.query(Student).options(joinedload(Student.results)).all()
            rows = []
            for s in students:
                results = s.results
                if results:
                    for r in results:
                        rows.append({
                            "ID": s.id, "Name": s.name, "Roll No": s.roll_no,
                            "Email": s.email, "Course": s.course_name,
                            "Subject": r.subject, "Marks": r.marks,
                            "Total": r.total, "Grade": r.grade, "GPA": r.gpa,
                        })
                else:
                    rows.append({
                        "ID": s.id, "Name": s.name, "Roll No": s.roll_no,
                        "Email": s.email, "Course": s.course_name,
                        "Subject": "-", "Marks": "-", "Total": "-", "Grade": "-", "GPA": "-",
                    })
            return rows
        finally:
            db.close()

    # ── Search & Paginate ───────────────────────────────────────────────────

    def search(self, name: str = "", course: str = "", roll_no: str = ""):
        db = SessionLocal()
        try:
            query = db.query(Student).options(joinedload(Student.results))
            if name:
                query = query.filter(Student.name.ilike(f"%{name}%"))
            if course:
                query = query.filter(Student.course_name.ilike(f"%{course}%"))
            if roll_no:
                query = query.filter(Student.roll_no.ilike(f"%{roll_no}%"))
            
            items = query.all()
            # Convert to list of dicts for legacy support in templates
            result_list = []
            for item in items:
                d = item.__dict__.copy()
                d.pop('_sa_instance_state', None)
                d['results'] = [r.__dict__.copy() for r in item.results]
                for r_dict in d['results']:
                    r_dict.pop('_sa_instance_state', None)
                result_list.append(d)
            return result_list
        finally:
            db.close()

    @staticmethod
    def paginate(items: list, page: int, per_page: int = 10):
        total = len(items)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        return items[start: start + per_page], page, total_pages


class CourseManager:
    def __init__(self):
        pass

    @property
    def courses(self):
        db = SessionLocal()
        try:
            items = db.query(Course).all()
            result_list = []
            for item in items:
                d = item.__dict__.copy()
                d.pop('_sa_instance_state', None)
                result_list.append(d)
            return result_list
        finally:
            db.close()

    def add_course(self, title: str, teacher: str):
        db = SessionLocal()
        try:
            new_course = Course(title=title, teacher=teacher)
            db.add(new_course)
            db.commit()
        finally:
            db.close()

    def remove_course(self, course_id: int):
        db = SessionLocal()
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                db.delete(course)
                db.commit()
        finally:
            db.close()

    def get_by_id(self, course_id: int):
        db = SessionLocal()
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                d = course.__dict__.copy()
                d.pop('_sa_instance_state', None)
                return d
            return None
        finally:
            db.close()