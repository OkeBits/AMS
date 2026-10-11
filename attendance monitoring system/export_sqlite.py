import sqlite3
from pathlib import Path

# Folder containing this Python script and your database files
PROJECT_FOLDER = Path(__file__).resolve().parent

DATABASE_FILES = [
    "rfid_attendance.db",
    "users.db",
    "time_and_date.db",
]

# Keep exported files in a separate folder
BACKUP_FOLDER = PROJECT_FOLDER / "sql_backups"
BACKUP_FOLDER.mkdir(exist_ok=True)

for database_name in DATABASE_FILES:
    database_path = PROJECT_FOLDER / database_name

    if not database_path.exists():
        print(f"SKIPPED: {database_name} was not found.")
        continue

    output_path = BACKUP_FOLDER / (
        database_path.stem + ".sql"
    )

    try:
        with sqlite3.connect(
            f"file:{database_path.as_posix()}?mode=ro",
            uri=True
        ) as connection:
            with output_path.open(
                "w", encoding="utf-8", newline="\n"
            ) as sql_file:
                sql_file.write(
                    f"-- SQLite export of {database_name}\n"
                )
                sql_file.write(
                    "-- Keep this backup private.\n\n"
                )

                for statement in connection.iterdump():
                    sql_file.write(statement + "\n")

        print(f"SUCCESS: {database_name} -> {output_path}")

    except sqlite3.Error as error:
        print(f"ERROR exporting {database_name}: {error}")
    except OSError as error:
        print(f"ERROR writing {output_path}: {error}")

print("\nExport process finished.")