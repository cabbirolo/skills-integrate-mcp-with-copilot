"""Helpers for creating and checking teacher credentials."""

import hashlib
import hmac
import json
import secrets
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).with_name("teachers.json")
PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return salt.hex(), password_hash.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    try:
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
        )
        expected = bytes.fromhex(expected_hash)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual_hash, expected)


def load_teacher_accounts(path: Path = CREDENTIALS_FILE) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as credentials_file:
        data = json.load(credentials_file)

    teachers = data.get("teachers") if isinstance(data, dict) else None
    if not isinstance(teachers, list):
        raise ValueError("Teacher credentials must contain a teachers list")

    for teacher in teachers:
        if not isinstance(teacher, dict) or not all(
            isinstance(teacher.get(key), str)
            for key in ("username", "salt", "password_hash")
        ):
            raise ValueError("Teacher credential entry is malformed")

    return teachers