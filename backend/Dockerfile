FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY backend/pyproject.toml backend/poetry.lock* /app/

RUN poetry install --no-root

COPY backend/ /app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]