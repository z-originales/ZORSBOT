# BUILDER stage
FROM python:3.13-slim-bookworm AS builder
LABEL authors="ZEN"
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only the necessary files for Poetry to install dependencies
COPY pyproject.toml poetry.lock ./

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1\
    POETRY_VIRTUALENVS_CREATE=1\
    POETRY_CACHE_DIR='/tmp/poetry_cache'

# Install the dependencies
RUN poetry install --no-root && rm -rf /tmp/poetry_cache

# APP stage
FROM python:3.13-slim-bookworm AS app
LABEL authors="ZEN"
WORKDIR /app

RUN mkdir -p /backups

RUN apt update && apt install libssl-dev -y

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Set the PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# set python unbuffered so that the output is printed to the console
ENV PYTHONUNBUFFERED=1

# Set the environment variables for the application folder and backup folder
ENV APP_FOLDER=/app
ENV BACKUP_FOLDER=/backups

# Copy the application files
## volumes aimed folders
RUN mkdir cogs
RUN mkdir -p /backups
COPY /cogs /backups/cogs
COPY assets/ /backups/assets
RUN mkdir logs

## application files
COPY prisma/ prisma/
COPY utils/ utils/
COPY main.py main.py

## Volumes declaration
VOLUME /app/cogs
VOLUME /app/logs
VOLUME /app/assets

# Generate Prisma client , Generating it here to avoid generating it in every container and make the run faster
RUN prisma generate

# Copy the entrypoint script
COPY entrypoint.sh entrypoint.sh
# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]