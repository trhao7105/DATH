from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import random

from app.models import TutorRequest, RequestStatus, User
from app.database import get_db
from app.services.services import (
    AuthService, ScheduleService, CoordinationService,
    SysManagementService, MatchingService, BookingService
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =========================
# HELPERS
# =========================

def get_user_session(request: Request):
    """Lấy thông tin user từ session một cách an toàn"""
    user = request.session.get("user")
    if isinstance(user, dict) and user.get("id") and user.get("role"):
        return user
    return None


def require_role(request: Request, role: str):
    """Kiểm tra quyền truy cập theo role"""
    user = get_user_session(request)
    if not user or user.get("role") != role:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return user


# =========================
# INPUT MODELS
# =========================

class LoginRequest(BaseModel):
    mssv: str
    password: str


class ScheduleRequest(BaseModel):
    action: str
    slots: List[str]


class ProgramRegRequest(BaseModel):
    program_id: int


class BookRequest(BaseModel):
    slot_id: int
    note: Optional[str] = None


class TutorSelectRequest(BaseModel):
    tutor_id: int


class TutorRespondBooking(BaseModel):
    req_id: int
    action: str  # 'accept' hoặc 'reject'


class TutorRespondRequest(BaseModel):
    request_id: int
    accept: bool
    reason: Optional[str] = None


# =========================
# AUTH ROUTES
# =========================

@router.post("/api/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.login(req.mssv, req.password)
    
    if user:
        # CHỈ lưu dữ liệu primitive để tránh lỗi JSON serializable
        user_data = {
            "id": user.id,
            "ho_ten": user.ho_ten,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }
        request.session["user"] = user_data
        return {"success": True, "user": user_data}
    
    return {"success": False, "message": "Sai MSSV hoặc mật khẩu"}


@router.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"success": True}


# =========================
# FIND TUTOR USE CASE
# =========================

@router.get("/find-tutor", response_class=HTMLResponse)
def view_find_tutor(request: Request):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        return RedirectResponse("/")
    
    return templates.TemplateResponse(
        request=request, 
        name="find_tutor.html", 
        context={"user": user}
    )


@router.get("/api/find_tutor")
def api_find_tutor(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user:
        return []

    match_service = MatchingService(db)
    tutors_db = match_service.search_tutors()

    departments = ["Khoa học Máy tính", "Điện - Điện tử", "Cơ khí", "Kỹ thuật Hóa học", "Khoa học Ứng dụng"]
    subjects_pool = ["Giải tích 1", "Vật lý 1", "Đại số tuyến tính", "Cấu trúc dữ liệu", "Lập trình C++", "Hóa đại cương"]

    enriched_tutors = []
    for t in tutors_db:
        enriched_tutors.append({
            "id": t.id,
            "name": t.ho_ten,
            "mssv": t.mssv,
            "department": random.choice(departments),
            "rating": round(random.uniform(4.0, 5.0), 1),
            "totalSessions": random.randint(10, 50),
            "subjects": random.sample(subjects_pool, k=2),
            "bio": "Sinh viên năm 3 với thành tích học tập xuất sắc. Nhiệt tình hỗ trợ các bạn mất gốc.",
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={t.mssv}"
        })
    
    return enriched_tutors


@router.post("/api/select_tutor")
def api_select_tutor(req: TutorSelectRequest, request: Request, db: Session = Depends(get_db)):
    user = require_role(request, "student")
    match_service = MatchingService(db)
    
    if match_service.select_tutor(user["id"], req.tutor_id):
        return {"success": True, "message": "Đã gửi yêu cầu đến tutor thành công!"}
    else:
        return {"success": False, "message": "Không thể gửi. Bạn đã gửi yêu cầu này rồi hoặc tutor không tồn tại."}


# =========================
# TUTOR - QUẢN LÝ YÊU CẦU TÌM TUTOR
# =========================

@router.get("/api/tutor/pending_requests")
def get_pending_requests(request: Request, db: Session = Depends(get_db)):
    user = require_role(request, "tutor")
    match_service = MatchingService(db)
    
    requests = match_service.get_pending_requests_for_tutor(user["id"])
    
    return [{
        "id": r.id,
        "student_name": r.student.ho_ten,
        "student_mssv": r.student.mssv,
        "requested_at": r.requested_at.strftime("%d/%m/%Y %H:%M")
    } for r in requests]


@router.post("/api/tutor/respond_request")
def respond_request(payload: TutorRespondRequest, request: Request, db: Session = Depends(get_db)):
    user = require_role(request, "tutor")
    match_service = MatchingService(db)
    
    if not payload.accept and (not payload.reason or payload.reason.strip() == ""):
        return {"success": False, "message": "Vui lòng nhập lý do từ chối!"}
    
    if match_service.respond_to_request(payload.request_id, user["id"], payload.accept, payload.reason):
        action = "đồng ý" if payload.accept else "từ chối"
        return {"success": True, "message": f"Đã {action} yêu cầu thành công!"}
    else:
        return {"success": False, "message": "Yêu cầu không tồn tại hoặc đã được xử lý."}


@router.get("/api/my_tutor_requests")
def get_my_requests(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        return []

    requests = (
        db.query(TutorRequest)
        .join(User, User.id == TutorRequest.tutor_id)
        .filter(TutorRequest.student_id == user["id"])
        .order_by(TutorRequest.requested_at.desc())
        .all()
    )

    result = []
    for r in requests:
        result.append({
            "id": r.id,
            "tutor_name": r.tutor.ho_ten if r.tutor else "Tutor không tồn tại",
            "tutor_mssv": r.tutor.mssv if r.tutor else "",
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "status_text": (
                "Đang chờ phản hồi" if r.status == RequestStatus.pending else
                "Đã chấp nhận" if r.status == RequestStatus.accepted else
                "Bị từ chối"
            ),
            "requested_at": r.requested_at.strftime("%d/%m/%Y %H:%M"),
            "responded_at": r.responded_at.strftime("%d/%m/%Y %H:%M") if r.responded_at else None,
            "reject_reason": r.reject_reason or None
        })

    return result


# =========================
# STUDENT ROUTES
# =========================

@router.get("/register", response_class=HTMLResponse)
def view_register(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        return RedirectResponse("/")
    
    coord_service = CoordinationService(db)
    programs = coord_service.get_available_programs()
    
    return templates.TemplateResponse(
        request=request,
        name="register.html", 
        context={
            "user": user, 
            "programs": programs
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
def view_student_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        return RedirectResponse("/")
    
    booking_service = BookingService(db)
    raw_requests = booking_service.get_student_bookings(user["id"])
    
    from datetime import datetime, timezone, timedelta
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz).replace(tzinfo=None)
    
    upcoming_sessions = []
    recent_sessions = []
    total_hours = 0.0
    completed_count = 0

    for req in raw_requests:
        req_status = req.status.value if hasattr(req.status, "value") else str(req.status)
        
        if req.slot and "accepted" in req_status:
            start_dt = req.slot.start_time
            end_dt = req.slot.end_time
            
            if hasattr(start_dt, 'tzinfo') and start_dt.tzinfo is not None:
                start_dt = start_dt.replace(tzinfo=None)
            if hasattr(end_dt, 'tzinfo') and end_dt.tzinfo is not None:
                end_dt = end_dt.replace(tzinfo=None)

            session_info = {
                "date": start_dt,
                "subject": req.note if req.note else "Hỗ trợ học tập",
                "tutor_name": req.tutor.ho_ten if req.tutor else "N/A",
                "status": "accepted",
                "start_time": start_dt.strftime("%H:%M"),
                "end_time": end_dt.strftime("%H:%M"),
                "location": "Phòng học Online"
            }

            if end_dt >= now:
                upcoming_sessions.append(session_info)
            else:
                recent_sessions.append(session_info)
                completed_count += 1
                duration = end_dt - start_dt
                total_hours += duration.total_seconds() / 3600

    upcoming_sessions.sort(key=lambda x: x["date"])
    recent_sessions.sort(key=lambda x: x["date"], reverse=True)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", 
        context={
            "user": user, 
            "total_sessions": len(upcoming_sessions) + completed_count,
            "completed_sessions": completed_count,
            "upcoming_count": len(upcoming_sessions),
            "accumulated_hours": round(total_hours, 1),
            "upcoming_sessions": upcoming_sessions[:5],
            "recent_sessions": recent_sessions[:5]
        }
    )

@router.post("/api/register_program")
def register_program(req: ProgramRegRequest, request: Request, db: Session = Depends(get_db)):
    user = require_role(request, "student")
    coord_service = CoordinationService(db)
    try:
        coord_service.register_student_to_program(user["id"], req.program_id)
        return {"success": True, "message": "Đăng ký thành công!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# TUTOR ROUTES
# =========================

@router.get("/tutor/dashboard", response_class=HTMLResponse)
def view_tutor_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "tutor":
        return RedirectResponse("/")
    
    booking_service = BookingService(db)

    # Yêu cầu đang chờ
    raw_pending = booking_service.tutor_get_pending_requests(user["id"])
    pending_requests = []
    for r in raw_pending:
        if r.slot and r.student:
            pending_requests.append({
                "id": r.id,
                "date": r.slot.start_time,
                "studentName": r.student.ho_ten,
                "startTime": r.slot.start_time.strftime("%H:%M"),
                "endTime": r.slot.end_time.strftime("%H:%M"),
                "notes": r.note or "",
                "status": r.status,
                "slot_id": r.slot.id
            })

    # Buổi học sắp tới
    raw_upcoming = booking_service.tutor_get_upcoming_sessions(user["id"])
    upcoming_sessions = []
    for r in raw_upcoming:
        if r.slot and r.student:
            upcoming_sessions.append({
                "id": r.id,
                "date": r.slot.start_time,
                "studentName": r.student.ho_ten,
                "startTime": r.slot.start_time.strftime("%H:%M"),
                "endTime": r.slot.end_time.strftime("%H:%M"),
                "status": r.status,
                "location": "Phòng học online",
                "slot_id": r.slot.id
            })
    
    active_students_list = booking_service.get_tutor_students(user["id"])
    actual_teaching_hours = booking_service.get_teaching_hours(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="tutor_dashboard.html", 
        context={
            "user": user,
            "pending_requests": pending_requests,
            "upcoming_sessions": upcoming_sessions,
            "total_sessions": 156,
            "active_students": len(active_students_list),
            "rating": 4.8,
            "teaching_hours": actual_teaching_hours
        }
    )


@router.get("/schedule", response_class=HTMLResponse)
def view_schedule(request: Request):
    user = get_user_session(request)
    if not user or user.get("role") != "tutor":
        return RedirectResponse("/")
    
    return templates.TemplateResponse(
        request=request, 
        name="schedule.html", 
        context={"user": user}
    )


@router.get("/api/get_schedule")
def get_schedule(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user:
        return []
    
    service = ScheduleService(db)
    slots = service.get_tutor_schedule(user["id"])
    
    events = []
    for s in slots:
        events.append({
            "title": "Rảnh",
            "start": str(s.start_time).replace(" ", "T"),
            "end": str(s.end_time).replace(" ", "T"),
            "color": "#28a745"
        })
    return events


@router.post("/api/update_schedule")
def update_schedule(req: ScheduleRequest, request: Request, db: Session = Depends(get_db)):
    user = require_role(request, "tutor")
    service = ScheduleService(db)
    
    try:
        if req.action == "add":
            for t in req.slots:
                service.add_slot(user["id"], t)
            msg = "Đã thêm khung giờ"
        elif req.action == "delete":
            for t in req.slots:
                service.remove_slot(user["id"], t)
            msg = "Đã xóa khung giờ"
        else:
            msg = "Action không hợp lệ"
        return {"success": True, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# STUDENT SCHEDULE & BOOKING
# =========================

@router.get("/student/schedule", response_class=HTMLResponse)
def view_student_schedule(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        return RedirectResponse("/")
    
    booking_service = BookingService(db)
    raw_requests = booking_service.get_student_bookings(user["id"])
    
    requests_data = []
    for req in raw_requests:
        if req.slot:
            requests_data.append({
                "id": req.id,
                "status": req.status.value if hasattr(req.status, "value") else str(req.status),
                "note": req.note,
                "start": req.slot.start_time.strftime("%H:%M"),
                "end": req.slot.end_time.strftime("%H:%M"),
                "start_time": req.slot.start_time,
                "end_time": req.slot.end_time,
                "tutor_name": req.tutor.ho_ten if req.tutor else "N/A"
            })

    return templates.TemplateResponse(
        request=request,
        name="student_schedule.html", 
        context={
            "user": user, 
            "requests": requests_data
        }
    )


@router.get("/api/student/schedule")
def student_schedule(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = BookingService(db)
    raw_requests = service.get_student_bookings(user["id"])
    
    events = []
    for req in raw_requests:
        if req.slot and req.tutor and req.status != "rejected":
            status_display = "pending" if req.status == "pending" else "accepted"
            textColor = "#a16225" if req.status == "pending" else "#15803d"
            
            events.append({
                "title": f"{req.tutor.ho_ten}",
                "start": str(req.slot.start_time)[:19].replace(" ", "T"),
                "end": str(req.slot.end_time)[:19].replace(" ", "T"),
                "status": status_display,
                "textColor": textColor
            })
    return events


@router.get("/api/student/slots")
def get_slots(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = BookingService(db)
    slots = service.get_slots_of_tutors(user["id"])
    return {"slots": slots or []}


@router.post("/api/student/book")
async def book_slot(req: BookRequest, request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        service = BookingService(db)
        booking = service.create_booking_request(user["id"], req.slot_id, req.note)
        return {"message": "Yêu cầu đặt lịch đã được gửi", "request": booking}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/student/bookings")
def student_bookings(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = BookingService(db)
    bookings = service.get_student_bookings(user["id"])
    return {"bookings": bookings}


@router.delete("/api/student/booking/{req_id}")
def cancel_booking(req_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = BookingService(db)
    service.cancel_booking(user["id"], req_id)
    return {"message": "Đã hủy yêu cầu đặt lịch"}


@router.get("/api/tutor/requests")
def tutor_requests(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = BookingService(db)
    requests = service.tutor_get_requests(user["id"])
    return {"requests": requests}


@router.post("/api/tutor/requests/respond")
def respond_booking(req: TutorRespondBooking, request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "tutor":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    service = BookingService(db)
    try:
        updated_req = service.tutor_respond(user["id"], req.req_id, req.action)
        if updated_req:
            message = "Đã chấp nhận yêu cầu đặt lịch." if req.action == "accept" else "Đã từ chối yêu cầu đặt lịch."
            return {"message": message, "request_id": updated_req.id}
        else:
            raise HTTPException(status_code=404, detail="Yêu cầu không tồn tại.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# ADMIN & COORDINATOR
# =========================

@router.get("/admin/dashboard", response_class=HTMLResponse)
def view_admin(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse("/")
    
    sys = SysManagementService(db)
    
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html", 
        context={
            "user": user, 
            "users": sys.get_all_users()
        }
    )


@router.get("/coordinator/dashboard", response_class=HTMLResponse)
def view_coord(request: Request, db: Session = Depends(get_db)):
    user = get_user_session(request)
    if not user or user.get("role") != "coordinator":
        return RedirectResponse("/")
    
    coord = CoordinationService(db)
    
    return templates.TemplateResponse(
        request=request,
        name="coordinator_dashboard.html", 
        context={
            "user": user, 
            "programs": coord.get_available_programs()
        }
    )


@router.get("/sso", response_class=HTMLResponse)
async def sso_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="hcmut_sso.html"
    )

@router.get("/my-students")
def view_my_students(request: Request, db: Session = Depends(get_db)):
    # 1. Lấy thông tin user từ session
    user = request.session.get("user")
    if not user or user['role'] != 'tutor':
        return RedirectResponse(url="/login")
    booking_service = BookingService(db)
    # 2. Gọi service để lấy danh sách sinh viên đã được chấp nhận (Accepted)
    students = booking_service.get_tutor_students(user["id"])

    return templates.TemplateResponse(
    request=request,
    name="my_students.html",
    context={
        "user": user,
        "students": students
    })