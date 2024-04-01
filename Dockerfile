FROM python:3.12.2-slim-bookworm
LABEL authors="lolozen"

WORKDIR /app
RUN useradd -r -d /app -s /bin/false bot
RUN chown -R bot:bot /app
USER bot
COPY *.py ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt
RUN mkdir -p /app/logs
ENTRYPOINT ["python", "main.py"]