FROM docker.io/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --user SQLAlchemy

COPY main.py .

CMD ["python", "main.py"]
