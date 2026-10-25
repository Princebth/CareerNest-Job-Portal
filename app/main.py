from contextlib import asynccontextmanager
from pathlib import Path
import uuid

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Query,
    File,
    Form,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select, or_, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def add_missing_application_columns():
    """
    Adds new application fields to an existing MySQL table.
    Existing application records are preserved.
    """

    required_columns = {
        "full_name": "VARCHAR(100) NULL",
        "email": "VARCHAR(255) NULL",
        "phone": "VARCHAR(20) NULL",
        "education": "VARCHAR(150) NULL",
        "college": "VARCHAR(200) NULL",
        "skills": "TEXT NULL",
        "experience_level": "VARCHAR(30) NULL",
    }

    inspector = inspect(engine)

    if "applications" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("applications")
    }

    with engine.begin() as connection:
        for column_name, column_definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE applications "
                        f"ADD COLUMN {column_name} {column_definition}"
                    )
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    add_missing_application_columns()
    yield


# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="CareerNest Job Portal API",
    description="Recruitment portal built with FastAPI and MySQL",
    version="1.1.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads",
)


# --------------------------------------------------
# HOME AND HEALTH
# --------------------------------------------------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

@app.post(
    "/api/auth/register",
    response_model=schemas.UserOut,
    status_code=201,
)
def register(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()

    existing_user = db.scalar(
        select(models.User).where(models.User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    user = models.User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    return user


@app.post(
    "/api/auth/login",
    response_model=schemas.TokenOut,
)
def login(
    payload: schemas.LoginInput,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()

    user = db.scalar(
        select(models.User).where(models.User.email == email)
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


@app.get(
    "/api/auth/me",
    response_model=schemas.UserOut,
)
def me(
    user: models.User = Depends(get_current_user),
):
    return user


# --------------------------------------------------
# JOBS
# --------------------------------------------------

@app.get(
    "/api/jobs",
    response_model=list[schemas.JobOut],
)
def list_jobs(
    search: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    job_type: str | None = Query(default=None, max_length=50),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(models.Job)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                models.Job.title.ilike(term),
                models.Job.company.ilike(term),
                models.Job.description.ilike(term),
            )
        )

    if location:
        stmt = stmt.where(
            models.Job.location.ilike(f"%{location.strip()}%")
        )

    if job_type:
        stmt = stmt.where(models.Job.job_type == job_type)

    return list(
        db.scalars(
            stmt.order_by(models.Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


@app.get(
    "/api/jobs/{job_id}",
    response_model=schemas.JobOut,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@app.post(
    "/api/jobs",
    response_model=schemas.JobOut,
    status_code=201,
)
def create_job(
    payload: schemas.JobCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("recruiter")),
):
    job = models.Job(
        **payload.model_dump(),
        recruiter_id=user.id,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@app.patch(
    "/api/jobs/{job_id}",
    response_model=schemas.JobOut,
)
def update_job(
    job_id: int,
    payload: schemas.JobUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("recruiter")),
):
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.recruiter_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own jobs",
        )

    for key, value in payload.model_dump(
        exclude_unset=True
    ).items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)

    return job


@app.delete(
    "/api/jobs/{job_id}",
    status_code=204,
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("recruiter")),
):
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.recruiter_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own jobs",
        )

    db.delete(job)
    db.commit()

    return None


# --------------------------------------------------
# APPLY FOR JOB
# --------------------------------------------------

@app.post(
    "/api/jobs/{job_id}/apply",
    response_model=schemas.ApplicationOut,
    status_code=201,
)
def apply_for_job(
    job_id: int,
    full_name: str = Form(..., min_length=2, max_length=100),
    email: str = Form(..., max_length=255),
    phone: str = Form(..., min_length=7, max_length=20),
    education: str = Form(..., min_length=2, max_length=150),
    college: str = Form(..., min_length=2, max_length=200),
    skills: str = Form(..., min_length=1),
    experience_level: str = Form(...),
    cover_letter: str = Form(default=""),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("candidate")),
):
    # Check job
    job = db.get(models.Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # Prevent duplicate applications
    existing = db.scalar(
        select(models.Application).where(
            models.Application.job_id == job_id,
            models.Application.candidate_id == user.id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already applied for this job",
        )

    # Validate text fields
    full_name = full_name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    education = education.strip()
    college = college.strip()
    skills = skills.strip()
    cover_letter = cover_letter.strip()

    if not full_name or not education or not college or not skills:
        raise HTTPException(
            status_code=400,
            detail="Please fill in all required fields",
        )

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address",
        )

    if experience_level not in ("Fresher", "Experienced"):
        raise HTTPException(
            status_code=400,
            detail="Experience level must be Fresher or Experienced",
        )

    # Validate resume
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume",
        )

    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file",
        )

    file_content = resume.file.read()

    if not file_content or len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Resume must be non-empty and no larger than 5 MB",
        )

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF",
        )

    # Use a generated filename to avoid filename collisions
    filename = f"{uuid.uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(file_content)

    # Save applicant details in MySQL
    application = models.Application(
        job_id=job_id,
        candidate_id=user.id,
        full_name=full_name,
        email=email,
        phone=phone,
        education=education,
        college=college,
        skills=skills,
        experience_level=experience_level,
        resume_url=f"/uploads/{filename}",
        cover_letter=cover_letter or None,
        status="Submitted",
    )

    db.add(application)

    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=409,
            detail="You have already applied for this job",
        )
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    return application


# --------------------------------------------------
# CANDIDATE APPLICATIONS
# --------------------------------------------------

@app.get(
    "/api/applications/me",
    response_model=list[schemas.ApplicationOut],
)
def my_applications(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("candidate")),
):
    stmt = (
        select(models.Application)
        .where(models.Application.candidate_id == user.id)
        .order_by(models.Application.created_at.desc())
    )

    return list(db.scalars(stmt).all())


# --------------------------------------------------
# RECRUITER APPLICATIONS
# --------------------------------------------------

@app.get(
    "/api/recruiter/applications",
    response_model=list[schemas.ApplicationOut],
)
def recruiter_applications(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("recruiter")),
):
    stmt = (
        select(models.Application)
        .join(models.Job)
        .where(models.Job.recruiter_id == user.id)
        .order_by(models.Application.created_at.desc())
    )

    return list(db.scalars(stmt).all())


@app.patch(
    "/api/recruiter/applications/{application_id}",
    response_model=schemas.ApplicationOut,
)
def update_application_status(
    application_id: int,
    payload: schemas.ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("recruiter")),
):
    application = db.get(models.Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if application.job.recruiter_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update applications to your jobs",
        )

    application.status = payload.status

    db.commit()
    db.refresh(application)

    return application