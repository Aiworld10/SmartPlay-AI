from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request  # Add Request here
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from model import models
from model import schemas, crud
from model.database import get_session


# tags is for grouping in docs
router = APIRouter(prefix="/players", tags=["players"])
templates = Jinja2Templates(directory="templates")


@router.get("/id/{player_id}", response_class=HTMLResponse)
async def fetch_player_by_id(
    player_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Retrieve player details and responses safely for Jinja rendering."""
    result = await db.execute(
        select(models.Player)
        .options(
            selectinload(models.Player.responses)
            .selectinload(models.Response.question)
        )
        .where(models.Player.id == player_id)
    )
    player = result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    responses = [
        {

            "response_text": r.response_text,
            "score": r.score,
            "created_at": r.created_at,
            "llm_feedback": r.llm_feedback,
            "question_theme": r.question.theme if r.question else None,
            "question_text": r.question.question_text if r.question else None,
        }
        for r in player.responses
    ]

    return templates.TemplateResponse(
        "player_detail.html",
        {
            "request": request,
            "player": player,
            "responses": responses,
            "username": player.name,
            "user_id": player.id,
        }
    )


@router.get("/{player_id}/responses", response_model=list[schemas.ResponseOut])
async def get_player_responses(player_id: int, db: AsyncSession = Depends(get_session)):
    """Retrieve all responses linked to a specific player."""
    return await crud.get_responses_by_player(db, player_id)


@router.post("/{player_id}/responses/reset", response_model=schemas.PlayerOut)
async def reset_player_responses(player_id: int, db: AsyncSession = Depends(get_session)):
    """Delete all responses associated with a specific player and reset score to 0."""
    # Delete all responses
    deleted_count = await crud.reset_user_responses(db, player_id)

    # Reset player score to 0
    updated_player = await crud.reset_player_scores(db, player_id)

    if not updated_player:
        raise HTTPException(status_code=404, detail="Player not found")

    return updated_player
