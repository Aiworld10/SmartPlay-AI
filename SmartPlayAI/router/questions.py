from pathlib import Path
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from model import schemas, crud
from model.database import get_session
from fastapi import Query

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

router = APIRouter(prefix="/questions", tags=["questions"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.post("/create", response_model=schemas.QuestionOut)
async def create_question(
    db: AsyncSession = Depends(get_session),
    theme: str = Form(None),
    question_text: str = Form(None),
    question: schemas.QuestionCreate | None = None,  # JSON body
):
    """
    Create a new question.
    Supports both JSON (API clients) and Form (HTML forms).
    """
    if question:  # JSON case
        data = question
    elif theme and question_text:  # Form case
        data = schemas.QuestionCreate(theme=theme, question_text=question_text)
    else:
        raise HTTPException(status_code=400, detail="Invalid input")

    db_question = await crud.store_question(db, data)
    return db_question


@router.get("/id/{question_id}", response_model=schemas.QuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_session)):
    """
    Retrieve a question by ID.

    Args:
        question_id (int): Unique identifier of the question.
        db (AsyncSession): Async SQLAlchemy database session.

    Returns:
        QuestionOut: The Question object if found.

    Raises:
        HTTPException: If the question with the given ID does not exist.
    """
    db_question = await crud.get_question(db, question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question


@router.get("/random", response_class=HTMLResponse)
async def get_random_questions(
        request: Request,
        theme: str = Query(...),
        user_id: int = Query(...),
        db: AsyncSession = Depends(get_session)):

    db_questions = await crud.get_random_questions_by_theme(db, theme, player_id=user_id)
    if not db_questions:
        raise HTTPException(status_code=404, detail="No questions found")

    # Convert SQLAlchemy objects to dictionaries for JSON serialization
    questions_dict = []
    for q in db_questions:
        questions_dict.append({
            "id": q.id,
            "theme": q.theme,
            "question_text": q.question_text
        })

    # Return the game interface with questions
    return templates.TemplateResponse(
        request,
        "question_game.html",
        {
            "questions": questions_dict,
            "user_id": user_id,
            "theme": theme
        }
    )


@router.get("/random/api", response_model=schemas.ListQuestionsOut)
async def get_random_questions_api(
        theme: str = Query(...),
        user_id: int = Query(...),
        db: AsyncSession = Depends(get_session)):
    """API endpoint for getting random questions as JSON"""
    db_questions = await crud.get_random_questions_by_theme(db, theme, player_id=user_id)
    if not db_questions:
        raise HTTPException(status_code=404, detail="No questions found")
    return schemas.ListQuestionsOut(questions=db_questions, user_id=user_id)


@router.get("/result", response_class=HTMLResponse)
async def get_result_page(request: Request):
    """Display the result page after answering a question"""
    return templates.TemplateResponse(request, "result.html", {})


@router.get("/next", response_class=HTMLResponse)
async def get_next_question_page(request: Request):
    """Display the next question page"""
    return templates.TemplateResponse(request, "next_question.html", {})


@router.get("/leaderboard", response_class=HTMLResponse)
async def get_leaderboard_page(request: Request):
    """Display the leaderboard page"""
    return templates.TemplateResponse(request, "leaderboard.html", {})
