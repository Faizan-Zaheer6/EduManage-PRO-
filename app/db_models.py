from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    TEACHER = "teacher"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNMARKED = "unmarked"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # for teachers

    student = relationship("Student")
    course = relationship("Course")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    teacher = Column(String)
    students = relationship("Student", back_populates="course_rel")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String)
    roll_no = Column(String, unique=True, index=True)
    course_name = Column(String)  # We'll keep the name for compatibility, or link to Course ID
    
    # Relationships
    results = relationship("Result", back_populates="student", cascade="all, delete-orphan")
    attendance = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    
    # Optional: Link to Course table
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    course_rel = relationship("Course", back_populates="students")

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String)
    marks = Column(Float)
    total = Column(Float, default=100.0)
    grade = Column(String)
    gpa = Column(Float)
    pct = Column(Float)
    
    student = relationship("Student", back_populates="results")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    status = Column(String) # present, absent
    
    student = relationship("Student", back_populates="attendance")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True, index=True)

    user = relationship("User")
