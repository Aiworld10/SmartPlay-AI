FROM python:3.12.1-slim

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ".python-version" "uv.lock" "pyproject.toml" ./

RUN uv sync --locked --no-cache --no-dev

COPY . .

# Remove any unnecessary files
RUN find . -type d -name "__pycache__" -exec rm -rf {} + || true
RUN find . -type f -name "*.pyc" -delete || true

EXPOSE 8080

ENTRYPOINT [ "uv", "run", "python", "main.py" ]