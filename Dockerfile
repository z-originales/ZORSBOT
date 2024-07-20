FROM python:3.12.2-slim-bookworm
LABEL authors="lolozen"

WORKDIR /app

RUN pip install poetry
RUN useradd -r -d /app -s /bin/false bot && chown -R bot:bot /app

# USER bot

RUN mkdir -p /app/logs
RUN mkdir -p /app/cogs

COPY *.py ./
COPY pyproject.toml ./

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "main.py"]