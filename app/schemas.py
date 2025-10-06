from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuestionRead(BaseModel):
    id: int
    text: str

    class Config:
        orm_mode = True


class DocumentRead(BaseModel):
    id: int
    title: str
    original_filename: str
    summary: str
    questions: List[QuestionRead]
    created_at: datetime

    class Config:
        orm_mode = True


class AnswerRequest(BaseModel):
    question_id: int


class AnswerResponse(BaseModel):
    question: QuestionRead
    answer: str
    supporting_text: Optional[str] = None
