FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /bot

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /bot/

RUN poetry install --no-root

COPY . /bot/

CMD ["python", "-m", "app.main"]