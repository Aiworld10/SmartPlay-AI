from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from model import schemas, crud
from model.database import get_session


# tags is for grouping in docs
router = APIRouter(prefix="/players", tags=["players"])


@router.get("/id/{player_id}", response_model=schemas.PlayerOut)
async def fetch_player_by_id(player_id: int, db: AsyncSession = Depends(get_session)):
    """Retrieve a player by ID or raise 404 if not found."""
    db_player = await crud.get_player(db, player_id)
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    return db_player


@router.get("/{player_id}/responses", response_model=list[schemas.ResponseOut])
async def get_player_responses(player_id: int, db: AsyncSession = Depends(get_session)):
    """Retrieve all responses linked to a specific player."""
    return await crud.get_responses_by_player(db, player_id)
