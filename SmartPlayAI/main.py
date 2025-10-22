
import os
from pathlib import Path
from router.authenticate import _get_user_from_token
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import pipeline  # local dev
from huggingface_hub import InferenceClient  # inference API for production
import random
from model import crud as crud_ops  # to not re import in the route
from model import schemas
from model.database import get_session
from router import players, questions, responses, authenticate


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="SmartPlayAI", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(players.router)
app.include_router(questions.router)
app.include_router(responses.router)
app.include_router(authenticate.router)
# This is for local development with a downloaded model
# text_generator = pipeline(
#     "text-generation",
#     model="meta-llama/Llama-3.1-8B-Instruct",
#     dtype="bfloat16",
#     device_map="auto"
# )

# This is for production with Hugging Face Inference API
client = InferenceClient()

# Predefined themes for SmartPlay AI scenarios
THEMES = ["survival", "work", "interview"]


def generate_question(theme: str) -> str:
    prompts = {
        "survival": """
        You are a helpful assistant that creates varied survival scenario questions. Here are some examples:
        Example 1: You're stranded on a deserted island with limited food and no communication. What is your first course of action?
        Example 2: Your boat capsizes in rough seas and you wash ashore on unfamiliar land. How do you find shelter?
        Example 3: A sudden storm traps you in a mountain cabin with dwindling supplies. What critical decisions do you make?
        Now, create a new, unique survival scenario question:
        """,
        "work": """
        You are an assistant that creates engaging workplace scenario questions. Consider these examples:
        Example 1: You find a critical error in a report moments before submission. How do you handle it?
        Example 2: Your manager gives you an unrealistic deadline that conflicts with another project. What do you do?
        Example 3: A coworker takes credit for your idea in a meeting. How do you address this?
        Now, please generate a new, unique work scenario question:
        """,
        "interview": """
        You are an assistant that generates interview scenario questions. Consider these examples:
        Example 1: Describe a challenging team conflict you resolved. How did you approach it?
        Example 2: Tell me about a time you missed a deadline. What did you learn?
        Example 3: How would you handle receiving unclear instructions on a critical task?
        Now, create a fresh and original interview scenario question:
        """
    }

    fallback_questions = {
        "survival": "You're trapped in a cave with limited supplies. What's your first priority?",
        "school": "Your project partner hasn't done their part and the deadline is tomorrow. How do you handle this?",
        "work": "You discover a major error in your team's presentation 10 minutes before presenting to the CEO. What do you do?",
        "social": "You overhear someone spreading false rumors about your friend. How do you respond?",
        "moral": "You find a wallet with $500 cash and no ID. What do you do?"
    }

    try:
        user_prompt = prompts.get(theme, prompts["survival"])

        messages = [
            {
                "role": "system",
                "content": (
                    "You generate only the scenario description itself. "
                    "Do NOT end with questions like 'What would you do?' or 'How do you handle it?'. "
                    "Do NOT add labels or introductions. "
                    "Output must be a single, self-contained sentence (under 25 words) ending with a period."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            max_tokens=40,
            temperature=0.7,
        )

        generated_text = completion.choices[0].message["content"].strip()

        if not generated_text.endswith("?"):
            generated_text = generated_text.rstrip(".") + "?"

        if len(generated_text) < 10:
            return fallback_questions.get(theme, fallback_questions["survival"])

        return generated_text

    except Exception as e:
        print(f"Error generating question: {e}")
        return fallback_questions.get(theme, fallback_questions["survival"])


async def optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Optional[schemas.PlayerBase]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return await _get_user_from_token(token, db)
    except HTTPException:
        return None

# ----------- ROUTES ------------


@app.get("/generate_question", response_class=HTMLResponse)
async def generate_question_form(request: Request):
    """Generate a random question and display it for user approval."""
    selected_theme = random.choice(THEMES)
    generated_question = generate_question(selected_theme)

    return templates.TemplateResponse(request, "form.html", {
        "question": generated_question,
        "theme": selected_theme
    })


@app.get('/', response_class=HTMLResponse)
async def index(request: Request,
                current_user: Optional[schemas.PlayerBase] = Depends(optional_current_user)):
    """Render the main index page."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": current_user,
            "username": current_user.name if current_user else None,
            "user_score": current_user.score if current_user else None,
            "user_id": current_user.id if current_user else None
        }
    )


@app.get('/leaderboard')
async def get_leaderboard(
    theme: str = None,
    db: AsyncSession = Depends(get_session)
):
    """Get leaderboard data, optionally filtered by theme."""

    try:
        leaderboard_data = await crud_ops.get_leaderboard(db, theme)
        return leaderboard_data
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch leaderboard")


@app.get('/leaderboard/details')
async def get_leaderboard_details(
    theme: str = None,
    db: AsyncSession = Depends(get_session),
):
    """Fetch question, response, and score details for leaderboard review."""
    try:
        details = await crud_ops.get_leaderboard_response_details(db, theme)
        return details
    except Exception as e:
        print(f"Error fetching leaderboard details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard details")


if __name__ == "__main__":
    import uvicorn

    environment = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

    if environment == "production":
        # Production-specific config here
        # e.g., enable some monitoring, logging, feature toggles
        pass
    else:
        # Local or staging-specific config here
        pass

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
