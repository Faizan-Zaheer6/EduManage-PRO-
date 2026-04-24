import random
from datetime import date, timedelta
from app.database import SessionLocal, engine, Base
from app.db_models import User, Student, Course, Result, Attendance
from app.auth import hash_password

# Initialize tables
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    print("Seeding mock data into Neon database...")

    # 1. Create Admin & Test User
    if not db.query(User).filter_by(username="admin").first():
        db.add(User(username="admin", password=hash_password("admin123"), role="admin"))
    if not db.query(User).filter_by(username="testuser").first():
        db.add(User(username="testuser", password=hash_password("test123"), role="user"))

    # 2. Create Courses
    course_list = [
        ("BSCS", "Dr. Hamza"),
        ("BSIT", "Ms. Sarah"),
        ("Data Science", "Dr. Zaid"),
        ("Artificial Intelligence", "Engr. Faizan")
    ]
    created_courses = []
    for title, teacher in course_list:
        course = db.query(Course).filter_by(title=title).first()
        if not course:
            course = Course(title=title, teacher=teacher)
            db.add(course)
            db.flush()
        created_courses.append(course)

    # 3. Create 10 Students
    student_names = [
        "Ali Ahmed", "Sara Khan", "Usman Sheikh", "Zainab Bibi", 
        "Hamza Ali", "Ayesha Malik", "Bilal Siddiqui", "Hafsa Noor",
        "Omar Farooq", "Maria Jan"
    ]
    
    subjects = ["Programming", "Database", "Mathematics", "Networking"]
    
    for i, name in enumerate(student_names):
        roll = f"FA24-BS-{i+1:02d}"
        student = db.query(Student).filter_by(roll_no=roll).first()
        if not student:
            course = random.choice(created_courses)
            student = Student(
                name=name,
                email=f"{name.lower().replace(' ', '.')}@example.com",
                roll_no=roll,
                course_name=course.title,
                course_id=course.id
            )
            db.add(student)
            db.flush()

            # Add Results for each student
            for sub in subjects:
                marks = random.randint(45, 98)
                pct = marks
                # Simple grading for seed
                if pct >= 80: grade, gpa = "A", 4.0
                elif pct >= 70: grade, gpa = "B", 3.0
                elif pct >= 60: grade, gpa = "C", 2.0
                else: grade, gpa = "D", 1.0
                
                db.add(Result(
                    student_id=student.id,
                    subject=sub,
                    marks=marks,
                    total=100,
                    grade=grade,
                    gpa=gpa,
                    pct=pct
                ))

            # Add Attendance for last 7 days
            for day in range(7):
                att_date = date.today() - timedelta(days=day)
                status = "present" if random.random() > 0.15 else "absent"
                db.add(Attendance(student_id=student.id, date=att_date, status=status))

    db.commit()
    db.close()
    print("Seeding Complete! 10 students, 4 courses, and 280+ records added.")

if __name__ == "__main__":
    seed()
