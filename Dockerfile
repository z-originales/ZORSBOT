# BUILDER stage
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder
LABEL authors="ZEN"
WORKDIR /app

# Copy only the necessary files for UV to install dependencies
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-cache --no-dev --compile-bytecode --no-install-project

# APP stage
FROM python:3.13-alpine AS app
LABEL authors="ZEN"
WORKDIR /app

# Install the necessary system packages, need to find a way to not use bash in alpine image (for faster startup)
RUN apk update && apk add --no-cache --upgrade openssl-dev bash postgresql-client

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Set the PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# set python unbuffered so that the output is printed to the console
ENV PYTHONUNBUFFERED=1

# Copy the application files
## volumes aimed folders
COPY cogs cogs
COPY assets/ assets/
RUN mkdir logs

## application files
COPY alembic/env.py alembic/env.py
COPY alembic/script.py.mako alembic/script.py.mako
RUN mkdir alembic/versions
COPY alembic.ini alembic.ini
COPY config/ config/
COPY model/ model/
COPY utils/ utils/
COPY main.py main.py

## Volumes declaration
VOLUME /app/cogs
VOLUME /app/logs
VOLUME /app/assets


# Copy the entrypoint script
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]