FROM docker.io/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY . .

# RUN useradd -u 1000 --user-group --no-create-home --shell /usr/sbin/nologin app
# USER app

EXPOSE 8000

CMD ["/bin/bash", "entry.sh"]
