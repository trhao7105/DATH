-- ============================
--  DELETE + RECREATE DATABASE
-- ============================
DROP DATABASE IF EXISTS tutor_system;
CREATE DATABASE tutor_system;
USE tutor_system;

-- ============================
--  TABLE: USERS
-- ============================
CREATE TABLE users (
    id INT PRIMARY KEY,
    mssv VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    ho_ten VARCHAR(255) NOT NULL,
    role ENUM('student', 'tutor', 'admin', 'coordinator') NOT NULL
);

-- ============================
--  TABLE: PROGRAMS
-- ============================
CREATE TABLE programs (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    semester VARCHAR(255) NOT NULL,
    status ENUM('open','closed') NOT NULL
);

-- ============================
--  TABLE: REGISTRATIONS
-- ============================
CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    program_id INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (program_id) REFERENCES programs(id)
);

-- ============================
--  TABLE: TIME SLOTS
-- ============================
CREATE TABLE time_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tutor_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    is_booked TINYINT(1) DEFAULT 0,
    FOREIGN KEY (tutor_id) REFERENCES users(id)
);

-- ============================
--  TABLE: APPOINTMENTS
-- ============================
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    slot_id INT NOT NULL,
    status ENUM('pending','confirmed','cancelled') DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(id)
);

-- ============================
--  TABLE: BOOKING REQUESTS
-- ============================
CREATE TABLE booking_requests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    tutor_id INT NOT NULL,
    slot_id INT NOT NULL,
    note TEXT,
    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (tutor_id) REFERENCES users(id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(id)
);

-- ============================
--  INSERT USERS
-- ============================
INSERT INTO users (id, mssv, password, ho_ten, role) VALUES 
(1, '2310001', '2310001', 'Nguyễn Văn An (Student)', 'student'),
(2, '2310002', '2310002', 'Trần Thị Bình (Student)', 'student'),
(3, '2310003', '2310003', 'Lê Văn Cường (Student)', 'student'),

(4, '2010001', '2010001', 'Phạm Minh Đức (Tutor)', 'tutor'),
(5, '2010002', '2010002', 'Hoàng Thị Dung (Tutor)', 'tutor'),

(6, 'admin', 'admin', 'System Administrator', 'admin'),
(7, 'coord', 'coord', 'Phòng Đào Tạo', 'coordinator');

-- ============================
--  INSERT PROGRAMS
-- ============================
INSERT INTO programs (id, name, semester, status) VALUES 
(1, 'Chương trình tutor HK2', 'HK2 2025-2026', 'open'),
(2, 'Chương trình tutor HK1', 'HK1 2025-2026', 'closed'),
(3, 'Chương trình tutor HK2', 'HK2 2024-2025', 'closed');

-- ============================
--  INSERT REGISTRATIONS
-- ============================
INSERT INTO registrations (student_id, program_id) VALUES 
(1, 1),
(1, 2),
(2, 1),
(3, 3);

-- ============================
--  INSERT TIME SLOTS
-- ============================
INSERT INTO time_slots (id, tutor_id, start_time, end_time, is_booked) VALUES 
(1, 4, '2025-12-01 08:00:00', '2025-12-01 09:00:00', 1),
(2, 4, '2025-12-01 09:00:00', '2025-12-01 10:00:00', 0),
(3, 4, '2025-12-02 14:00:00', '2025-12-02 15:00:00', 0),

(4, 5, '2025-12-03 08:00:00', '2025-12-03 09:00:00', 0),
(5, 5, '2025-12-03 10:00:00', '2025-12-03 11:00:00', 1);

-- ============================
--  INSERT APPOINTMENTS
-- ============================
INSERT INTO appointments (student_id, slot_id, status) VALUES 
(1, 1, 'confirmed'),
(2, 5, 'pending');

