# CareerNest — Job Portal (FastAPI + MySQL)

A full-stack job portal portfolio project built with FastAPI, SQLAlchemy, MySQL, Pydantic, JWT authentication, and a responsive HTML/CSS/JavaScript frontend.

## Features

- Candidate and recruiter registration/login
- Password hashing and JWT bearer authentication
- Recruiters can create, edit, and delete their own job listings
- Public job listing with keyword search, location filter, job-type filter, and pagination
- Candidates can apply once per job and optionally provide a resume URL and cover letter
- Recruiters can view applications for their jobs and update application status
- Pydantic request validation, helpful HTTP errors, relational database constraints
- Interactive OpenAPI/Swagger documentation at `/docs`
- Responsive frontend served by FastAPI

## Tech stack

- Python 3.10+
- FastAPI + Uvicorn
- MySQL 8+
- SQLAlchemy 2 + PyMySQL
- Pydantic v2
- JWT (`python-jose`) and Passlib password hashing
- HTML, CSS, vanilla JavaScript
- Pytest + FastAPI TestClient

## Project structure

```text
job_portal_fastapi/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── tests/
│   └── test_health.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 1. Prerequisites

Install Python 3.10 or newer and MySQL 8+. Start the MySQL server.

Create the database:

```sql
CREATE DATABASE job_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 2. Set up the environment

Open a terminal in the project folder.

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, use Command Prompt and run:

```bat
.venv\Scripts\activate.bat
```

Edit `.env` and set `DATABASE_URL` with your MySQL username/password. Example:

```text
DATABASE_URL=mysql+pymysql://root:MyPassword@localhost:3306/job_portal
SECRET_KEY=replace-this-with-a-long-random-secret
ACCESS_TOKEN_MINUTES=120
```

The app loads `.env` automatically using `python-dotenv`. Never commit the real `.env` file.

### Optional PowerShell environment variables (current terminal only)

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:MyPassword@localhost:3306/job_portal"
$env:SECRET_KEY = "replace-this-with-a-long-random-secret"
```

## 3. Run the app

```powershell
uvicorn app.main:app --reload
```

Open:
- Frontend: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Tables are created automatically on app startup for local development. For production, use database migrations (e.g. Alembic) rather than `create_all`.

## 4. Try the project

1. Open the frontend and create a **Recruiter** account.
2. Log out and create a **Candidate** account in a separate browser/profile, or use Swagger.
3. Log back in as recruiter and publish a job.
4. Log in as candidate and apply to that job.
5. In Swagger, authorize using the access token returned from `/api/auth/login` (paste the token; the OAuth2 bearer scheme will add `Bearer`).
6. As the recruiter, use `/api/recruiter/applications` to see applications and `PATCH /api/recruiter/applications/{application_id}` to update status.

For Swagger's login endpoint, use the JSON body defined by the API (`email` and `password`), not the OAuth2 password form. To authorize manually, copy the `access_token` from the JSON login response into the Authorize dialog.

## API overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Create candidate/recruiter account |
| POST | `/api/auth/login` | Public | Receive JWT token |
| GET | `/api/auth/me` | Signed-in user | Current profile |
| GET | `/api/jobs` | Public | Search/list jobs |
| GET | `/api/jobs/{job_id}` | Public | Job details |
| POST | `/api/jobs` | Recruiter | Create a job |
| PATCH | `/api/jobs/{job_id}` | Owning recruiter | Update a job |
| DELETE | `/api/jobs/{job_id}` | Owning recruiter | Delete a job |
| POST | `/api/jobs/{job_id}/apply` | Candidate | Apply to a job |
| GET | `/api/applications/me` | Candidate | List own applications |
| GET | `/api/recruiter/applications` | Recruiter | List applications to own jobs |
| PATCH | `/api/recruiter/applications/{application_id}` | Owning recruiter | Update application status |

### Example request bodies

Register:

```json
{
  "name": "Alex Candidate",
  "email": "candidate@example.com",
  "password": "StrongPass123",
  "role": "candidate"
}
```

Create job (requires recruiter token):

```json
{
  "title": "Junior Python Developer",
  "company": "Example Tech",
  "location": "Pune",
  "job_type": "Full-time",
  "description": "Build and maintain Python REST APIs with the engineering team.",
  "salary": "3–5 LPA"
}
```

Apply (requires candidate token):

```json
{
  "resume_url": "https://example.com/resume.pdf",
  "cover_letter": "I am interested in this Python Developer role."
}
```

Update application status (requires owning recruiter token):

```json
{
  "status": "Shortlisted"
}
```

## 5. Testing

With MySQL configured and the virtual environment active:

```powershell
pytest -q
```

The included tests check the health route and public jobs endpoint. Because app startup initializes the database, tests require the configured MySQL database to be running.

## Security and production notes

- Change `SECRET_KEY` to a long random secret before deployment.
- Configure secrets via environment variables; do not commit `.env`.
- This demo accepts a resume URL rather than uploading files directly.
- Add Alembic migrations, rate limiting, email verification, CORS rules, structured logging, and production database credentials before production use.
- Restrict recruiter account creation or add an approval process in a real hiring platform.
- Serve behind HTTPS in production. Browser localStorage is convenient for this portfolio demo; stronger production apps may use secure, HttpOnly cookies.
- Do not store or share real candidate personal data in a public demo.

## Resume-ready project entry

**CareerNest — Job Portal REST API | Python, FastAPI, MySQL, SQLAlchemy, Pydantic, JWT, HTML, CSS, JavaScript**

- Developed a full-stack recruitment portal with role-based candidate/recruiter workflows and JWT authentication.
- Built REST APIs for job CRUD, search/filtering, applications, and application-status management using FastAPI and Pydantic.
- Designed relational MySQL tables and SQLAlchemy models with foreign keys and duplicate-application prevention.
- Documented and tested endpoints using Swagger UI and Pytest.

Only list features you have run and can confidently explain in an interview.

## GitHub upload

```bash
git init
git add .
git commit -m "Build CareerNest FastAPI job portal"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/job-portal-fastapi.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Do not upload `.env` or credentials.
