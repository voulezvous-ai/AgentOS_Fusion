FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \ 
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential gcc curl git libffi-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY . .

RUN poetry export -f requirements.txt --output requirements.txt

RUN poetry install --no-root

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
