```text
tutor_system/
├── app/
│   ├── integration/         # Layer: Integration (Adapters for SSO, Library, DataCore)
│   ├── repositories/        # Layer: Data Access (CRUD operations)
│   ├── domain/              # Layer: Business/Domain (Pure business logic/rules)
│   ├── services/            # Layer: Application/Service (Orchestration)
│   ├── routers/             # Layer: User Interface (API Endpoints & View Controllers)
│   ├── models.py            # Database Entities (SQLAlchemy)
│   ├── database.py          # Database Connection
│   ├── main.py              # App Entry Point
│   └── templates/           # HTML Views (Jinja2)
├── requirements.txt
└── README.md
```
# Create enviroment

`python -m venv venv`
`venv\Scripts\activate`
# Install requirements

`pip install -r requirements.txt`

# Run

First you need to run the script.sql to hard code database (Mysql : 3306)

`uvicorn app.main:app --reload --port 8000`
## Hướng dẫn sử dụng hệ thống Tutor System

### Giới thiệu

Hệ thống được xây dựng dành riêng cho môi trường trường học, vì vậy **không có chức năng đăng ký tài khoản**. Việc xác thực người dùng được thực hiện thông qua hệ thống **SSO (Single Sign-On)** của trường.

<img width="2548" height="1339" alt="image" src="https://github.com/user-attachments/assets/a068b0da-304e-4482-8476-cc4dece21a46" />

---

## 👨‍🎓 Tài khoản sinh viên (Demo)

* **MSSV:** 2310001
* **Mật khẩu:** 2310001

### Chức năng sinh viên

1. **Vào giao diện sinh viên**
   <img width="2506" height="1329" alt="image" src="https://github.com/user-attachments/assets/75017456-de35-43cc-8379-33dd05c8e301" />


2. **Đăng ký chương trình học**
  <img width="2535" height="1339" alt="image" src="https://github.com/user-attachments/assets/0463597a-7755-44dd-a832-e6752ba5db18" />


3. **Tìm kiếm giảng viên**
   <img width="2495" height="1335" alt="image" src="https://github.com/user-attachments/assets/a92240af-11f3-4ffe-a59f-e02b462cc5cc" />


4. **Gửi yêu cầu để được dạy kèm**
   <img width="2498" height="1326" alt="image" src="https://github.com/user-attachments/assets/79c1f3ea-d8a1-4658-bf73-febc836ede1d" />


5. **Xem lịch rảnh của giảng viên**
   <img width="2497" height="1324" alt="image" src="https://github.com/user-attachments/assets/6796e1a6-ae40-483f-b5a9-bd417ea90123" />

6. **Chọn lịch muốn học**
   <img width="2480" height="1300" alt="image" src="https://github.com/user-attachments/assets/9f8c15cc-a373-4c95-8ac7-8328c46b3a5a" />


7. **Sau khi được giảng viên đồng ý**
   → Hệ thống sẽ hiển thị **lịch học chính thức**
   <img width="2488" height="1332" alt="image" src="https://github.com/user-attachments/assets/1cf3d38d-3dc9-47eb-9643-12e1224a69d5" />


---

## 👨‍🏫 Tài khoản giảng viên (Demo)

* **MSSV:** 210001
* **Mật khẩu:** 210001

### Chức năng giảng viên

1. **Vào giao diện giảng viên**
   <img width="2504" height="1335" alt="image" src="https://github.com/user-attachments/assets/7b769fb2-b9bf-422b-8572-cb6b1188bbe4" />


2. **Thiết lập lịch rảnh**

   * Có thể **thêm** hoặc **xóa** lịch
     <img width="2497" height="1337" alt="image" src="https://github.com/user-attachments/assets/6e711bc0-5be0-48e0-aebe-bb55f0c9b2a5" />


3. **Nhận thông báo sinh viên yêu cầu dạy kèm**
   <img width="2461" height="1281" alt="image" src="https://github.com/user-attachments/assets/4ce1a219-6fad-4109-94ea-5750bb272d9a" />


4. **Duyệt hoặc từ chối yêu cầu học**
   <img width="2509" height="1309" alt="image" src="https://github.com/user-attachments/assets/6f08227b-5977-4d9a-98df-ffd48096b016" />

5. **Nhận thông báo yêu cầu đặt lịch**
    <img width="2470" height="1290" alt="image" src="https://github.com/user-attachments/assets/bafd92d1-4640-42cd-9715-f08e6868832e" />

6. **Nhận thông báo lịch học sắp tới**
   <img width="2475" height="1315" alt="image" src="https://github.com/user-attachments/assets/9872460d-18dc-4259-8a63-561c16a37598" />


6. **Xem danh sách sinh viên đang dạy**
   <img width="2520" height="1294" alt="image" src="https://github.com/user-attachments/assets/04fe46ec-7eb9-449a-8571-118c4895aae6" />


---


