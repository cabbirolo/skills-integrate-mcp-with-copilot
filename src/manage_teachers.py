"""Interactively add a teacher account to the local credentials file."""

import getpass
import json
import sys

from teacher_auth import CREDENTIALS_FILE, hash_password, load_teacher_accounts


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit("Usage: python manage_teachers.py <username>")

    username = sys.argv[1].strip()
    try:
        teachers = load_teacher_accounts(CREDENTIALS_FILE)
    except FileNotFoundError:
        teachers = []

    if any(teacher["username"] == username for teacher in teachers):
        raise SystemExit(f"Teacher account '{username}' already exists")

    password = getpass.getpass("New password (at least 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    salt, password_hash = hash_password(password)
    teachers.append({"username": username, "salt": salt, "password_hash": password_hash})
    CREDENTIALS_FILE.write_text(
        json.dumps({"teachers": teachers}, indent=2) + "\n", encoding="utf-8"
    )
    CREDENTIALS_FILE.chmod(0o600)
    print(f"Added teacher account '{username}' to {CREDENTIALS_FILE.name}")


if __name__ == "__main__":
    main()