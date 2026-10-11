
import sqlite3
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent

DATABASE_FILES = [
    "rfid_attendance.db",
    "users.db",
    "time_and_date.db",
]

for database_name in DATABASE_FILES:
    database_path = PROJECT_FOLDER / database_name

    print(f"\n{'=' * 45}")
    print(f"DATABASE: {database_name}")

    if not database_path.exists():
        print("NOT FOUND")
        continue

    try:
        with sqlite3.connect(
            f"{database_path.as_uri()}?mode=ro",
            uri=True
        ) as connection:
            tables = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()

            if not tables:
                print("No tables found.")

            for (table_name,) in tables:
                columns = connection.execute(
                    f'PRAGMA table_info("{table_name}")'
                ).fetchall()

                count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]

                column_names = [column[1] for column in columns]

                print(f"\nTable: {table_name}")
                print(f"Columns: {', '.join(column_names)}")
                print(f"Records: {count}")

    except sqlite3.Error as error:
        print(f"ERROR: {error}")

print("\nDatabase check finished.")
