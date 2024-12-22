FROM python:3.13-slim-bookworm
LABEL authors="ZEN"
WORKDIR /app

RUN apt update && apt install libssl-dev -y

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


