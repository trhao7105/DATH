from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.repositories.repos import UserRepository, ScheduleRepository, ProgramRepository, SystemRepository, BookingRepository
from app.models import TutorRequest, User, RequestStatus, BookingRequest, TimeSlot
from app.integration.adapters import SSOAdapter
from app.domain.rules import ScheduleDomain
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.sso_adapter = SSOAdapter()

    def login(self, mssv: str, password: str):
        if not self.sso_adapter.authenticate(mssv, password):
            return None
        user = self.user_repo.get_by_mssv(mssv)
        if user and user.password == password:
            return user
        return None

class ScheduleService:
    def __init__(self, db: Session):
        self.schedule_repo = ScheduleRepository(db)
        self.domain = ScheduleDomain()

    def _parse_time(self, time_str: str) -> datetime:
        """
        Giải pháp tối ưu: Lấy chính xác mặt chữ thời gian (bỏ qua mọi múi giờ ngầm định)
        Cắt lấy chính xác 19 ký tự đầu tiên (YYYY-MM-DDTHH:MM:SS)
        """
        clean_str = time_str[:19]
        return datetime.fromisoformat(clean_str)

    def get_tutor_schedule(self, tutor_id: int):
        return self.schedule_repo.get_slots_by_tutor(tutor_id)

    def add_slot(self, tutor_id: int, start_time_str: str):
        # Dùng hàm _parse_time thông minh vừa tạo
        start_time = self._parse_time(start_time_str)
        end_time = self.domain.validate_slot_time(start_time)
        return self.schedule_repo.create_slot(tutor_id, start_time, end_time)

    def remove_slot(self, tutor_id: int, start_time_str: str):
        # Dùng hàm _parse_time để lúc xóa cũng khớp 100% với lúc thêm
        start_time = self._parse_time(start_time_str)
        self.schedule_repo.delete_slot(tutor_id, start_time)

    def book_appointment(self, student_id: int, slot_id: int):
        slot = self.schedule_repo.get_slot_by_id(slot_id)
        if not slot or slot.is_booked:
            raise Exception("Khung giờ đã được đặt hoặc không tồn tại")
        self.schedule_repo.mark_booked(slot_id)
        self.schedule_repo.create_appointment(student_id, slot_id)

class CoordinationService:
    def __init__(self, db: Session):
        self.prog_repo = ProgramRepository(db)

    def get_available_programs(self):
        return self.prog_repo.get_open_programs()

    def register_student_to_program(self, student_id: int, program_id: int):
        return self.prog_repo.register_student(student_id, program_id)
    
    def create_new_program(self, name: str, semester: str):
        return self.prog_repo.create_program(name, semester)

class SysManagementService:
    def __init__(self, db: Session):
        self.sys_repo = SystemRepository(db)
        self.user_repo = UserRepository(db)

    def get_health(self): return {"status": "ok"}
    def get_all_users(self): return self.user_repo.get_all()
    
class MatchingService:
    def __init__(self, db: Session):
        self.db = db

    def search_tutors(self):
        return self.db.query(User).filter(User.role == "tutor").all()

    def select_tutor(self, student_id: int, tutor_id: int) -> bool:
        # Kiểm tra tutor tồn tại
        tutor = self.db.query(User).filter(User.id == tutor_id, User.role == "tutor").first()
        if not tutor:
            return False

        # Kiểm tra đã gửi pending chưa
        exists = self.db.query(TutorRequest).filter(
            TutorRequest.student_id == student_id,
            TutorRequest.tutor_id == tutor_id,
            TutorRequest.status == RequestStatus.pending
        ).first()

        if exists:
            return False

        # Tạo yêu cầu mới
        try:
            request = TutorRequest(
                student_id=student_id,
                tutor_id=tutor_id,
                status=RequestStatus.pending
            )
            self.db.add(request)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def get_pending_requests_for_tutor(self, tutor_id: int):
        return (self.db.query(TutorRequest)
                .filter(TutorRequest.tutor_id == tutor_id,
                        TutorRequest.status == RequestStatus.pending)
                .join(User, User.id == TutorRequest.student_id)
                .all())

    def respond_to_request(self, request_id: int, tutor_id: int, accept: bool, reason: str = None) -> bool:
        request = self.db.query(TutorRequest).filter(
            TutorRequest.id == request_id,
            TutorRequest.tutor_id == tutor_id,
            TutorRequest.status == RequestStatus.pending
        ).first()

        if not request:
            return False

        if accept:
            request.status = RequestStatus.accepted
        else:
            request.status = RequestStatus.rejected
            request.reject_reason = reason or "Không có lý do cụ thể"

        # FIX: Đồng bộ giờ VN (UTC+7) naive cho trường responded_at
        vn_tz = timezone(timedelta(hours=7))
        request.responded_at = datetime.now(vn_tz).replace(tzinfo=None)
        
        self.db.commit()
        return True
    
