FROM python:3.12.2-slim-bookworm
LABEL authors="ZEN"

WORKDIR /app

RUN pip install poetry
RUN useradd -r -d /app -s /bin/false bot && chown -R bot:bot /app

USER bot

COPY utilities/ classes/
COPY main.py ./
COPY pyproject.toml ./

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "main.py"]