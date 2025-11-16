import os
from pathlib import Path
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
from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from model import crud, schemas
from model.database import get_session

# ---------------------------
# Setup
# ---------------------------
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "hgaghagahgagahgwfagahgawf")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Check if we're in production (Railway sets this)
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

request = Request  # For type hinting in dependencies

secure = True if os.getenv("ENV") == "production" else False

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


async def authenticate_user(db: AsyncSession, username: str, password: str) -> schemas.PlayerRead | None:
    user = await crud.get_player_by_name(db, username)
    if not user or not verify_password(password, str(user.password_hash)):
        return None
    return schemas.PlayerRead.model_validate(user)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def _get_user_from_token(token: str, db: AsyncSession) -> schemas.PlayerRead:
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
    return schemas.PlayerRead.model_validate(user)


# ---------------------------
# Dependencies
# ---------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
):
    return await _get_user_from_token(token, db)


async def get_current_user_from_cookie(
    request: request,
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
async def login_for_access_token(request: Request,
                                 username: str = Form(...),
                                 password: str = Form(...),
                                 db: AsyncSession = Depends(get_session)):

    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error_message": "Incorrect username or password."
        })

    access_token = create_access_token({"sub": user.name, "id": user.id})

    response = RedirectResponse(url="/auth/theme-selection", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=secure
    )
    return response


@router.post("/logout")
async def logout(request: request):
    """Log out user by deleting cookie and redirecting to home page."""
    # Use RedirectResponse to go back to /
    response = RedirectResponse(url="/", status_code=303)

    # Delete the cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )

    return response


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: request,
    username: str = Form(...),
    password1: str = Form(...),
    password2: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    print(f"Registering user: {username}")

    # Validate passwords match
    if password1 != password2:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": None,
                "username": None,
                "error_message": "Passwords do not match. Please try again."
            }
        )

    # Validate password length
    if len(password1) < 6:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": None,
                "username": None,
                "error_message": "Password must be at least 6 characters long."
            }
        )

    # Validate username length
    if len(username) < 3:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": None,
                "username": None,
                "error_message": "Username must be at least 3 characters long."
            }
        )

    try:
        player = await crud.create_player(
            db,
            schemas.PlayerCreate(name=username),
            password1,
        )
        if not player:
            return templates.TemplateResponse(
                request,
                "index.html",
                {
                    "user": None,
                    "username": None,
                    "error_message": "Registration failed. Username might already exist."
                }
            )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": None,
                "username": None,
                "success_message": f"Account created successfully for {username}! You can now log in."
            }
        )
    except Exception as e:
        print(f"Registration error: {e}")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": None,
                "username": None,
                "error_message": "Registration failed. Username might already exist."
            }
        )


@router.get("/theme-selection", response_class=HTMLResponse)
async def theme_selection(
    request: request,
    current_user: schemas.PlayerRead = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_session),
):
    return templates.TemplateResponse(
        "theme_selection.html",
        {
            "request": request,
            "user": current_user,
            "username": current_user.name,
            "user_id": current_user.id,
            "user_score": current_user.score,
        },
    )
