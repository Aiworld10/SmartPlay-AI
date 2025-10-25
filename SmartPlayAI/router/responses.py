from fastapi import APIRouter, Request, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from router.authenticate import get_current_user_from_cookie
from model import schemas, crud
from fetchLLMresponse import evaluate_player_response as evaluate_answer
from model.database import get_session


router = APIRouter(prefix="/responses", tags=["responses"])


@router.post("/create", response_model=schemas.ResponseOut)
async def create_response(response: schemas.ResponseCreate, db: AsyncSession = Depends(get_session)):
    """
    Create a new response.

    Args:
        response (ResponseCreate): Pydantic model containing response creation data.
        db (AsyncSession): Async SQLAlchemy database session.

    Returns:
        ResponseOut: The newly created Response object.
    """
    db_response = await crud.store_response(db, response)
    return db_response


@router.post("/answer")
async def answer_question(
    request: Request,
    question_id: int = Form(...),
    question_text: str = Form(...),
    response_text: str = Form(...),
    db: AsyncSession = Depends(get_session),
    current_user: schemas.PlayerRead = Depends(get_current_user_from_cookie),
):
    # Evaluate with LLM
    text, result = evaluate_answer(
        question_text, response_text)

    # Store response in DB
    db_response = await crud.store_response(
        db,
        schemas.ResponseCreate(
            player_id=current_user.id,   # pulled from token
            question_id=question_id,
            response_text=response_text,
            score=result["score"],
        ),
    )

    # Return results (frontend can render evaluation & verdict)
    return {
        "db_response": db_response,
        "evaluation": text,
        "verdict": result["verdict"],
        "score": result["score"],
    }
