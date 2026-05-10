FROM python:3.11-slim

WORKDIR /app

COPY app/ /app/

RUN pip install --no-cache-dir \
    python-telegram-bot \
    flask \
    requests \
    docker \
    psutil \
    qdrant-client

CMD ["python", "bot.py"]
