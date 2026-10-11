import os
import re
import json
import hashlib
import secrets
from datetime import datetime
from string import Formatter
from urllib.parse import urlsplit

import mysql.connector
import requests
from mysql.connector import Error, IntegrityError

from flask import (
    Flask, jsonify, request, redirect, session, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash

# =========================================================
# FLASK SETUP
# =========================================================

app = Flask(__name__)

# Set FLASK_SECRET_KEY in your environment before deployment.
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"
)

# =========================================================
# MYSQL CONFIGURATION
# =========================================================

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": "rfid_attendance",
}

PHILSMS_SEND_URL = os.getenv(
    "PHILSMS_API_URL",
    "https://app.philsms.com/api/v3/sms/send",
)
PHILSMS_ALLOWED_SEND_URLS = {
    "https://app.philsms.com/api/v3/sms/send",
    "https://dashboard.philsms.com/api/v3/sms/send",
}
SCHOOL_TIME_IN = "7:00 AM"
DEFAULT_TIME_IN_TEMPLATE = (
    "Dear Parent/Guardian, please be informed that {student_name} arrived "
    "at school on {date} at {time}. Student details: {grade} {strand}. "
    "Thank you."
)
DEFAULT_TIME_OUT_TEMPLATE = (
    "Dear Parent/Guardian, please be informed that {student_name} departed "
    "from school on {date} at {time}. Student details: {grade} {strand}. "
    "Thank you."
)
PREVIOUS_TIME_IN_TEMPLATE = (
    "Good day! {student_name} arrived at school at {time} on {date}. "
    "Status: {grade} {strand}."
)
PREVIOUS_TIME_OUT_TEMPLATE = (
    "Good day! {student_name} left school at {time} on {date}. "
    "Status: {grade} {strand}."
)
LEGACY_TIME_IN_TEMPLATE = (
    "Attendance notice: {student_name} timed in at {time} on {date}."
)
LEGACY_TIME_OUT_TEMPLATE = (
    "Attendance notice: {student_name} timed out at {time} on {date}."
)
SMS_TEMPLATE_FIELDS = {
    "student_name", "date", "time", "grade", "strand"
}


def get_mysql_connection():
    """Connect to the rfid_attendance MySQL database."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def initialize_mysql_database():
    """Create the app database and required tables if they do not exist."""
    server_config = {
        key: value
        for key, value in MYSQL_CONFIG.items()
        if key != "database"
    }

    connection = mysql.connector.connect(**server_config)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS `rfid_attendance` "
            "CHARACTER SET utf8mb4"
        )
    finally:
        connection.close()

    table_statements = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(254) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS students (
            student_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            rfid_number VARCHAR(64) NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            birthday VARCHAR(32) NOT NULL,
            education_level VARCHAR(64) NOT NULL,
            grade_level VARCHAR(64) NOT NULL,
            strand VARCHAR(128) NOT NULL,
            parent_name VARCHAR(255) NOT NULL,
            parent_phone VARCHAR(32) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            rfid_number VARCHAR(64) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            grade_level VARCHAR(64) NOT NULL,
            strand VARCHAR(128) NOT NULL,
            `date` VARCHAR(10) NOT NULL,
            time_in VARCHAR(32),
            time_out VARCHAR(32),
            status VARCHAR(32) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS user_time_date (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            `user` VARCHAR(254) NOT NULL,
            `time` VARCHAR(32) NOT NULL,
            `date` VARCHAR(10) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS parent_users (
            parent_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(254) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            phone_number VARCHAR(32) NOT NULL,
            is_active TINYINT NOT NULL DEFAULT 1
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS parent_login_history (
            history_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(254) NOT NULL,
            login_date VARCHAR(10) NOT NULL,
            login_time VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS sms_settings (
            id TINYINT NOT NULL PRIMARY KEY,
            api_token TEXT NOT NULL,
            sender_id VARCHAR(11) NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            notify_time_in BOOLEAN NOT NULL DEFAULT TRUE,
            notify_time_out BOOLEAN NOT NULL DEFAULT TRUE,
            time_in_template TEXT NOT NULL,
            time_out_template TEXT NOT NULL,
            api_url VARCHAR(255) NOT NULL DEFAULT
                'https://app.philsms.com/api/v3/sms/send'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS sms_send_requests (
            ticket_hash CHAR(64) NOT NULL PRIMARY KEY,
            rfid_number VARCHAR(64) NOT NULL,
            attendance_date VARCHAR(10) NOT NULL,
            event_type VARCHAR(16) NOT NULL,
            attendance_time VARCHAR(32) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sms_send_requests_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    )

    connection = get_mysql_connection()
    try:
        cursor = connection.cursor()
        for statement in table_statements:
            cursor.execute(statement)
        cursor.execute("SHOW COLUMNS FROM sms_settings")
        sms_settings_columns = {
            column[0] for column in cursor.fetchall()
        }
        if "time_in_template" not in sms_settings_columns:
            cursor.execute("""
                ALTER TABLE sms_settings
                ADD COLUMN time_in_template TEXT NULL
            """)
        if "time_out_template" not in sms_settings_columns:
            cursor.execute("""
                ALTER TABLE sms_settings
                ADD COLUMN time_out_template TEXT NULL
            """)
        if "api_url" not in sms_settings_columns:
            cursor.execute("""
                ALTER TABLE sms_settings
                ADD COLUMN api_url VARCHAR(255) NOT NULL DEFAULT
                    'https://app.philsms.com/api/v3/sms/send'
            """)
        cursor.execute("""
            INSERT IGNORE INTO sms_settings (
                id, api_token, sender_id, enabled,
                notify_time_in, notify_time_out,
                time_in_template, time_out_template
            )
            VALUES (%s, '', 'PhilSMS', FALSE, TRUE, TRUE, %s, %s)
        """, (1, DEFAULT_TIME_IN_TEMPLATE, DEFAULT_TIME_OUT_TEMPLATE))
        cursor.execute("""
            UPDATE sms_settings
            SET time_in_template = %s
            WHERE id = 1 AND (time_in_template IS NULL OR time_in_template = '')
        """, (DEFAULT_TIME_IN_TEMPLATE,))
        cursor.execute("""
            UPDATE sms_settings
            SET time_out_template = %s
            WHERE id = 1 AND (time_out_template IS NULL OR time_out_template = '')
        """, (DEFAULT_TIME_OUT_TEMPLATE,))
        cursor.execute("""
            UPDATE sms_settings
            SET time_in_template = %s
            WHERE id = 1 AND time_in_template = %s
        """, (DEFAULT_TIME_IN_TEMPLATE, LEGACY_TIME_IN_TEMPLATE))
        cursor.execute("""
            UPDATE sms_settings
            SET time_out_template = %s
            WHERE id = 1 AND time_out_template = %s
        """, (DEFAULT_TIME_OUT_TEMPLATE, LEGACY_TIME_OUT_TEMPLATE))
        cursor.execute("""
            UPDATE sms_settings
            SET time_in_template = %s
            WHERE id = 1 AND time_in_template = %s
        """, (DEFAULT_TIME_IN_TEMPLATE, PREVIOUS_TIME_IN_TEMPLATE))
        cursor.execute("""
            UPDATE sms_settings
            SET time_out_template = %s
            WHERE id = 1 AND time_out_template = %s
        """, (DEFAULT_TIME_OUT_TEMPLATE, PREVIOUS_TIME_OUT_TEMPLATE))
        connection.commit()
    finally:
        connection.close()


def get_mysql_cursor(connection):
    """Return database rows as dictionaries."""
    return connection.cursor(dictionary=True)


def create_sms_send_ticket(cursor, rfid_number, attendance_date, event, time):
    """Create a short-lived, single-use token for a manual SMS action."""
    ticket = secrets.token_urlsafe(32)
    ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
    cursor.execute("""
        DELETE FROM sms_send_requests
        WHERE created_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE)
    """)
    cursor.execute("""
        INSERT INTO sms_send_requests (
            ticket_hash, rfid_number, attendance_date, event_type,
            attendance_time
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        ticket_hash,
        rfid_number,
        attendance_date,
        event,
        time,
    ))
    return ticket


