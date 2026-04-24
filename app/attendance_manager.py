from .database import SessionLocal
from .db_models import Attendance, Student
from datetime import date as date_type
from sqlalchemy import func


class AttendanceManager:
    def __init__(self):
        pass

    def mark_bulk(self, date_str: str, records: dict):
        """records = {student_id_str: 'present'|'absent'}"""
        db = SessionLocal()
        try:
            # Parse date
            y, m, d = map(int, date_str.split('-'))
            dt = date_type(y, m, d)
            
            for sid_str, status in records.items():
                sid = int(sid_str)
                # Check if already exists for this student on this date
                existing = db.query(Attendance).filter(Attendance.student_id == sid, Attendance.date == dt).first()
                if existing:
                    existing.status = status
                else:
                    db.add(Attendance(student_id=sid, date=dt, status=status))
            db.commit()
        finally:
            db.close()

    def get_for_date(self, date_str: str) -> dict:
        db = SessionLocal()
        try:
            y, m, d = map(int, date_str.split('-'))
            dt = date_type(y, m, d)
            recs = db.query(Attendance).filter(Attendance.date == dt).all()
            return {str(r.student_id): r.status for r in recs}
        finally:
            db.close()

    def get_student_summary(self, student_id: int) -> dict:
        db = SessionLocal()
        try:
            present = db.query(Attendance).filter(Attendance.student_id == student_id, Attendance.status == "present").count()
            absent  = db.query(Attendance).filter(Attendance.student_id == student_id, Attendance.status == "absent").count()
            total = present + absent
            pct = round((present / total) * 100, 1) if total > 0 else 0.0
            return {"present": present, "absent": absent, "total": total, "pct": pct}
        finally:
            db.close()

    def today_summary(self, student_ids: list) -> dict:
        dt = date_type.today()
        db = SessionLocal()
        try:
            today_recs = db.query(Attendance).filter(Attendance.date == dt).all()
            status_map = {r.student_id: r.status for r in today_recs}
            
            present = sum(1 for sid in student_ids if status_map.get(sid) == "present")
            absent  = sum(1 for sid in student_ids if status_map.get(sid) == "absent")
            unmarked = len(student_ids) - present - absent
            return {"present": present, "absent": absent, "unmarked": unmarked}
        finally:
            db.close()

    def all_dates(self) -> list:
        db = SessionLocal()
        try:
            dates = db.query(Attendance.date).distinct().order_by(Attendance.date.desc()).all()
            return [str(d[0]) for d in dates]
        finally:
            db.close()
