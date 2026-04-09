from sqlalchemy.orm import Session, joinedload
from app.models import User, Program, Registration, TimeSlot, Appointment, BookingRequest
from typing import List, Optional
from datetime import datetime, timezone, timedelta

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_by_mssv(self, mssv: str) -> Optional[User]:
        return self.db.query(User).filter(User.mssv == mssv).first()
    def get_all(self):
        return self.db.query(User).all()
    # NEW: Get all tutors
    def get_all_tutors(self) -> List[User]:
        return self.db.query(User).filter(User.role == 'tutor').all()

class ProgramRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_open_programs(self) -> List[Program]:
        return self.db.query(Program).filter(Program.status == 'open').order_by(Program.id.desc()).all()
    
    def register_student(self, student_id: int, program_id: int):
        exists = self.db.query(Registration).filter_by(student_id=student_id, program_id=program_id).first()
        if exists: raise Exception("Bạn đã đăng ký chương trình này rồi")
        reg = Registration(student_id=student_id, program_id=program_id)
        self.db.add(reg)
        self.db.commit()
        return reg
    
    def create_program(self, name: str, semester: str):
        prog = Program(name=name, semester=semester, status='open')
        self.db.add(prog)
        self.db.commit()
        return prog

class ScheduleRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_slots_by_tutor(self, tutor_id: int) -> List[TimeSlot]:
        return self.db.query(TimeSlot).filter(TimeSlot.tutor_id == tutor_id).all()
    
    def get_slot_by_id(self, slot_id: int):
        return self.db.query(TimeSlot).filter(TimeSlot.id == slot_id).first()

    def create_slot(self, tutor_id: int, start_time: datetime, end_time: datetime):
        slot = TimeSlot(tutor_id=tutor_id, start_time=start_time, end_time=end_time)
        self.db.add(slot)
        self.db.commit()
        return slot

    def delete_slot(self, tutor_id: int, start_time: datetime):
        self.db.query(TimeSlot).filter(TimeSlot.tutor_id == tutor_id, TimeSlot.start_time == start_time).delete()
        self.db.commit()

    def mark_booked(self, slot_id: int):
        slot = self.get_slot_by_id(slot_id)
        if slot:
            slot.is_booked = True
            self.db.commit()

    def create_appointment(self, student_id: int, slot_id: int):
        appt = Appointment(student_id=student_id, slot_id=slot_id)
        self.db.add(appt)
        self.db.commit()
        return appt

class SystemRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_logs(self): return []



class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, student_id, tutor_id, slot_id, note):
        req = BookingRequest(
            student_id=student_id,
            tutor_id=tutor_id,
            slot_id=slot_id,
            note = note,
            status="pending"
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req
    
    def get_pending_requests(self, tutor_id: int):
        return (
            self.db.query(BookingRequest)
            .options(
                joinedload(BookingRequest.student),
                joinedload(BookingRequest.slot)
            )
            .filter(
                BookingRequest.tutor_id == tutor_id,
                BookingRequest.status == "pending"
            )
            .order_by(BookingRequest.created_at.asc())
            .all()
        )
    
    def get_upcoming_sessions(self, tutor_id: int):
        vn_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(vn_tz).replace(tzinfo=None)
        
        return (
            self.db.query(BookingRequest)
            .join(TimeSlot)
            .options(
                joinedload(BookingRequest.student),
                joinedload(BookingRequest.slot)
            )
            .filter(
                BookingRequest.tutor_id == tutor_id,
                BookingRequest.status == "accepted",
                TimeSlot.end_time >= current_time 
            )
            .order_by(TimeSlot.start_time.asc())
            .all()
        )

    def get_by_tutor(self, tutor_id):
        return (
            self.db.query(BookingRequest)
            .options(
                joinedload(BookingRequest.student),
                joinedload(BookingRequest.slot)
            )
            .filter(BookingRequest.tutor_id == tutor_id)
            .order_by(BookingRequest.created_at.desc())
            .all()
        )

    def get_by_student(self, student_id):
        return (
            self.db.query(BookingRequest)
            .options(
                joinedload(BookingRequest.slot),
                joinedload(BookingRequest.tutor)
            )
            .filter(BookingRequest.student_id == student_id)
            .order_by(BookingRequest.created_at.desc())
            .all()
        )

    def get_by_id(self, req_id):
        return self.db.query(BookingRequest).filter(BookingRequest.id == req_id).first()

    def update_status(self, req_id, status):
        req = self.get_by_id(req_id)
        if req:
            req.status = status
            if status == "accepted":
                slot = self.db.query(TimeSlot).filter(TimeSlot.id == req.slot_id).first()
                if slot:
                    slot.is_booked = True
            self.db.commit()
            self.db.refresh(req)
            return req
        return None

    def delete_request(self, req_id, student_id):
        self.db.query(BookingRequest).filter(
            BookingRequest.id == req_id,
            BookingRequest.student_id == student_id,
            BookingRequest.status == "pending"
        ).delete()
        self.db.commit()