def password_matches(stored_password, entered_password):
    """
    Support existing plaintext passwords temporarily and hashed passwords.
    A successful login will upgrade an old plaintext password to a hash.
    """
    if not stored_password:
        return False

    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        try:
            return check_password_hash(stored_password, entered_password)
        except (ValueError, TypeError):
            return False

    return stored_password == entered_password


def is_admin_logged_in():
    return bool(session.get("username"))


def normalize_philippines_phone(phone_number):
    """Format a Philippine mobile number as 639XXXXXXXXX for PhilSMS."""
    digits = re.sub(r"\D", "", phone_number)
    if len(digits) == 11 and digits.startswith("09"):
        return "63" + digits[1:]
    if len(digits) == 12 and digits.startswith("639"):
        return digits
    if len(digits) == 10 and digits.startswith("9"):
        return "63" + digits
    raise ValueError("Parent phone must be a valid Philippine mobile number.")


def validate_sms_template(template):
    if not isinstance(template, str) or not template.strip():
        raise ValueError("Both SMS message templates are required.")
    if len(template) > 1000:
        raise ValueError("SMS message templates must be 1,000 characters or fewer.")
    try:
        parts = list(Formatter().parse(template))
    except ValueError as error:
        raise ValueError("A message template contains unmatched braces.") from error
    if any(
        field_name not in SMS_TEMPLATE_FIELDS or conversion or format_spec
        for _, field_name, format_spec, conversion in parts
        if field_name is not None
    ):
        allowed = ", ".join(
            "{" + field + "}" for field in sorted(SMS_TEMPLATE_FIELDS)
        )
        raise ValueError(f"Use only these template placeholders: {allowed}.")
    return template.strip()


def _send_philsms_message_once(
    api_token, sender_id, recipient, message, api_url=PHILSMS_SEND_URL
):
    """Send a single SMS using the PhilSMS v3 API."""
    if api_url not in PHILSMS_ALLOWED_SEND_URLS:
        raise RuntimeError("Choose a valid PhilSMS API endpoint in Settings.")

    payload = {
        "recipient": recipient,
        "sender_id": sender_id,
        "type": "plain",
        "message": message,
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
            timeout=15,
        )
        response.raise_for_status()
        response_body = response.text
    except requests.HTTPError as error:
        status_code = (
            error.response.status_code if error.response is not None else 0
        )
        response_body = (
            error.response.text[:4096] if error.response is not None else ""
        )
        firewall_signature_blocked = (
            "blocked access based on your browser's signature"
            in response_body.lower()
        )
        try:
            error_payload = json.loads(response_body)
        except json.JSONDecodeError:
            error_payload = None
        detail = ""
        if firewall_signature_blocked:
            detail = "The site owner blocked this API client's request signature."
        elif isinstance(error_payload, dict):
            for key in ("message", "error", "detail", "errors"):
                if error_payload.get(key):
                    detail = str(error_payload[key])
                    break
        elif response_body and not response_body.lstrip().startswith("<"):
            detail = response_body.strip()
        detail = detail.replace(api_token, "[redacted]")[:400]
        endpoint_host = urlsplit(api_url).hostname or "configured endpoint"
        message = f"PhilSMS at {endpoint_host} returned HTTP {status_code}"
        if detail:
            message += f": {detail}"
        if status_code == 403:
            message += (
                ". Check that the API token is active and belongs to this "
                "PhilSMS account, the sender ID is approved for that account, "
                "and API sending is enabled in your PhilSMS dashboard."
            )
        else:
            message += "."
        raise RuntimeError(message) from error
    except requests.RequestException as error:
        raise RuntimeError("Could not connect to PhilSMS.") from error

    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise RuntimeError("PhilSMS returned an invalid response.") from error

    if isinstance(result, dict) and (
        result.get("success") is False
        or str(result.get("status", "")).lower() in {"error", "failed"}
    ):
        raise RuntimeError("PhilSMS rejected the SMS request.")


