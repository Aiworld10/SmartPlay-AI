from fastapi import APIRouter, Request, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from model import schemas, crud
from model.database import get_session
from fastapi import Query

router = APIRouter(prefix="/questions", tags=["questions"])


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


@router.get("/random", response_model=schemas.ListQuestionsOut)
async def get_random_questions(
        theme: str = Query(...),
        user_id: int = Query(...),
        db: AsyncSession = Depends(get_session)):

    db_questions = await crud.get_random_questions_by_theme(db, theme, player_id=user_id)
    if not db_questions:
        raise HTTPException(status_code=404, detail="No questions found")
    return schemas.ListQuestionsOut(questions=db_questions, user_id=user_id)
