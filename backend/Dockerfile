# backend/Dockerfile

# ---- Base Stage ----
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

# System dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# ---- Builder Stage ----
FROM base as builder

# Install dependencies
RUN poetry install --no-root --no-dev

# ---- Runtime Stage ----
FROM base as runtime

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/.venv /app/.venv
# Copy application code
COPY . /app

# Ensure the start.sh script has execution permissions
RUN chmod +x /app/start.sh

# Expose application port
EXPOSE 8000

# Add a healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/api/v1/healthcheck || exit 1

# Default command
CMD ["/app/start.sh"]