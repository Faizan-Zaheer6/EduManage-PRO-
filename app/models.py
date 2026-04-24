class Person:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email


def grade_from_marks(marks: float, total: float = 100) -> dict:
    """Return letter grade, GPA point, and percentage from marks/total."""
    if total <= 0:
        return {"grade": "N/A", "gpa": 0.0, "pct": 0.0}
    pct = (marks / total) * 100
    if pct >= 90:
        grade, gpa = "A+", 4.0
    elif pct >= 80:
        grade, gpa = "A", 4.0
    elif pct >= 70:
        grade, gpa = "B+", 3.5
    elif pct >= 60:
        grade, gpa = "B", 3.0
    elif pct >= 50:
        grade, gpa = "C", 2.0
    elif pct >= 40:
        grade, gpa = "D", 1.0
    else:
        grade, gpa = "F", 0.0
    return {"grade": grade, "gpa": gpa, "pct": round(pct, 1)}


class Student(Person):
    def __init__(self, student_id: int, name: str, email: str, course: str, roll_no: str):
        super().__init__(name, email)
        self.id = student_id
        self.course = course
        self.roll_no = roll_no
        self.results = []   # list of {subject, marks, total, grade, gpa, pct}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "course": self.course,
            "roll_no": self.roll_no,
            "results": self.results,
        }