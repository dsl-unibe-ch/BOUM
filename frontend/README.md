# BOUM frontend

## development

- you need the .env variables and the db in /db_data/app.db
- start the backend api and database in WSL environment:
  - `docker-compose build --no-cache backend`
  - `docker-compose up backend video_processor nginx` in root
- start dev in /frontend:
  - `pnpm install`
  - `pnpm dev`
