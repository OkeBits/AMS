
import sqlite3
from pathlib import Path
from getpass import getpass
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).resolve().parent / "users.db"


def main():
    if not DB_PATH.exists():
        print("ERROR: users.db was not found.")
        return

    username = input("Enter your administrator Gmail: ").strip().lower()
    password = getpass("Enter your CURRENT administrator password: ")

    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT username, password FROM users WHERE lower(username) = ?",
            (username,)
        )
        user = cursor.fetchone()

        if user is None:
            print("ERROR: Administrator account not found. Nothing changed.")
            return

        stored_password = user[1]

        # Stop if this account already has a valid password hash.
        if isinstance(stored_password, str) and (
            stored_password.startswith("scrypt:")
            or stored_password.startswith("pbkdf2:")
        ):
            if check_password_hash(stored_password, password):
                print("This password is already hashed. Nothing changed.")
            else:
                print("ERROR: Password verification failed. Nothing changed.")
            return

        # Verify the current plain-text password before changing anything.
        if stored_password != password:
            print("ERROR: Current password is incorrect. Nothing changed.")
            return

        hashed_password = generate_password_hash(password)

        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed_password, user[0])
        )

        if cursor.rowcount != 1:
            connection.rollback()
            print("ERROR: The password was not updated.")
            return

        connection.commit()

        # Verify that the stored hash matches the original password.
        cursor.execute(
            "SELECT password FROM users WHERE username = ?",
            (user[0],)
        )
        saved_hash = cursor.fetchone()[0]

        if check_password_hash(saved_hash, password):
            print("SUCCESS: Your administrator password is now hashed.")
            print("Your username and password have not changed.")
        else:
            connection.rollback()
            print("ERROR: Verification failed. The change was rolled back.")

    except sqlite3.Error as error:
        connection.rollback()
        print("Database error:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
