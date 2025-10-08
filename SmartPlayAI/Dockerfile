FROM python:3.12.1-slim

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ".python-version" "uv.lock" "pyproject.toml" ./

RUN uv sync --locked

COPY . .

EXPOSE 8080

ENTRYPOINT [ "uv", "run", "python", "main.py" ]