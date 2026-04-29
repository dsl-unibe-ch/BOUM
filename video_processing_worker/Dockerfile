FROM docker.io/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --user SQLAlchemy paramiko

COPY ./app ./app

CMD ["python", "-m", "app.main"]