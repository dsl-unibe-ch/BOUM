#!/bin/bash
set -e

python -c "from app import create_app, setup_db; app=create_app(); setup_db(app)"
exec gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"