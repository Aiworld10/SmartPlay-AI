# SmartPlay-AI

SmartPlay AI is a chat-based simulation platform that uses large language models (LLMs) to generate dynamic scenarios across survival, school, work, social, and moral themes.

# Choices on tech stack

Model: - meta-llama/Llama-3.1-8B-Instruct (use hugging face token )
Web Framework: - FastAPI, HTMX
Database: - SQLAlCHEMY (ORM no query), PostgreSQL
Host Provider: - Railway, vercel and render
optional - Inference API for LLM models (free tier), aws, azure - Docker
Ollama - download the LLM locally, expose API
authetication - JWT and httponly cookie

# To clone and set up:

- pip install uv
  uv sync --locked

- Create an .env file at root
  paste in what you need

- uv run main.py

  To visit the website access: localhost:8080
