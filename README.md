# BOUM

A web application for the BOUM project. Researchers can create experiments, upload videos of their plants, and attach structured metadata to each recording. It also supports transcribing audio notes via an external speech-to-text service and extracting metadata fields from the transcript using an LLM.

## Architecture

The application is composed of four containers, all connected via a bridge network:

- **backend** -- Flask REST API (Python 3.12, served by gunicorn with 4 workers). Handles authentication, experiment/video/metadata CRUD, and proxies audio to external AI services for transcription and metadata extraction.
- **frontend** -- SvelteKit app (Node.js, built with pnpm). Provides the web UI.
- **video_processor** -- A lightweight Python worker that polls the database for newly uploaded videos and runs them through a validation/processing pipeline (multiprocessing, 4 workers).
- **nginx** -- Reverse proxy (nginx:alpine). Routes `/api/` to the backend and everything else to the frontend. Allows uploads up to 500 MB.

Nginx is the only container with published ports. The backend and frontend are only reachable through it.

```
Client
  |
  v
nginx (:8000 -> :80)
  |
  ├── /api/*  -->  backend (:8000)
  └── /*      -->  frontend (:3000)

backend + video_processor share:
  - SQLite database (WAL mode, mounted from host)
  - Video upload directory (mounted from host)
```

The database is SQLite, stored on a bind-mounted host directory. Both the backend and the video processor access it concurrently using WAL journal mode.

## External services

The audio transcription and metadata extraction features depend on a GPUStack instance (or any OpenAI-compatible API). Two endpoints are used:

- A speech-to-text endpoint (default model: `faster-whisper-large-v3`)
- A chat completions endpoint (default model: `gpt-oss-120b`)

These are optional. The rest of the application works without them, but the audio-to-metadata feature will not.

## Configuration

Copy `env.example` to `.env` and edit it:

```sh
cp env.example .env
```

The variables:

| Variable | Purpose | Default |
|---|---|---|
| `VIDEO_INPUT_DIR` | Path inside the containers where videos are stored | `/tmp/upload` |
| `VIDEO_DIR_PATH` | Path on the host for video storage | `/tmp/videos` |
| `DATABASE_LOCAL_DIR` | Path on the host for the SQLite database | `./db_data` |
| `DATABASE_DEST_DIR` | Mount point inside the containers for the database | `/db_data` |
| `DATABASE_DEST_URL` | Database file path inside the container | `/db_data/app.db` |
| `JWT_SECRET_KEY` | Secret used to sign JWT tokens. Change this. | `very_secret_secret_key` |
| `ADMIN_PASSWORD` | Password for the default `admin` user, created on first startup | `adminpass` |
| `GPUSTACK_API_TOKEN` | Bearer token for the upstream AI service | (none) |
| `SPEECH_UPSTREAM_URL` | URL of the speech-to-text API | (none) |
| `COMPLETIONS_UPSTREAM_URL` | URL of the chat completions API | (none) |

At minimum, you should change `JWT_SECRET_KEY` and `ADMIN_PASSWORD` before running in any non-local context.

## Running with Podman

Make sure you have `podman` and `podman-compose` installed.

1. Create the `.env` file as described above.

2. Create the host directories for data persistence:

```sh
mkdir -p db_data
mkdir -p /tmp/videos   # or whatever you set VIDEO_DIR_PATH to
```

3. Build and start all services:

```sh
podman-compose up --build -d
```

The application will be available at `http://localhost:8000`. Log in with the username `admin` and the password you set in `ADMIN_PASSWORD`.

To stop everything:

```sh
podman-compose down
```

To view logs:

```sh
podman-compose logs -f
```

## API

The backend exposes a JSON REST API under `/api/`. Documentation can be found at `/api/doc`

See `backend/README.md` for more info.

## Development

To run just the backend services while developing the frontend locally:

```sh
podman-compose up backend video_processor nginx -d
```

Then, in the `frontend/` directory:

```sh
pnpm install
pnpm dev
```

The frontend dev server will need the backend accessible through nginx at `localhost:8000`.
