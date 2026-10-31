import src.auth as auth


def create_user(username):
    with auth.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, salt)
            VALUES (?, ?, ?, ?)
            """,
            (username, f"{username}@example.com", "hash", "salt")
        )
    return cursor.lastrowid


def configure_test_database(monkeypatch, tmp_path):
    monkeypatch.setattr(auth, "DATA_DIR", tmp_path)
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "users.db")
    auth.initialize_database()


def test_saved_reports_are_persistent_and_deduplicated(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    user_id = create_user("alice")

    report_id = auth.save_report(user_id, "blood-test.pdf", b"report contents")
    duplicate_id = auth.save_report(user_id, "renamed.pdf", b"report contents")

    assert duplicate_id == report_id
    saved_reports = auth.list_saved_reports(user_id)
    assert len(saved_reports) == 1
    assert saved_reports[0]["id"] == report_id
    assert saved_reports[0]["filename"] == "blood-test.pdf"
    assert auth.get_saved_report(user_id, report_id) == (
        "blood-test.pdf",
        b"report contents",
    )


def test_saved_reports_are_private_and_can_be_deleted(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    owner_id = create_user("owner")
    other_user_id = create_user("other")
    report_id = auth.save_report(owner_id, "private.pdf", b"private report")

    assert auth.list_saved_reports(other_user_id) == []
    assert auth.get_saved_report(other_user_id, report_id) is None
    assert auth.delete_saved_report(other_user_id, report_id) is False
    assert auth.get_saved_report(owner_id, report_id) == (
        "private.pdf",
        b"private report",
    )

    assert auth.delete_saved_report(owner_id, report_id) is True
    assert auth.get_saved_report(owner_id, report_id) is None
    assert auth.list_saved_reports(owner_id) == []


def test_login_verification_includes_user_id(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    assert auth.register_user("alice", "alice@example.com", "password123")[0]
    user_id = auth.get_user_id("alice")

    assert auth.verify_user("alice@example.com", "password123") == (
        user_id,
        "alice",
    )
