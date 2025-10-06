from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import ai, auth, models, schemas
from .database import Base, engine, get_db
from .pdf_parser import extract_text_from_upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Frågeassistent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-postadressen används redan")
    hashed_password = auth.get_password_hash(user_in.password)
    user = models.User(email=user_in.email, full_name=user_in.full_name, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Felaktig e-post eller lösenord")
    token = auth.create_access_token(user.email)
    return schemas.TokenResponse(access_token=token)


@app.get("/documents", response_model=List[schemas.DocumentRead])
def list_documents(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    documents = (
        db.query(models.Document)
        .filter(models.Document.owner_id == current_user.id)
        .order_by(models.Document.created_at.desc())
        .all()
    )
    return documents


@app.get("/documents/{document_id}", response_model=schemas.DocumentRead)
def get_document(document_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.owner_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumentet hittades inte")
    return document


@app.post("/documents/upload", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form("Mitt dokument"),
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    text_content = await extract_text_from_upload(file)
    summary = ai.summarize_text(text_content)
    questions = ai.extract_questions(text_content)

    document = models.Document(
        title=title or "Mitt dokument",
        original_filename=file.filename or title,
        text_content=text_content,
        summary=summary,
        owner=current_user,
    )
    db.add(document)
    db.flush()

    for question_text in questions:
        question_model = models.Question(text=question_text, document=document)
        db.add(question_model)

    db.commit()
    db.refresh(document)
    return document


@app.post("/questions/answer", response_model=schemas.AnswerResponse)
def answer_question(
    answer_request: schemas.AnswerRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    question = (
        db.query(models.Question)
        .join(models.Document)
        .filter(
            models.Question.id == answer_request.question_id,
            models.Document.owner_id == current_user.id,
        )
        .first()
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frågan hittades inte")

    document = question.document
    answer_text, supporting_text = ai.answer_question(question.text, document.text_content)
    question_read = schemas.QuestionRead.from_orm(question)
    return schemas.AnswerResponse(question=question_read, answer=answer_text, supporting_text=supporting_text)
