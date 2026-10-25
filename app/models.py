from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    jobs: Mapped[list["Job"]] = relationship(back_populates="recruiter")
    applications: Mapped[list["Application"]] = relationship(back_populates="candidate")

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), index=True)
    company: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(150), default="Remote")
    job_type: Mapped[str] = mapped_column(String(50), default="Full-time")
    description: Mapped[str] = mapped_column(Text)
    salary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recruiter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recruiter: Mapped["User"] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE")
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    # Applicant details
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    education: Mapped[str | None] = mapped_column(String(150), nullable=True)
    college: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Resume and cover letter
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="Submitted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    job: Mapped["Job"] = relationship(back_populates="applications")
    candidate: Mapped["User"] = relationship(back_populates="applications")