class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.schedule_repo = ScheduleRepository(db)

    def get_slots_of_tutors(self, student_id):
        # Tìm tutors đã accepted ở bảng TutorRequest
        from app.models import TutorRequest, RequestStatus, TimeSlot, User

        # FIX: Đồng bộ lấy giờ VN thay vì giờ local của server (tránh trễ 7 tiếng)
        vn_tz = timezone(timedelta(hours=7))
        current_time = datetime.now(vn_tz).replace(tzinfo=None)
        
        accepted_tutor_ids = (
            self.db.query(TutorRequest.tutor_id)
            .filter(
                TutorRequest.student_id == student_id,
                TutorRequest.status == RequestStatus.accepted
            )
            .subquery()
        )

        results = (
            self.db.query(TimeSlot, User.ho_ten)
            .join(User, TimeSlot.tutor_id == User.id)
            .filter(TimeSlot.tutor_id.in_(accepted_tutor_ids))
            .filter(TimeSlot.is_booked == False)
            .filter(TimeSlot.start_time > current_time)
            .order_by(TimeSlot.start_time.asc())
            .all()
        )

        formatted_slots = [
            {
                "id": slot.id,
                "tutor_id": slot.tutor_id,
                "tutor_name": tutor_name,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "is_booked": slot.is_booked,
            }
            for slot, tutor_name in results
        ]

        return formatted_slots

    def create_booking_request(self, student_id, slot_id, note=None):
        slot = self.schedule_repo.get_slot_by_id(slot_id)
        if not slot:
            raise HTTPException(
                status_code=400,
                detail="Slot không tồn tại"
            )
        
        existing_slot_request = (
            self.db.query(BookingRequest)
            .filter(BookingRequest.slot_id == slot_id)
            .filter(BookingRequest.status == "pending")
            .first()
        )
        if existing_slot_request:
            raise HTTPException(
                status_code=400,
                detail="Slot này đang có yêu cầu đặt lịch khác chờ phản hồi."
            )

        if slot.is_booked:
            raise HTTPException(
            status_code=400,
            detail="Slot này đã được đặt. Vui lòng chọn slot khác."
        )

        try:
            return self.booking_repo.create_request(
                student_id=student_id,
                tutor_id=slot.tutor_id,
                slot_id=slot_id,
                note=note
            )
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Slot này đang có yêu cầu đặt lịch khác chờ phản hồi hoặc đã được đặt."
            )
        except Exception as e:
            self.db.rollback()
            raise e

    def get_student_bookings(self, student_id):
        return self.booking_repo.get_by_student(student_id)

    def cancel_booking(self, student_id, req_id):
        self.booking_repo.delete_request(req_id, student_id)

    def tutor_get_pending_requests(self, tutor_id):
        return self.booking_repo.get_pending_requests(tutor_id)
    
    def tutor_get_upcoming_sessions(self, tutor_id):
        return self.booking_repo.get_upcoming_sessions(tutor_id)

    def tutor_get_requests(self, tutor_id):
        return self.booking_repo.get_by_tutor(tutor_id)

    def tutor_respond(self, tutor_id, req_id, action: str):
        req = self.booking_repo.get_by_id(req_id)
        if not req or req.tutor_id != tutor_id:
            raise Exception("Yêu cầu không tồn tại hoặc không thuộc về bạn.")
        if req.status != 'pending':
            raise Exception(f"Yêu cầu đã ở trạng thái {req.status} rồi.")
        
        if action == 'accept':
            # 1. Cập nhật trạng thái request thành accepted
            updated_req = self.booking_repo.update_status(req_id, "accepted")
            
            # 2. Quan trọng: Đánh dấu Slot này đã có người đặt để ẩn khỏi người khác
            slot = self.schedule_repo.get_slot_by_id(req.slot_id)
            if slot:
                self.schedule_repo.mark_booked(slot.id) # Gọi hàm đánh dấu đã đặt
                
            return updated_req
            
        elif action == 'reject':
            updated_req = self.booking_repo.update_status(req_id, "rejected")
            return updated_req
        
        else:
            raise Exception("Hành động không hợp lệ.")