def send_philsms_message(
    api_token, sender_id, recipient, message, api_url=PHILSMS_SEND_URL
):
    """Retry on PhilSMS's alternate host only after an explicit HTTP 403."""
    if api_url not in PHILSMS_ALLOWED_SEND_URLS:
        raise RuntimeError("Choose a valid PhilSMS API endpoint in Settings.")

    endpoints = [api_url] + sorted(PHILSMS_ALLOWED_SEND_URLS - {api_url})
    denied = []
    for endpoint in endpoints:
        try:
            _send_philsms_message_once(
                api_token, sender_id, recipient, message, endpoint
            )
            return endpoint
        except RuntimeError as error:
            error_message = str(error)
            if "returned HTTP 403" not in error_message:
                raise
            denied.append(error_message)

    if any("request signature" in error.lower() for error in denied):
        raise RuntimeError(
            "PhilSMS's firewall blocked this application's API request on "
            "both supported endpoints. The SMS API did not validate or "
            "process the message, so changing the token or Sender ID will "
            "not fix this specific error. Contact PhilSMS support and ask "
            "them to allow server-to-server API requests from your network "
            "or provide the correct API endpoint."
        )
    raise RuntimeError(
        "PhilSMS returned HTTP 403 from both supported API endpoints. "
        + " | ".join(denied)
        + " Check the active API token, approved Sender ID, and API access "
        "in your PhilSMS account."
    )


def render_attendance_sms(student, event, attendance_date, attendance_time, template):
    """Fill the configured template for one attendance event."""
    if not template:
        template = (
            DEFAULT_TIME_IN_TEMPLATE
            if event == "time_in"
            else DEFAULT_TIME_OUT_TEMPLATE
        )
    message_values = {
        "student_name": student.get("full_name") or "Student",
        "date": attendance_date or "date unavailable",
        "time": attendance_time or "time unavailable",
        "grade": student.get("grade_level") or "",
        "strand": student.get("strand") or "",
    }
    try:
        message = template.format_map(message_values)
    except (KeyError, ValueError) as error:
        app.logger.exception("Could not render attendance SMS template")
        raise RuntimeError("The saved attendance SMS template is invalid.") from error

    if re.search(r"\bundefined\b", message, re.IGNORECASE):
        app.logger.warning(
            "SMS template for %s contained an undefined value; using default.",
            event,
        )
        default_template = (
            DEFAULT_TIME_IN_TEMPLATE
            if event == "time_in"
            else DEFAULT_TIME_OUT_TEMPLATE
        )
        message = default_template.format_map(message_values)
    return message


