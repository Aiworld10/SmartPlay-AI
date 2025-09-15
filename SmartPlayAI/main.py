from pyexpat import model
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import pipeline  # local dev
from huggingface_hub import InferenceClient  # inference API for production
import random

from router import players, questions, responses, authenticate


app = FastAPI(title="SmartPlayAI", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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


# ----------- ROUTES ------------

@app.get("/generate_question", response_class=HTMLResponse)
async def generate_question_form(request: Request):
    """Generate a random question and display it for user approval."""
    selected_theme = random.choice(THEMES)
    generated_question = generate_question(selected_theme)

    return templates.TemplateResponse("form.html", {
        "request": request,
        "question": generated_question,
        "theme": selected_theme
    })


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """Render the main index page."""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
