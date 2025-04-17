FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY promptos_backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY promptos_backend /app

# Cria user não‑root (Railway usa UID 1000 por default)
RUN adduser --disabled-password --gecos '' appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "promptos_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
