-- SQLite export of time_and_date.db
-- Keep this backup private.

BEGIN TRANSACTION;
CREATE TABLE user_time_date (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            time TEXT NOT NULL,
            date TEXT NOT NULL
        );
INSERT INTO "user_time_date" VALUES(80,'kylecatao@gmail.com','04:26:41 AM','2026-10-10');
INSERT INTO "user_time_date" VALUES(81,'kylecatao@gmail.com','04:35:45 AM','2026-10-10');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('user_time_date',81);
COMMIT;
