
import sqlite3
from pathlib import Path
from getpass import getpass

import mysql.connector

# All database files should be in this project folder.
PROJECT_FOLDER = Path(__file__).resolve().parent

# SQLite database -> tables to migrate
DATABASE_TABLES = {
    "rfid_attendance.db": ["students", "attendance"],
    "users.db": [
        "users",
        "parent_users",
        "parent_login_history",
    ],
    "time_and_date.db": ["user_time_date"],
}

MYSQL_TABLES = [
    "students",
    "attendance",
    "users",
    "parent_users",
    "parent_login_history",
    "user_time_date",
]


def main():
    password = getpass("Enter your local MySQL root password: ")

    connection = None

    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password=password,
            database="rfid_attendance",
        )

        cursor = connection.cursor()

        print("\nConnected to MySQL successfully.")

        # Refuse to migrate if any destination table has records.
        for table in MYSQL_TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]

            if count > 0:
                print(
                    f"\nSTOPPED: MySQL table '{table}' "
                    f"already contains {count} record(s)."
                )
                print(
                    "No records were imported. Check the database "
                    "before deciding how to continue."
                )
                return

        # Check all SQLite source files before copying anything.
        for database_name in DATABASE_TABLES:
            path = PROJECT_FOLDER / database_name

            if not path.exists():
                raise FileNotFoundError(
                    f"SQLite file not found: {path}"
                )

        copied_counts = {}

        for database_name, tables in DATABASE_TABLES.items():
            sqlite_path = PROJECT_FOLDER / database_name

            # Read from SQLite; do not modify the source database.
            with sqlite3.connect(
                f"{sqlite_path.resolve().as_uri()}?mode=ro",
                uri=True,
            ) as source:
                source.row_factory = sqlite3.Row

                for table in tables:
                    rows = source.execute(
                        f'SELECT * FROM "{table}"'
                    ).fetchall()

                    if not rows:
                        copied_counts[table] = 0
                        print(f"{table}: 0 records")
                        continue

                    columns = rows[0].keys()

                    column_sql = ", ".join(
                        f"`{column}`" for column in columns
                    )
                    placeholders = ", ".join(
                        ["%s"] * len(columns)
                    )

                    sql = (
                        f"INSERT INTO `{table}` "
                        f"({column_sql}) "
                        f"VALUES ({placeholders})"
                    )

                    values = [
                        tuple(row[column] for column in columns)
                        for row in rows
                    ]

                    cursor.executemany(sql, values)
                    copied_counts[table] = len(rows)

                    print(
                        f"{table}: prepared "
                        f"{len(rows)} record(s)"
                    )

        connection.commit()
        print("\nMigration completed successfully!")

        print("\nVerifying MySQL record counts:")
        for table, expected in copied_counts.items():
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            actual = cursor.fetchone()[0]

            print(
                f"{table}: {actual} record(s) "
                f"(source: {expected})"
            )

            if actual != expected:
                print("WARNING: Record counts do not match.")

    except FileNotFoundError as error:
        if connection and connection.is_connected():
            connection.rollback()
        print(f"\nERROR: {error}")

    except (sqlite3.Error, mysql.connector.Error) as error:
        if connection and connection.is_connected():
            connection.rollback()
        print(f"\nDATABASE ERROR: {error}")
        print("The MySQL transaction was rolled back.")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()
        print(f"\nERROR: {error}")
        print("The MySQL transaction was rolled back.")

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\nMySQL connection closed.")


if __name__ == "__main__":
    main()
