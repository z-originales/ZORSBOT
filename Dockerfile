FROM python:3.13-slim-bookworm
LABEL authors="ZEN"
WORKDIR /app

RUN apt update && apt install libssl-dev -y

RUN groupadd -g 10000 bot && useradd -u 10000 -g 10000 -r -d /app -s /bin/false bot && chown -R bot:bot /app

USER bot

RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -Ur requirements.txt

RUN mkdir assets
COPY assets/ assets/
RUN mkdir cogs
COPY cogs/ cogs/
RUN mkdir logs
COPY prisma/ prisma/
COPY utils/ utils/
COPY main.py main.py

RUN prisma generate

ENTRYPOINT ["python", "main.py"]


