# SmartPlay-AI

SmartPlay AI is a dynamic, chat-based simulation platform that leverages large language models (LLMs) to generate immersive scenarios across survival, school, work, social, and moral themes. Users make choices that shape the narrative, creating a unique interactive experience.

## Tech Stack

- **LLM Model**: qwen3:14b (via Hugging Face token)
- **Web Framework**: FastAPI + HTMX for dynamic UI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Hosting**: Railway

**Optional Features:**

- Inference API (free tier) via AWS, Azure, or Ollama (local LLM)
- Docker for containerization

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Aiworld10/SmartPlay-AI
cd SmartPlay-AI
```

### 2. Install Dependencies

```bash
pip install uv
uv sync --locked
```

### 3. Configure Environment

Create a `.env` file at the project root:

```env
contact us for env key
example:
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_PUBLIC_URL=postgresql+asyncpg://postgres:
PUBLIC_ALEMBIC_URL=postgresql+psycopg2://postgres:

SERVEO_HOST=

```

Replace placeholders with your actual credentials.

### 4. Run the Application

```bash
uv run main.py
```

### 5. Access the App

Visit [http://localhost:8080](http://localhost:8080) in your browser.

## File Structure

```
smartplay-ai/
├── routers/              # API endpoints for CRUD operations (players, questions, responses, auth)
├── models/               # Database schemas, ORM definitions, and connection logic
│   └── crud.py           # Database operations (create, read, update, delete)
├── templates/            # HTML files for the frontend
├── static/               # Static assets (JSON files, images)
├── utils/                # Helper functions (e.g., `fetchLLMresponse.py`)
├── seed_questions.py     # Script to populate the database from `static/questions.json`
├── clear_questions.py    # Script to reset the database
├── main.py               # FastAPI application entry point
└── .env.example          # Example environment variables
```

## Key Features

- **Dynamic Scenario Generation**: LLM-driven narratives that adapt to user choices.
- **Modular Architecture**: Separation of concerns between API, database, and frontend.
- **Scalable Hosting**: Deploy on Railway, Vercel, or Render with ease.
- **Cost-Optimized Inference**: Optional local GPU setup (via Ollama) to avoid Hugging Face costs.

## Contributing

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Submit a pull request

## testing

1. uv run pytest -v

## License

This project is licensed under the MIT License. See the LICENSE file for details.
