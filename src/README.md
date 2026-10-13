# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher sign-in to register and unregister students

## Getting Started

1. From the repository root, install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. From the `src` directory, create a teacher account:

   ```
   python manage_teachers.py <username>
   ```

3. Start the application from the `src` directory:

```sh
uvicorn app:app --reload
```

The command prompts for a password of at least 12 characters and stores only a salted PBKDF2 hash in `teachers.json`. That local credentials file is git-ignored. Teacher sessions use an HTTP-only, same-site cookie and expire after eight hours; restarting the server signs out all teachers.

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Sign in as a teacher                                                 |
| GET    | `/auth/session`                                                   | Check the current teacher session                                   |
| DELETE | `/auth/logout`                                                    | Sign out the current teacher                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student registration                                   |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only student removal                                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
