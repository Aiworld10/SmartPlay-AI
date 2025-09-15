from fastapi import APIRouter, Request, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from model import schemas, crud
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
