-- SQLite export of users.db
-- Keep this backup private.

BEGIN TRANSACTION;
CREATE TABLE parent_login_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_date TEXT NOT NULL,
                login_time TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('Success', 'Failed'))
            );
CREATE TABLE parent_users (
                parent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
INSERT INTO "users" VALUES(6,'kylecatao@gmail.com','072008');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',6);
INSERT INTO "sqlite_sequence" VALUES('parent_users',1);
INSERT INTO "sqlite_sequence" VALUES('parent_login_history',3);
COMMIT;
