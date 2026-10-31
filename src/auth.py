
import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
import uuid
from pathlib import Path

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "users.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                storage_key TEXT NOT NULL UNIQUE,
                sha256 TEXT NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, sha256)
            )
        """)

def get_user_id(username):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    return user[0] if user else None

def save_report(user_id, filename, file_bytes):
    initialize_database()
    content = bytes(file_bytes)
    digest = hashlib.sha256(content).hexdigest()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM reports WHERE user_id = ? AND sha256 = ?",
            (user_id, digest)
        ).fetchone()
        if existing:
            return existing[0]

    report_id = uuid.uuid4().hex
    storage_key = f"{uuid.uuid4().hex}.upload"
    reports_dir = DATA_DIR / "uploads"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = reports_dir / storage_key

    try:
        file_path.write_bytes(content)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reports
                (id, user_id, filename, storage_key, sha256)
                VALUES (?, ?, ?, ?, ?)
                """,
                (report_id, user_id, Path(filename).name, storage_key, digest)
            )
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    return report_id

def list_saved_reports(user_id):
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, uploaded_at
            FROM reports
            WHERE user_id = ?
            ORDER BY uploaded_at DESC, rowid DESC
            """,
            (user_id,)
        ).fetchall()
    return [
        {"id": row[0], "filename": row[1], "uploaded_at": row[2]}
        for row in rows
    ]

def get_saved_report(user_id, report_id):
    initialize_database()
    with get_connection() as conn:
        report = conn.execute(
            """
            SELECT filename, storage_key
            FROM reports
            WHERE id = ? AND user_id = ?
            """,
            (report_id, user_id)
        ).fetchone()
    if report is None:
        return None

    filename, storage_key = report
    file_path = DATA_DIR / "uploads" / storage_key
    return filename, file_path.read_bytes()

def delete_saved_report(user_id, report_id):
    initialize_database()
    with get_connection() as conn:
        report = conn.execute(
            """
            SELECT storage_key
            FROM reports
            WHERE id = ? AND user_id = ?
            """,
            (report_id, user_id)
        ).fetchone()
        if report is None:
            return False

        (DATA_DIR / "uploads" / report[0]).unlink(missing_ok=True)
        conn.execute(
            "DELETE FROM reports WHERE id = ? AND user_id = ?",
            (report_id, user_id)
        )
    return True

def hash_password(password, salt):
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=bytes.fromhex(salt),
        n=2**14,
        r=8,
        p=1
    ).hex()

def register_user(username, email, password):
    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return False, "All fields are required."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    salt = secrets.token_bytes(16).hex()
    password_hash = hash_password(password, salt)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users
                (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, salt)
            )

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Username or email already exists."

def verify_user(email, password):
    email = email.strip().lower()

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, username, password_hash, salt
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if not user:
        return None

    user_id, username, stored_hash, salt = user
    entered_hash = hash_password(password, salt)

    if hmac.compare_digest(entered_hash, stored_hash):
        return user_id, username

    return None

def show_authentication():
    initialize_database()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        user_id = st.session_state.get("user_id")
        if user_id is None:
            user_id = get_user_id(st.session_state.get("username", ""))
            if user_id is not None:
                st.session_state.user_id = user_id

    if st.session_state.authenticated and user_id is not None:
        with st.sidebar:
            st.success(
                f"Logged in as {st.session_state.username}"
            )

            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.pop("user_id", None)
                for key in (
                    "analysis_measurements",
                    "analysis_text",
                    "analysis_name",
                    "analysis_signature",
                    "analysis_explanation",
                    "chat_messages",
                    "comparison_result",
                    "comparison_dates",
                    "comparison_names",
                    "analysis_upload",
                    "old_upload",
                    "new_upload",
                ):
                    st.session_state.pop(key, None)
                st.rerun()

        return True
    st.session_state.authenticated = False

    st.markdown(
        "<h1 style='text-align:center;'>🩺 SWASTHYA AI</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center;'>"
        "Your AI-powered Medical Report Analyzer"
        "</p>",
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with login_tab:
        st.subheader("Welcome Back")

        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input(
                "Password",
                type="password"
            )
            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login_button:
            user = verify_user(email, password)

            if user:
                user_id, username = user
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with register_tab:
        st.subheader("Create Your Account")

        with st.form("register_form"):
            username = st.text_input("Full Name")
            email = st.text_input("Email Address")
            password = st.text_input(
                "Create Password",
                type="password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            register_button = st.form_submit_button(
                "Register",
                use_container_width=True
            )

        if register_button:
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(
                    username, email, password
                )

                if success:
                    st.success(message)
                    st.info("Please log in using your new account.")
                else:
                    st.error(message)

    return False