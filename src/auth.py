
import streamlit as st
import sqlite3
import hashlib
import secrets
import hmac
import uuid
import os
import tempfile
import binascii
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from streamlit.errors import StreamlitSecretNotFoundError

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "users.db"
ENCRYPTED_PREFIX = b"SWASTHYA_ENC_V1:"
ENCRYPTED_FILENAME_PREFIX = "SWASTHYA_ENC_V1:"

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

def get_report_fernet():
    try:
        key = st.secrets.get("REPORT_ENCRYPTION_KEY")
    except StreamlitSecretNotFoundError:
        key = None
    key = key or os.environ.get("SWASTHYA_REPORT_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "Report encryption is not configured. Set REPORT_ENCRYPTION_KEY "
            "in Streamlit secrets or SWASTHYA_REPORT_ENCRYPTION_KEY in the "
            "environment. Generate a key with "
            "Fernet.generate_key().decode(). Keep a secure backup; losing "
            "the key makes saved reports unrecoverable."
        )
    try:
        return Fernet(key.encode("ascii") if isinstance(key, str) else key)
    except (binascii.Error, TypeError, ValueError) as error:
        raise RuntimeError(
            "The report encryption key is invalid. Generate a Fernet key "
            "with Fernet.generate_key().decode()."
        ) from error

def _write_encrypted_file(file_path, content):
    encrypted = ENCRYPTED_PREFIX + get_report_fernet().encrypt(content)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(encrypted)
        temp_path.replace(file_path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

def _ensure_encrypted_file(file_path):
    content = file_path.read_bytes()
    if content.startswith(ENCRYPTED_PREFIX):
        return
    _write_encrypted_file(file_path, content)

def _read_report_file(file_path):
    content = file_path.read_bytes()
    if not content.startswith(ENCRYPTED_PREFIX):
        _write_encrypted_file(file_path, content)
        return content
    try:
        return get_report_fernet().decrypt(content[len(ENCRYPTED_PREFIX):])
    except InvalidToken as error:
        raise RuntimeError(
            "Could not decrypt this report. The encryption key may have "
            "changed or the stored file may be damaged."
        ) from error

def _encrypt_filename(filename, fernet):
    return ENCRYPTED_FILENAME_PREFIX + fernet.encrypt(
        filename.encode("utf-8")
    ).decode("ascii")

def _decrypt_filename(filename, fernet):
    if not filename.startswith(ENCRYPTED_FILENAME_PREFIX):
        return filename
    try:
        encrypted = filename[len(ENCRYPTED_FILENAME_PREFIX):].encode("ascii")
        return fernet.decrypt(encrypted).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as error:
        raise RuntimeError(
            "Could not decrypt a saved report filename. The encryption key "
            "may have changed or the database may be damaged."
        ) from error

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
    fernet = get_report_fernet()

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT id, filename, storage_key
            FROM reports
            WHERE user_id = ? AND sha256 = ?
            """,
            (user_id, digest)
        ).fetchone()
        if existing:
            _ensure_encrypted_file(DATA_DIR / "uploads" / existing[2])
            if not existing[1].startswith(ENCRYPTED_FILENAME_PREFIX):
                conn.execute(
                    "UPDATE reports SET filename = ? WHERE id = ?",
                    (_encrypt_filename(existing[1], fernet), existing[0])
                )
            return existing[0]

    report_id = uuid.uuid4().hex
    storage_key = f"{uuid.uuid4().hex}.upload"
    reports_dir = DATA_DIR / "uploads"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_path = reports_dir / storage_key

    try:
        _write_encrypted_file(file_path, content)
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reports
                (id, user_id, filename, storage_key, sha256)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    user_id,
                    _encrypt_filename(Path(filename).name, fernet),
                    storage_key,
                    digest,
                )
            )
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    return report_id

def list_saved_reports(user_id):
    initialize_database()
    fernet = get_report_fernet()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, uploaded_at, storage_key
            FROM reports
            WHERE user_id = ?
            ORDER BY uploaded_at DESC, rowid DESC
            """,
            (user_id,)
        ).fetchall()
        reports = []
        for report_id, filename, uploaded_at, storage_key in rows:
            _ensure_encrypted_file(DATA_DIR / "uploads" / storage_key)
            if not filename.startswith(ENCRYPTED_FILENAME_PREFIX):
                filename = _encrypt_filename(filename, fernet)
                conn.execute(
                    "UPDATE reports SET filename = ? WHERE id = ?",
                    (filename, report_id)
                )
            reports.append({
                "id": report_id,
                "filename": _decrypt_filename(filename, fernet),
                "uploaded_at": uploaded_at,
            })
    return reports

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
    fernet = get_report_fernet()
    file_path = DATA_DIR / "uploads" / storage_key
    return _decrypt_filename(filename, fernet), _read_report_file(file_path)

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