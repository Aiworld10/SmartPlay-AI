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

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


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
@router.post("/login", response_class=HTMLResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Return the index page with error message for HTMX
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
                "error_message": "Incorrect username or password. Please try again."
            }
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        {"sub": user.name, "id": user.id},
        expires_delta=access_token_expires,
    )

    # Create response with redirect header for HTMX
    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "success_message": f"Welcome back, {user.name}!"
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        samesite="Lax",
        secure=secure,   # Set to True in production with HTTPS
    )
    # Add HX-Redirect header to redirect after successful login
    response.headers["HX-Redirect"] = "/auth/theme-selection"
    return response


@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": None,
            "success_message": "You have been logged out successfully."
        }
    )
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="Lax",
        secure=secure,  # match your cookie set flags
        path="/",
    )
    return response


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password1: str = Form(...),
    password2: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    print(f"Registering user: {username}")

    # Validate passwords match
    if password1 != password2:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
                "error_message": "Passwords do not match. Please try again."
            }
        )

    # Validate password length
    if len(password1) < 6:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
                "error_message": "Password must be at least 6 characters long."
            }
        )

    # Validate username length
    if len(username) < 3:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
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
                    "error_message": "Registration failed. Username might already exist."
                }
            )

        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
                "success_message": f"Account created successfully for {username}! You can now log in."
            }
        )
    except Exception as e:
        print(f"Registration error: {e}")
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "user": None,
                "error_message": "Registration failed. Username might already exist."
            }
        )


@router.get("/theme-selection", response_class=HTMLResponse)
async def theme_selection(
    request: Request,
    current_user: schemas.PlayerBase = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_session),
):
    return templates.TemplateResponse(
        request,
        "theme_selection.html",
        {
            "username": current_user.name,
            "user_score": current_user.score,
        },
    )
