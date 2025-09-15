from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from dotenv import load_dotenv
import os
from fastapi.params import Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from model import crud, schemas
from model.database import get_session
load_dotenv()  # Load environment variables from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")


def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(
            minutes=expires_delta if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@router.post("/login")
async def login_player_by_name(
    username: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    # Get or create player
    db_player = await crud.get_player_by_name(db, username)
    if not db_player:
        new_player = schemas.PlayerCreate(name=username)
        db_player = await crud.create_player(db, new_player)

    # Create token
    access_token = create_access_token(
        {"sub": db_player.name, "id": db_player.id})

    # Redirect to theme-selection and set token cookie
    response = RedirectResponse(url="/auth/theme-selection", status_code=302)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        max_age=3600,
        samesite="Lax",
    )
    return response


@router.get("/theme-selection", response_class=HTMLResponse)
async def theme_selection(
    request: Request,
    access_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_session),
):
    # No token at all → send back to login
    if not access_token:
        return RedirectResponse(url="/", status_code=303)

    # Decode token safely
    payload = decode_access_token(access_token)
    if not payload or "id" not in payload:
        return RedirectResponse(url="/", status_code=303)

    # Retrieve player info
    player_id = payload["id"]
    db_player = await crud.get_player(db, player_id)
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Render template
    return templates.TemplateResponse(
        "theme_selection.html",
        {
            "request": request,
            "username": db_player.name,
            "user_score": db_player.score,
            "token": access_token,
        },
    )


async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload
