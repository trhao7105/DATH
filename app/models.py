from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime, timezone

# =========================
# ENUM TYPES 
# =========================

class UserRole(enum.Enum):
    student = "student"
    tutor = "tutor"
    admin = "admin"
    coordinator = "coordinator"

class ProgramStatus(enum.Enum):
    open = "open"
    closed = "closed"

class AppointmentStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

class RequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


# =========================
# USERS
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    mssv = Column(String(20), unique=True, index=True)
    password = Column(String(255))
    ho_ten = Column(String(100))

    role = Column(
        Enum(UserRole, name="user_role"),
        default=UserRole.student,
        nullable=False
    )

    registrations = relationship("Registration", back_populates="student")
    time_slots = relationship("TimeSlot", back_populates="tutor")
    appointments = relationship("Appointment", back_populates="student")

    student_booking_requests = relationship(
        "BookingRequest",
        back_populates="student",
        foreign_keys="[BookingRequest.student_id]"
    )

    tutor_booking_requests = relationship(
        "BookingRequest",
        back_populates="tutor",
        foreign_keys="[BookingRequest.tutor_id]"
    )


# =========================
# PROGRAMS
# =========================

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    semester = Column(String(50))

    status = Column(
        Enum(ProgramStatus, name="program_status"),
        default=ProgramStatus.open
    )

    registrations = relationship("Registration", back_populates="program")


# =========================
# REGISTRATIONS
# =========================

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    program_id = Column(Integer, ForeignKey("programs.id"))

    student = relationship("User", back_populates="registrations")
    program = relationship("Program", back_populates="registrations")


# =========================
# TIME SLOTS
# =========================

class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id"))

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    is_booked = Column(Boolean, default=False)

    tutor = relationship("User", back_populates="time_slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)
    booking_request = relationship("BookingRequest", back_populates="slot", uselist=False)


# =========================
# APPOINTMENTS
# =========================

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("time_slots.id"))

    status = Column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.confirmed
    )

    student = relationship("User", back_populates="appointments")
    slot = relationship("TimeSlot", back_populates="appointment")


# =========================
# TUTOR REQUEST
# =========================

class TutorRequest(Base):
    __tablename__ = "tutor_requests"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(
        Enum(RequestStatus, name="request_status"),
        default=RequestStatus.pending,
        nullable=False
    )

    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    reject_reason = Column(Text, nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    tutor = relationship("User", foreign_keys=[tutor_id])

    __table_args__ = (
        UniqueConstraint('student_id', 'tutor_id', 'status', name='unique_pending_request'),
        Index('ix_tutor_requests_tutor_status', 'tutor_id', 'status'),
        Index('ix_tutor_requests_student', 'student_id'),
    )


# =========================
# BOOKING REQUEST
# =========================

class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("users.id"))
    tutor_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("time_slots.id"))

    note = Column(Text, nullable=True)

    status = Column(
        Enum(RequestStatus, name="booking_request_status"),
        default=RequestStatus.pending
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    student = relationship("User", back_populates="student_booking_requests", foreign_keys=[student_id])
    tutor = relationship("User", back_populates="tutor_booking_requests", foreign_keys=[tutor_id])
    slot = relationship("TimeSlot", back_populates="booking_request")

    __table_args__ = (
        UniqueConstraint(
            "slot_id",
            "status",
            name="unique_slot_booking",
            deferrable=True,
            initially="DEFERRED"
        ),
    )