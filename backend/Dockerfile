FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser
WORKDIR /home/appuser/app

USER appuser
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user gunicorn

COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["/bin/bash", "entry.sh"]