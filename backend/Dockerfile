FROM docker.io/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user gunicorn

COPY . .

RUN mkdir -p ${UPLOAD_FOLDER:-/data/input}

EXPOSE 8000

CMD ["/bin/bash", "entry.sh"]
