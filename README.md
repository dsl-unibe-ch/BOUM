# BOUM

A web application for the BOUM project. Researchers can create experiments, upload videos of their plants, and attach structured metadata to each recording. It also supports transcribing audio notes via an external speech-to-text service and extracting metadata fields from the transcript using an LLM.

## Architecture

The application is composed of four containers, all connected via a bridge network:

- **backend** -- Flask REST API (Python 3.12, served by gunicorn with 4 workers). Handles authentication, experiment/video/metadata CRUD, and proxies audio to external AI services for transcription and metadata extraction.
- **frontend** -- SvelteKit app (Node.js, built with pnpm). Provides the web UI.
- **video_processor** -- A lightweight Python worker that polls the database for newly uploaded videos and runs them through a validation/processing pipeline (multiprocessing, 4 workers).
- **caddy** -- Reverse proxy (caddy:alpine). Routes `/api/` to the backend and everything else to the frontend. Terminates TLS. Allows uploads up to 500 MB.

Caddy is the only container with published ports (80 and 443). The backend and frontend are only reachable through it.

```
Client
  |
  v
caddy (:80, :443)
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

Copy `.env.example` to `.env` and fill in the values:

```sh
cp .env.example .env
```

Each variable is documented with a comment in `.env.example`.

At minimum, set `JWT_SECRET_KEY` and `ADMIN_PASSWORD` before running in any non-local context.

## TLS certificates

Caddy expects a certificate and key at `./certs/plant3d.ips.unibe.ch.pem` and `./certs/plant3d.ips.unibe.ch.key` (as configured in the `Caddyfile`). Create the directory and place the files there before starting:

```sh
mkdir -p certs
# copy your cert and key into certs/
```

## Running with Podman

Make sure you have `podman` and `podman-compose` installed.

1. Create the `.env` file as described above.

2. Place TLS certificates in `./certs/` as described above.

3. Create the host directories for data persistence (adjust paths to match your `.env`):

```sh
mkdir -p db_data
```

4. Build and start all services:

```sh
podman-compose up --build -d
```

The application will be available at `https://plant3d.ips.unibe.ch`. Log in with the username `admin` and the password you set in `ADMIN_PASSWORD`.

To stop everything:

```sh
podman-compose down
```

To view logs:

```sh
podman-compose logs -f
```

## API

The backend exposes a JSON REST API under `/api/`. Documentation (Swagger UI) is available at `/api/docs/`.

See `backend/README.md` for more info.

## Development

To run just the backend services while developing the frontend locally:

```sh
podman-compose up backend video_processor caddy -d
```

Then, in the `frontend/` directory:

```sh
pnpm install
pnpm dev
```

The frontend dev server will need the backend accessible through Caddy.
