from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["candidate", "recruiter"] = "candidate"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    company: str = Field(min_length=2, max_length=150)
    location: str = Field(default="Remote", max_length=150)
    job_type: str = Field(default="Full-time", max_length=50)
    description: str = Field(min_length=10)
    salary: str | None = Field(default=None, max_length=100)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    company: str | None = Field(default=None, min_length=2, max_length=150)
    location: str | None = Field(default=None, max_length=150)
    job_type: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, min_length=10)
    salary: str | None = Field(default=None, max_length=100)


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str
    job_type: str
    description: str
    salary: str | None
    recruiter_id: int
    created_at: datetime


class ApplicationCreate(BaseModel):
    resume_url: str | None = Field(default=None, max_length=500)
    cover_letter: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: Literal["Submitted", "Reviewed", "Shortlisted", "Accepted", "Rejected"]


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_id: int

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    college: str | None = None
    skills: str | None = None
    experience_level: str | None = None

    resume_url: str | None = None
    cover_letter: str | None = None

    status: str
    created_at: datetime