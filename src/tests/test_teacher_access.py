import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import app
from teacher_auth import hash_password


class TeacherAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app.TEACHERS_FILE = Path(self.temp_dir.name) / "teachers.json"
        salt, password_hash = hash_password("school-password-123")
        app.TEACHERS_FILE.write_text(
            json.dumps({"teachers": [{
                "username": "teacher",
                "salt": salt,
                "password_hash": password_hash,
            }]}),
            encoding="utf-8",
        )
        app.sessions.clear()
        self.original_participants = app.activities["Programming Class"]["participants"][:]
        self.client = TestClient(app.app)

    def tearDown(self):
        app.activities["Programming Class"]["participants"] = self.original_participants
        app.sessions.clear()
        self.temp_dir.cleanup()

    def test_only_authenticated_teachers_can_change_registrations(self):
        activity = "Programming Class"
        email = "test-student@mergington.edu"

        self.assertEqual(self.client.get("/activities").status_code, 200)
        self.assertEqual(
            self.client.post(f"/activities/{activity}/signup", params={"email": email}).status_code,
            401,
        )
        self.assertEqual(
            self.client.delete(f"/activities/{activity}/unregister", params={"email": email}).status_code,
            401,
        )

        login = self.client.post(
            "/auth/login", json={"username": "teacher", "password": "school-password-123"}
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("httponly", login.headers["set-cookie"].lower())
        self.assertEqual(
            self.client.post(f"/activities/{activity}/signup", params={"email": email}).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f"/activities/{activity}/unregister", params={"email": email}).status_code,
            200,
        )

        self.assertEqual(self.client.delete("/auth/logout").status_code, 200)
        self.assertEqual(
            self.client.post(f"/activities/{activity}/signup", params={"email": email}).status_code,
            401,
        )


if __name__ == "__main__":
    unittest.main()