def send_attendance_sms(
    student, event, attendance_date, attendance_time, message_override=None
):
    """Send an enabled attendance notification without undoing attendance."""
    connection = None
    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)
        cursor.execute("""
            SELECT api_token, sender_id, api_url, enabled,
                   notify_time_in, notify_time_out,
                   time_in_template, time_out_template
            FROM sms_settings
            WHERE id = 1
        """)
        settings = cursor.fetchone()

        if not settings or not settings["enabled"]:
            return {"status": "disabled", "message": "SMS notifications are off."}

        event_setting = (
            "notify_time_in" if event == "time_in" else "notify_time_out"
        )
        if not settings[event_setting]:
            return {
                "status": "disabled",
                "message": "SMS is disabled for this attendance event.",
            }
        if not settings["api_token"]:
            return {
                "status": "failed",
                "message": "Set the PhilSMS API token in Settings.",
            }

        try:
            recipient = normalize_philippines_phone(student["parent_phone"])
        except ValueError as error:
            return {"status": "failed", "message": str(error)}

        if message_override is not None:
            if (
                not isinstance(message_override, str)
                or not message_override.strip()
                or len(message_override) > 1000
            ):
                return {
                    "status": "failed",
                    "message": "Message must be 1–1,000 characters.",
                }
            message = message_override.strip()
        else:
            template = (
                settings["time_in_template"]
                if event == "time_in"
                else settings["time_out_template"]
            )
            message = render_attendance_sms(
                student, event, attendance_date, attendance_time, template
            )

        try:
            used_endpoint = send_philsms_message(
                settings["api_token"],
                settings["sender_id"],
                recipient,
                message,
                settings["api_url"],
            )
        except RuntimeError as error:
            app.logger.warning(
                "PhilSMS attendance notification failed: %s", error
            )
            return {"status": "failed", "message": str(error)}

        if used_endpoint != settings["api_url"]:
            return {
                "status": "sent",
                "sender_id": settings["sender_id"],
                "message": (
                    "Parent SMS sent using the alternate PhilSMS endpoint."
                ),
            }
        return {
            "status": "sent",
            "sender_id": settings["sender_id"],
            "message": "Parent SMS sent.",
        }
    except Error:
        app.logger.exception("Could not load PhilSMS attendance settings")
        return {
            "status": "failed",
            "message": "Could not load SMS settings.",
        }
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/sms/settings", methods=["GET", "POST"])
def sms_settings_api():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Please log in as an administrator."
        }), 401

    connection = None
    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        if request.method == "GET":
            cursor.execute("""
                SELECT api_token, sender_id, api_url, enabled,
                       notify_time_in, notify_time_out,
                       time_in_template, time_out_template
                FROM sms_settings
                WHERE id = 1
            """)
            settings = cursor.fetchone()
            if settings is None:
                raise RuntimeError("PhilSMS settings have not been initialized.")
            return jsonify({
                "success": True,
                "token_configured": bool(settings["api_token"]),
                "sender_id": settings["sender_id"],
                "api_url": settings["api_url"],
                "enabled": bool(settings["enabled"]),
                "notify_time_in": bool(settings["notify_time_in"]),
                "notify_time_out": bool(settings["notify_time_out"]),
                "time_in_template": (
                    settings["time_in_template"] or DEFAULT_TIME_IN_TEMPLATE
                ),
                "time_out_template": (
                    settings["time_out_template"] or DEFAULT_TIME_OUT_TEMPLATE
                ),
            })

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "Invalid PhilSMS settings."
            }), 400

        api_token = data.get("api_token", "")
        sender_id = data.get("sender_id", "")
        api_url = data.get("api_url", PHILSMS_SEND_URL)
        enabled = data.get("enabled")
        notify_time_in = data.get("notify_time_in")
        notify_time_out = data.get("notify_time_out")
        time_in_template = data.get("time_in_template")
        time_out_template = data.get("time_out_template")

        if (
            not isinstance(api_token, str)
            or not isinstance(sender_id, str)
            or not isinstance(api_url, str)
        ):
            return jsonify({
                "success": False,
                "message": "Enter a valid API token, sender ID, and API endpoint."
            }), 400
        api_url = api_url.strip()
        if api_url not in PHILSMS_ALLOWED_SEND_URLS:
            return jsonify({
                "success": False,
                "message": "Choose one of the supported PhilSMS API endpoints."
            }), 400
        sender_id = sender_id.strip()
        if not re.fullmatch(r"[A-Za-z0-9]{1,11}", sender_id):
            return jsonify({
                "success": False,
                "message": "Sender ID must be 1–11 letters or numbers."
            }), 400
        if not all(isinstance(value, bool) for value in (
            enabled, notify_time_in, notify_time_out
        )):
            return jsonify({
                "success": False,
                "message": "Choose valid SMS notification options."
            }), 400
        try:
            time_in_template = validate_sms_template(time_in_template)
            time_out_template = validate_sms_template(time_out_template)
        except ValueError as error:
            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        cursor.execute(
            "SELECT api_token FROM sms_settings WHERE id = 1"
        )
        current_settings = cursor.fetchone()
        if current_settings is None:
            raise RuntimeError("PhilSMS settings have not been initialized.")
        token_to_save = api_token.strip() or current_settings["api_token"]
        if enabled and not token_to_save:
            return jsonify({
                "success": False,
                "message": "Enter your PhilSMS API token before enabling SMS."
            }), 400
        if enabled and not (notify_time_in or notify_time_out):
            return jsonify({
                "success": False,
                "message": "Select at least one attendance event."
            }), 400

        cursor.execute("""
            UPDATE sms_settings
            SET api_token = %s, sender_id = %s, api_url = %s, enabled = %s,
                notify_time_in = %s, notify_time_out = %s,
                time_in_template = %s, time_out_template = %s
            WHERE id = 1
        """, (
            token_to_save,
            sender_id,
            api_url,
            enabled,
            notify_time_in,
            notify_time_out,
            time_in_template,
            time_out_template,
        ))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "PhilSMS settings saved."
        })
    except Error:
        app.logger.exception("PhilSMS settings database error")
        return jsonify({
            "success": False,
            "message": "Unable to access PhilSMS settings."
        }), 500
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/sms/test", methods=["POST"])
def test_philsms_api():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Please log in as an administrator."
        }), 401

    data = request.get_json(silent=True)
    phone_number = data.get("phone_number", "") if isinstance(data, dict) else ""
    if not isinstance(phone_number, str):
        return jsonify({
            "success": False,
            "message": "Enter a valid mobile number."
        }), 400
    try:
        recipient = normalize_philippines_phone(phone_number)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    connection = None
    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)
        cursor.execute("""
            SELECT api_token, sender_id, api_url
            FROM sms_settings
            WHERE id = 1
        """)
        settings = cursor.fetchone()
        if not settings:
            return jsonify({
                "success": False,
                "message": "Save and enable PhilSMS in Settings first."
            }), 400
        if not settings["api_token"]:
            return jsonify({
                "success": False,
                "message": "Set the PhilSMS API token in Settings first."
            }), 400
        used_endpoint = send_philsms_message(
            settings["api_token"],
            settings["sender_id"],
            recipient,
            "PhilSMS test message from the attendance monitoring system.",
            settings["api_url"],
        )
        message = (
            "PhilSMS accepted the test request; delivery to the phone is not "
            "confirmed. Check the SMS logs in your PhilSMS dashboard."
        )
        if used_endpoint != settings["api_url"]:
            message += " The alternate API endpoint was used."
        return jsonify({
            "success": True,
            "message": message
        })
    except RuntimeError as error:
        app.logger.warning("PhilSMS test message failed: %s", error)
        return jsonify({
            "success": False,
            "message": str(error)
        }), 502
    except Error:
        app.logger.exception("PhilSMS test settings database error")
        return jsonify({
            "success": False,
            "message": "Unable to access PhilSMS settings."
        }), 500
    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# PARENT LOGIN PAGE
# =========================================================

@app.route("/parent-login", methods=["GET"])
def parent_login_page():
    return send_from_directory(".", "parent_login.html")


