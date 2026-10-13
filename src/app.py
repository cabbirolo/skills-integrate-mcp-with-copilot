"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import secrets
import os
import time
from pathlib import Path
from teacher_auth import load_teacher_accounts, verify_password

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

AUTH_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
TEACHERS_FILE = Path(__file__).with_name("teachers.json")
sessions = {}


class TeacherCredentials(BaseModel):
    username: str
    password: str


def require_teacher(teacher_session: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME)) -> str:
    """Require a valid teacher session for activity changes."""
    session = sessions.get(teacher_session)
    if session is None:
        raise HTTPException(status_code=401, detail="Teacher login required")

    username, expires_at = session
    if expires_at <= time.time():
        sessions.pop(teacher_session, None)
        raise HTTPException(status_code=401, detail="Teacher session expired")

    return username

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: TeacherCredentials, request: Request, response: Response):
    try:
        teachers = load_teacher_accounts(TEACHERS_FILE)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Teacher accounts are not configured. Run python manage_teachers.py.",
        )

    teacher = next(
        (account for account in teachers if account["username"] == credentials.username),
        None,
    )
    if teacher is None or not verify_password(
        credentials.password, teacher["salt"], teacher["password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    now = time.time()
    for token, (_, expires_at) in list(sessions.items()):
        if expires_at <= now:
            sessions.pop(token, None)

    token = secrets.token_urlsafe(32)
    sessions[token] = (teacher["username"], now + SESSION_DURATION_SECONDS)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"message": "Signed in", "username": teacher["username"]}


@app.get("/auth/session")
def get_session(teacher_session: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME)):
    session = sessions.get(teacher_session)
    if session is None:
        return {"authenticated": False, "username": None}

    username, expires_at = session
    if expires_at <= time.time():
        sessions.pop(teacher_session, None)
        return {"authenticated": False, "username": None}

    return {"authenticated": True, "username": username}


@app.delete("/auth/logout")
def logout(response: Response, teacher_session: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME)):
    sessions.pop(teacher_session, None)
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return {"message": "Signed out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher: str = Depends(require_teacher)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher: str = Depends(require_teacher)):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
