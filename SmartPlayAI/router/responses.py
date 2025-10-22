from fastapi import APIRouter, Request, Form, Depends, HTTPException, Query
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
    current_user: schemas.PlayerBase = Depends(get_current_user_from_cookie),
):
    # Check for cached evaluation to avoid duplicate LLM calls
    cached = await crud.get_cached_evaluation(
        db, question_id=question_id, question_text=question_text, response_text=response_text
    )

    if cached and cached.llm_feedback and cached.score is not None:
        evaluation_text = cached.llm_feedback
        score = cached.score
        verdict = "GOOD" if score is not None and score >= 3 else "BAD"
    else:
        # Evaluate with LLM
        evaluation_text, result = evaluate_answer(question_text, response_text)
        score = result.get("score")
        verdict = result.get("verdict")

    # Store response in DB
    db_response = await crud.store_response(
        db,
        schemas.ResponseCreate(
            player_id=current_user.id,   # pulled from token
            question_id=question_id,
            response_text=response_text,
            score=score,
            llm_feedback=evaluation_text,
        ),
    )

    # Return results (frontend can render evaluation & verdict)
    return {
        "db_response": db_response,
        "evaluation": evaluation_text,
        "verdict": verdict,
        "score": score,
    }


@router.post("/{player_id}/{question_id}/feedback", response_model=schemas.ResponseOut)
async def set_response_feedback(
    player_id: int,
    question_id: int,
    feedback: schemas.ResponseFeedbackUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.PlayerBase = Depends(get_current_user_from_cookie),
):
    """
    Update like/dislike status for a response so developers can review preferences.
    """
    if current_user.id != player_id:
        raise HTTPException(status_code=403, detail="Cannot modify another player's feedback.")

    db_response = await crud.update_response_like_status(db, player_id, question_id, feedback.liked)
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found.")
    return db_response


@router.get("/feedback", response_model=list[schemas.ResponseOut])
async def list_response_feedback(
    liked: bool | None = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """
    List stored response feedback with optional like/dislike filter.
    """
    db_responses = await crud.list_response_feedback(db, liked)
    return db_responses
