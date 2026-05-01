FROM docker.io/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir SQLAlchemy paramiko

COPY ./app ./app

# RUN useradd -u 1000 --user-group --no-create-home --shell /usr/sbin/nologin app
# USER app

CMD ["python", "-m", "app.main"]