@app.route("/api/parent-login", methods=["POST"])
def parent_login_process():
    data = request.get_json(silent=True) or {}

    parent_name = str(data.get("parent_name") or "").strip()
    phone_number = str(data.get("phone_number") or "").strip()

    if not parent_name or not phone_number:
        return jsonify({
            "success": False,
            "message": "Enter your registered parent name and phone number."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT COUNT(*) AS match_count
            FROM students
            WHERE LOWER(TRIM(parent_name)) = LOWER(TRIM(%s))
              AND TRIM(parent_phone) = TRIM(%s)
        """, (parent_name, phone_number))

        result = cursor.fetchone()
        match_count = result["match_count"]

        if match_count == 0:
            return jsonify({
                "success": False,
                "message": "The details do not match the school's records."
            }), 401

        session.clear()
        session["role"] = "parent"
        session["parent_name"] = parent_name
        session["parent_phone"] = phone_number

        return jsonify({
            "success": True,
            "message": "Parent details verified.",
            "redirect": "/parent-dashboard"
        })

    except Error:
        app.logger.exception("Parent login MySQL error")
        return jsonify({
            "success": False,
            "message": "Unable to verify your details right now."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# PARENT ATTENDANCE API
# =========================================================

@app.route("/api/parent-attendance", methods=["GET"])
def get_parent_attendance():
    if session.get("role") != "parent":
        return jsonify({
            "success": False,
            "message": "Please log in as a parent."
        }), 401

    parent_phone = session.get("parent_phone")

    if not parent_phone:
        return jsonify({
            "success": False,
            "message": "This parent account has no linked phone number."
        }), 403

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT
                s.rfid_number,
                s.full_name,
                s.education_level,
                s.grade_level,
                s.strand,
                a.date,
                a.time_in,
                a.time_out,
                a.status
            FROM students AS s
            INNER JOIN attendance AS a
                ON a.rfid_number = s.rfid_number
            WHERE s.parent_phone = %s
            ORDER BY a.date DESC, a.attendance_id DESC
            LIMIT 100
        """, (parent_phone,))

        records = cursor.fetchall()

        return jsonify({
            "success": True,
            "history": records
        })

    except Error:
        app.logger.exception("Parent attendance MySQL error")
        return jsonify({
            "success": False,
            "message": "Unable to load attendance records."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/parent-logout", methods=["POST"])
def parent_logout():
    session.clear()
    return jsonify({
        "success": True,
        "redirect": "/parent-login"
    })


@app.route("/parent-dashboard", methods=["GET"])
def parent_dashboard_page():
    if session.get("role") != "parent":
        return redirect("/parent-login")

    return send_from_directory(".", "parent_dashboard.html")


@app.route("/parent_dashboard.css")
def parent_dashboard_css():
    return send_from_directory(".", "parent_dashboard.css")


@app.route("/parent_login.css")
def parent_login_css():
    return send_from_directory(".", "parent_login.css")


# =========================================================
# LOGIN PAGE AND IMAGES
# =========================================================

@app.route("/")
def login_page():
    return send_from_directory(".", "login.html")


@app.route("/login", methods=["GET"])
def login_get():
    return send_from_directory(".", "login.html")


@app.route("/school-logo.png")
def school_logo():
    return send_from_directory(".", "school-logo.png")


@app.route("/login-background.jpg")
def login_background():
    return send_from_directory(".", "login-background.jpg")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login_process():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No login information was received."
        }), 400

    gmail = str(data.get("username") or "").strip().lower()
    password = data.get("password", "")

    if not isinstance(password, str):
        return jsonify({
            "success": False,
            "message": "Invalid password."
        }), 400

    gmail_pattern = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"

    if not re.fullmatch(gmail_pattern, gmail):
        return jsonify({
            "success": False,
            "message": "Please enter a valid Gmail address ending with @gmail.com."
        }), 400

    # Keep this validation only if your existing login page requires 6 digits.
    if not re.fullmatch(r"[0-9]{6}", password):
        return jsonify({
            "success": False,
            "message": "Password must contain exactly 6 digits."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT id, username, password
            FROM users
            WHERE username = %s
            LIMIT 1
        """, (gmail,))

        user = cursor.fetchone()

        if user is None:
            return jsonify({
                "success": False,
                "message": "This Gmail address is not registered."
            }), 401

        if not password_matches(user["password"], password):
            return jsonify({
                "success": False,
                "message": "Incorrect password."
            }), 401

        # Upgrade an old plaintext password after successful login.
        if not user["password"].startswith(("pbkdf2:", "scrypt:")):
            cursor.execute("""
                UPDATE users
                SET password = %s
                WHERE id = %s
            """, (
                generate_password_hash(password),
                user["id"]
            ))
            connection.commit()

        session.clear()
        session["username"] = user["username"]
        session["role"] = "admin"

        now = datetime.now()

        cursor.execute("""
            INSERT INTO user_time_date (`user`, `time`, `date`)
            VALUES (%s, %s, %s)
        """, (
            user["username"],
            now.strftime("%I:%M:%S %p"),
            now.strftime("%Y-%m-%d")
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "redirect": "/dashboard"
        })

    except Error:
        app.logger.exception("Admin login MySQL error")
        return jsonify({
            "success": False,
            "message": "Unable to log in because of a database error."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# REGISTRATION
# =========================================================

@app.route("/register", methods=["GET"])
def register_page():
    return send_from_directory(".", "register.html")


@app.route("/register", methods=["POST"])
def register_process():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No registration information was received."
        }), 400

    gmail = str(data.get("username") or "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not re.fullmatch(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", gmail):
        return jsonify({
            "success": False,
            "message": "Please use a valid Gmail address ending with @gmail.com."
        }), 400

    if not isinstance(password, str) or not re.fullmatch(r"[0-9]{6}", password):
        return jsonify({
            "success": False,
            "message": "Password must contain exactly 6 digits."
        }), 400

    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (username, password)
            VALUES (%s, %s)
        """, (
            gmail,
            generate_password_hash(password)
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful."
        }), 201

    except IntegrityError:
        return jsonify({
            "success": False,
            "message": "This Gmail address is already registered."
        }), 400

    except Error:
        app.logger.exception("Registration MySQL error")
        return jsonify({
            "success": False,
            "message": "Unable to register because of a database error."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# ADD STUDENT
# =========================================================

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "No valid student information was received."
        }), 400

    rfid_number = str(data.get("rfid_number") or "").strip()
    full_name = str(data.get("full_name") or "").strip()
    birthday = str(data.get("birthday") or "").strip()
    education_level = "Senior High School"
    grade_level = str(data.get("grade_level") or "").strip()
    strand = str(data.get("strand") or "").strip()
    parent_name = str(data.get("parent_name") or "").strip()
    parent_phone = str(data.get("parent_phone") or "").strip()
    age_value = data.get("age")

    if (
        not all([
            rfid_number, full_name, birthday, education_level,
            grade_level, strand, parent_name, parent_phone
        ])
        or age_value is None
        or str(age_value).strip() == ""
    ):
        return jsonify({
            "success": False,
            "message": "Please complete all student information."
        }), 400

    try:
        age = int(age_value)
        if age <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Please enter a valid age."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO students (
                rfid_number, full_name, age, birthday,
                education_level, grade_level, strand,
                parent_name, parent_phone
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rfid_number, full_name, age, birthday,
            education_level, grade_level, strand,
            parent_name, parent_phone
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Student successfully saved!"
        }), 201

    except IntegrityError:
        return jsonify({
            "success": False,
            "message": "This RFID number is already registered."
        }), 400

    except Error:
        app.logger.exception("Add student MySQL error")
        return jsonify({
            "success": False,
            "message": "Database error while saving student."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# GET STUDENT LIST
# =========================================================

@app.route("/api/students", methods=["GET"])
def get_students():
    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT
                student_id, rfid_number, full_name, age,
                birthday, education_level, grade_level,
                strand, parent_name, parent_phone
            FROM students
            ORDER BY student_id DESC
        """)

        return jsonify(cursor.fetchall())

    except Error:
        app.logger.exception("Get students MySQL error") 
        return jsonify({
            "success": False,
            "message": "Could not load students."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()
# =========================================================
# RFID SCAN: FIRST SCAN = TIME IN, SECOND SCAN = TIME OUT
# =========================================================

@app.route("/api/scan", methods=["POST"])
def process_rfid_scan():
    data = request.get_json(silent=True) or {}
    rfid_number = str(data.get("rfid") or "").strip()

    if not rfid_number:
        return jsonify({
            "success": False,
            "message": "No RFID number was provided."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT rfid_number, full_name, grade_level, strand,
                   parent_name, parent_phone
            FROM students
            WHERE rfid_number = %s
        """, (rfid_number,))

        student = cursor.fetchone()

        if student is None:
            return jsonify({
                "success": False,
                "message": "This RFID card is not registered."
            }), 404

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%I:%M:%S %p")
        current_time_24 = now.strftime("%H:%M")

        school_time = datetime.strptime(
            SCHOOL_TIME_IN, "%I:%M %p"
        ).strftime("%H:%M")

        attendance_status = (
            "Present" if current_time_24 <= school_time else "Late"
        )

        cursor.execute("""
            SELECT attendance_id, time_in, time_out, status
            FROM attendance
            WHERE rfid_number = %s AND date = %s
            ORDER BY attendance_id DESC
            LIMIT 1
        """, (rfid_number, current_date))

        attendance = cursor.fetchone()

        if attendance is None:
            cursor.execute("""
                INSERT INTO attendance (
                    rfid_number, full_name, grade_level, strand,
                    date, time_in, time_out, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                student["rfid_number"],
                student["full_name"],
                student["grade_level"],
                student["strand"],
                current_date,
                current_time,
                None,
                attendance_status
            ))

            attendance_id = cursor.lastrowid
            connection.commit()
            sms_result = _send_scan_attendance_sms(
                student, "time_in", current_date, current_time
            )

            return jsonify({
                "success": True,
                "message": "Time In recorded successfully.",
                "attendance_id": attendance_id,
                "attendance_status": attendance_status,
                "event": "time_in",
                "sms": sms_result,
                "student": {
                    "rfid_number": student["rfid_number"],
                    "full_name": student["full_name"],
                    "grade_level": student["grade_level"],
                    "strand": student["strand"],
                    "parent_name": student["parent_name"],
                }
            })

        

        if attendance["time_out"] is None:
            cursor.execute("""
                UPDATE attendance
                SET time_out = %s
                WHERE attendance_id = %s
            """, (current_time, attendance["attendance_id"]))

            connection.commit()
            sms_result = _send_scan_attendance_sms(
                student, "time_out", current_date, current_time
            )

            return jsonify({
                "success": True,
                "message": "Time Out recorded successfully.",
                "attendance_id": attendance["attendance_id"],
                "attendance_status": attendance["status"],
                "event": "time_out",
                "sms": sms_result,
                "student": {
                    "rfid_number": student["rfid_number"],
                    "full_name": student["full_name"],
                    "grade_level": student["grade_level"],
                    "strand": student["strand"],
                    "parent_name": student["parent_name"],
                }
            })

        return jsonify({
            "success": False,
            "message": "This student already has a Time In and Time Out for today."
        }), 400

    except Error:
        app.logger.exception("RFID scan MySQL error")
        return jsonify({
            "success": False,
            "message": "An error occurred while processing the RFID scan."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


def _send_scan_attendance_sms(student, event, attendance_date, attendance_time):
    """Attempt automatic parent notification after recording attendance."""
    try:
        return send_attendance_sms(
            student, event, attendance_date, attendance_time
        )
    except Exception:
        app.logger.exception(
            "Unexpected error sending automatic %s parent SMS", event
        )
        return {
            "status": "failed",
            "message": "An unexpected error prevented the parent message from being sent.",
        }


@app.route("/api/scan/send-sms", methods=["POST"])
def send_scan_parent_sms():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Please log in as an administrator.",
        }), 401

    data = request.get_json(silent=True)
    ticket = data.get("ticket") if isinstance(data, dict) else None
    message_override = data.get("message") if isinstance(data, dict) else None
    if not isinstance(ticket, str) or not 40 <= len(ticket) <= 100:
        return jsonify({
            "success": False,
            "message": "This SMS action has expired. Scan the student card again.",
        }), 400
    if message_override is not None and (
        not isinstance(message_override, str)
        or not message_override.strip()
        or len(message_override) > 1000
    ):
        return jsonify({
            "success": False,
            "message": "Message must be 1–1,000 characters.",
        }), 400

    ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
    connection = None
    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)
        cursor.execute("""
            SELECT rfid_number, attendance_date, event_type, attendance_time
            FROM sms_send_requests
            WHERE ticket_hash = %s
              AND created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
            FOR UPDATE
        """, (ticket_hash,))
        send_request = cursor.fetchone()
        if send_request is None:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": (
                    "This SMS action has expired or was already used. "
                    "Scan the student card again."
                ),
            }), 410

        cursor.execute(
            "DELETE FROM sms_send_requests WHERE ticket_hash = %s",
            (ticket_hash,),
        )
        connection.commit()
        cursor.execute("""
            SELECT rfid_number, full_name, grade_level, strand,
                   parent_name, parent_phone
            FROM students
            WHERE rfid_number = %s
        """, (send_request["rfid_number"],))
        student = cursor.fetchone()
    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Could not authorize manual parent SMS")
        return jsonify({
            "success": False,
            "message": "Could not prepare the parent SMS. Please try again.",
        }), 500
    finally:
        if connection and connection.is_connected():
            connection.close()

    if student is None:
        return jsonify({
            "success": False,
            "message": "Student record is no longer available.",
        }), 404

    sms_result = send_attendance_sms(
        student,
        send_request["event_type"],
        send_request["attendance_date"],
        send_request["attendance_time"],
        message_override,
    )
    if sms_result["status"] != "sent":
        status_code = 400 if sms_result["status"] == "disabled" else 502
        return jsonify({
            "success": False,
            "message": sms_result["message"],
        }), status_code

    return jsonify({
        "success": True,
        "message": (
            "PhilSMS accepted the text SMS request. "
            + (
                "The default PhilSMS Sender ID only works for Globe; "
                "register and select your own Sender ID for Smart recipients. "
                if sms_result.get("sender_id") == "PhilSMS"
                else ""
            )
            + "Check PhilSMS SMS logs to confirm delivery to the phone."
        ),
    })


@app.route("/api/attendance/sms-preview", methods=["POST"])
def attendance_sms_preview():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Please log in as an administrator.",
        }), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Invalid SMS request."}), 400

    event = data.get("event")
    if not isinstance(event, str) or event not in {"time_in", "time_out"}:
        return jsonify({
            "success": False,
            "message": "Choose a valid Time In or Time Out event.",
        }), 400

    attendance_id = data.get("attendance_id")
    if isinstance(attendance_id, bool) or not isinstance(attendance_id, int):
        return jsonify({
            "success": False,
            "message": "Select a valid attendance record.",
        }), 400

    connection = None
    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)
        event_column = "time_in" if event == "time_in" else "time_out"
        cursor.execute(f"""
            SELECT a.rfid_number, a.date, a.{event_column} AS attendance_time,
                   s.full_name, s.grade_level, s.strand, s.parent_name,
                   s.parent_phone, cfg.enabled, cfg.notify_time_in,
                   cfg.notify_time_out, cfg.time_in_template,
                   cfg.time_out_template, cfg.api_token
            FROM attendance a
            JOIN students s ON s.rfid_number = a.rfid_number
            JOIN sms_settings cfg ON cfg.id = 1
            WHERE a.attendance_id = %s
        """, (attendance_id,))
        record = cursor.fetchone()
        if not record or not record["attendance_time"]:
            return jsonify({
                "success": False,
                "message": "The selected attendance time is not recorded.",
            }), 404
        event_setting = (
            "notify_time_in" if event == "time_in" else "notify_time_out"
        )
        if not record["enabled"] or not record[event_setting]:
            return jsonify({
                "success": False,
                "message": "Parent SMS is disabled for this event in Settings.",
            }), 400
        if not record["api_token"]:
            return jsonify({
                "success": False,
                "message": "Set the PhilSMS API token in Settings first.",
            }), 400
        try:
            normalized_phone = normalize_philippines_phone(
                record["parent_phone"] or ""
            )
        except ValueError as error:
            return jsonify({"success": False, "message": str(error)}), 400

        message_template = (
            record["time_in_template"]
            if event == "time_in"
            else record["time_out_template"]
        )
        message = render_attendance_sms(
            record, event, record["date"], record["attendance_time"],
            message_template,
        )
        ticket = create_sms_send_ticket(
            cursor,
            record["rfid_number"],
            record["date"],
            event,
            record["attendance_time"],
        )
        connection.commit()
        phone = normalized_phone
        masked_phone = (
            f"{phone[:2]}{'*' * max(0, len(phone) - 4)}{phone[-2:]}"
            if len(phone) >= 5
            else "not available"
        )
        return jsonify({
            "success": True,
            "ticket": ticket,
            "message": message,
            "student_name": record["full_name"],
            "parent_name": record["parent_name"],
            "recipient": masked_phone,
            "event": event,
        })
    except Error:
        app.logger.exception("Could not prepare attendance SMS preview")
        return jsonify({
            "success": False,
            "message": "Could not prepare the SMS preview.",
        }), 500
    except RuntimeError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# DASHBOARD ATTENDANCE
# =========================================================

@app.route("/api/dashboard-attendance", methods=["GET"])
def get_dashboard_attendance():
    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT attendance_id, rfid_number, full_name,
                   grade_level, strand, date, time_in, time_out, status
            FROM attendance
            WHERE date = %s
            ORDER BY attendance_id ASC
        """, (today,))

        return jsonify(cursor.fetchall())

    except Error:
        app.logger.exception("Dashboard attendance MySQL error")
        return jsonify({
            "success": False,
            "message": "Could not load attendance records."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

@app.route("/api/dashboard-stats", methods=["GET"])
def get_dashboard_stats():
    connection = None

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE date = %s AND time_in IS NOT NULL
        """, (today,))
        entered_today = cursor.fetchone()[0]

        current_time = datetime.now().strftime("%H:%M")
        school_time = datetime.strptime(
            SCHOOL_TIME_IN, "%I:%M %p"
        ).strftime("%H:%M")

        absent_today = (
            max(0, total_students - entered_today)
            if current_time >= school_time
            else 0
        )

        return jsonify({
            "success": True,
            "total_students": total_students,
            "entered_today": entered_today,
            "absent_today": absent_today
        })

    except Error:
        app.logger.exception("Dashboard statistics MySQL error")
        return jsonify({
            "success": False,
            "message": "Could not load dashboard statistics."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# HOME PAGE AND STATIC FILES
# =========================================================

@app.route("/dashboard")
def dashboard():
    if not is_admin_logged_in():
        return redirect("/")
    response = send_from_directory(".", "Home.html")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/login.css")
def login_css():
    return send_from_directory(".", "login.css")


@app.route("/register.css")
def register_css():
    return send_from_directory(".", "register.css")


@app.route("/Home.css")
def home_css():
    return send_from_directory(".", "Home.css")


@app.route("/script.js")
def javascript_file():
    response = send_from_directory(".", "script.js")
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================================================
# CHANGE ADMIN PASSWORD
# =========================================================

@app.route("/api/change-password", methods=["POST"])
def change_admin_password():
    if not is_admin_logged_in():
        return jsonify({
            "success": False,
            "message": "You are not logged in."
        }), 401

    data = request.get_json(silent=True) or {}

    current_username = str(data.get("currentUsername") or "").strip().lower()
    current_password = data.get("currentPassword", "")
    administrative_code = data.get("administrativeCode", "")
    new_password = data.get("newPassword", "")
    confirm_password = data.get("confirmNewPassword", "")

    if not all([
        current_username, current_password, administrative_code,
        new_password, confirm_password
    ]):
        return jsonify({
            "success": False,
            "message": "Please complete all fields."
        }), 400

    # IMPORTANT: Replace this old hardcoded code with a secure,
    # server-side configuration before using the system outside localhost.
    expected_code = os.getenv("ADMINISTRATIVE_CODE", "")

    if not expected_code or administrative_code != expected_code:
        return jsonify({
            "success": False,
            "message": "Incorrect administrative code."
        }), 403

    if current_username != session.get("username", "").lower():
        return jsonify({
            "success": False,
            "message": "The username must match your logged-in account."
        }), 401

    if not isinstance(new_password, str) or not re.fullmatch(r"[0-9]{6}", new_password):
        return jsonify({
            "success": False,
            "message": "New password must contain exactly 6 digits."
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "New passwords do not match."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT id, password
            FROM users
            WHERE username = %s
        """, (current_username,))
        user = cursor.fetchone()

        if user is None or not password_matches(
            user["password"], current_password
        ):
            return jsonify({
                "success": False,
                "message": "Incorrect current username or password."
            }), 401

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE id = %s
        """, (
            generate_password_hash(new_password),
            user["id"]
        ))
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Administrator password changed successfully."
        })

    except Error:
        app.logger.exception("Change password MySQL error")
        return jsonify({
            "success": False,
            "message": "Unable to change the password right now."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# MONTHLY ATTENDANCE REPORT
# =========================================================

@app.route("/api/attendance-report", methods=["GET"])
def get_attendance_report():
    selected_month = request.args.get("month", "").strip()
    selected_group = request.args.get("group", "").strip()

    if not re.fullmatch(r"\d{4}-\d{2}", selected_month):
        return jsonify({
            "success": False,
            "message": "Please select a valid month."
        }), 400

    connection = None

    try:
        connection = get_mysql_connection()
        cursor = get_mysql_cursor(connection)

        cursor.execute("""
            SELECT student_id, rfid_number, full_name, grade_level, strand
            FROM students
            ORDER BY full_name ASC
        """)
        all_students = cursor.fetchall()

        students = []

        for student in all_students:
            if not selected_group:
                students.append(student)
                continue

            selected_strand, grade_number = selected_group.rsplit(" ", 1)
            selected_grade = "Grade " + grade_number

            if (
                student["strand"] == selected_strand
                and student["grade_level"] == selected_grade
            ):
                students.append(student)

        cursor.execute("""
            SELECT attendance_id, rfid_number, full_name, grade_level,
                   strand, date, time_in, time_out, status
            FROM attendance
            WHERE date LIKE %s
            ORDER BY date ASC, attendance_id ASC
        """, (selected_month + "%",))

        attendance_records = cursor.fetchall()
        attendance_lookup = {}

        for record in attendance_records:
            rfid = record["rfid_number"]
            attendance_date = record["date"]

            attendance_lookup.setdefault(rfid, {})[attendance_date] = {
                "time_in": record["time_in"],
                "time_out": record["time_out"],
                "status": record["status"]
            }

        report_students = []

        for student in students:
            report_students.append({
                "student_id": student["student_id"],
                "rfid_number": student["rfid_number"],
                "full_name": student["full_name"],
                "grade_level": student["grade_level"],
                "strand": student["strand"],
                "attendance": attendance_lookup.get(
                    student["rfid_number"], {}
                )
            })

        return jsonify({
            "success": True,
            "month": selected_month,
            "group": selected_group or "All Students",
            "total_students": len(report_students),
            "students": report_students
        })

    except Error:
        app.logger.exception("Attendance report MySQL error")
        return jsonify({
            "success": False,
            "message": "Could not generate attendance report."
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":
    connection = None

    try:
        initialize_mysql_database()
        connection = get_mysql_connection()
        connection.cursor().execute("SELECT 1")
        print("MySQL connection successful.")

    except Error as error:
        app.logger.exception("Could not initialize or connect to MySQL.")
        raise SystemExit(
            f"MySQL setup failed: {error}. "
            "Check the server and MYSQL_CONFIG."
        ) from error

    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
        use_reloader=False
    )