import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import (
    APIRouter, Depends, Form, Request, Response, HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from model import crud, schemas
from model.database import get_session

# ---------------------------
# Setup
# ---------------------------
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY","hgaghagahgagahgwfagahgawf")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------
# Schemas
# ---------------------------
class TokenData(BaseModel):
    username: str | None = None


class RegisterForm(BaseModel):
    username: str = Field(..., min_length=3)
    password1: str = Field(..., min_length=6)
    password2: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password1 != self.password2:
            raise ValueError("Passwords do not match")
        return self

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password1: str = Form(...),
        password2: str = Form(...),
    ):
        return cls(username=username, password1=password1, password2=password2)


# ---------------------------
# Helpers
# ---------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await crud.get_player_by_name(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def _get_user_from_token(token: str, db: AsyncSession) -> schemas.PlayerBase:
    """Decode JWT and fetch user from DB."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await crud.get_player_by_name(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------
# Dependencies
# ---------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
):
    return await _get_user_from_token(token, db)


async def get_current_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await _get_user_from_token(token, db)


# ---------------------------
# Routes
# ---------------------------
@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        {"sub": user.name, "id": user.id},
        expires_delta=access_token_expires,
    )

    response = RedirectResponse(url="/auth/theme-selection", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        samesite="Lax",
        secure=False,   # Set to True in production with HTTPS
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="Lax",
        secure=False,  # match your cookie set flags
        path="/",
    )
    return response


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    form_data: RegisterForm = Depends(RegisterForm.as_form),
    db: AsyncSession = Depends(get_session),
):
    print(f"Registering user: {form_data.username}")

    player = await crud.create_player(
        db,
        schemas.PlayerCreate(name=form_data.username),
        form_data.password1,
    )
    if not player:
        raise HTTPException(
            status_code=400, detail="Player registration failed")

    return RedirectResponse(url="/", status_code=303)


@router.get("/theme-selection", response_class=HTMLResponse)
async def theme_selection(
    request: Request,
    current_user: schemas.PlayerBase = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_session),
):
    return templates.TemplateResponse(
        "theme_selection.html",
        {
            "request": request,
            "username": current_user.name,
            "user_score": current_user.score,
        },
    )
