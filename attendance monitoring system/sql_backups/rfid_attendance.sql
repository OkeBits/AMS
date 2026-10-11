-- SQLite export of rfid_attendance.db
-- Keep this backup private.

BEGIN TRANSACTION;
CREATE TABLE attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_number TEXT NOT NULL,
            full_name TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            strand TEXT NOT NULL,
            date TEXT NOT NULL,
            time_in TEXT,
            time_out TEXT,
            status TEXT NOT NULL
        );
INSERT INTO "attendance" VALUES(1,'4174799620','Kyle','Grade 12','ICT','2026-10-10','04:28:27 AM',NULL,'Present');
INSERT INTO "attendance" VALUES(2,'4171215620','mark','2nd Year','BSIT','2026-10-10','04:40:29 AM',NULL,'Present');
CREATE TABLE students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            birthday TEXT NOT NULL,
            education_level TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            strand TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            parent_phone TEXT NOT NULL
        );
INSERT INTO "students" VALUES(1,'4174799620','Kyle',18,'2008-07-17','Senior High School','Grade 12','ICT','REMELITA C. ALIPAR','09127107763');
INSERT INTO "students" VALUES(2,'4171215620','mark',18,'2008-06-26','College','2nd Year','BSIT','banguis','09127107763');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('students',2);
INSERT INTO "sqlite_sequence" VALUES('attendance',2);
COMMIT;
