# Copilot Instructions — BOUM

## Architecture

BOUM is a video processing and experiment management platform with four Docker Compose services behind an Nginx reverse proxy:

- **frontend** — SvelteKit 2 / Svelte 5 with `adapter-node`, CSR-only (`ssr = false`), port 3000
- **backend** — Flask 3 + SQLAlchemy 2 + SQLite (WAL mode), JSON API at port 8000, all routes under `/api/*`
- **video_processing_worker** — Python multiprocessing poller (4 workers) that advances videos through `PENDING → PROCESSING → PROCESSED | FAILED`. Uses atomic conditional updates to prevent race conditions.
- **nginx** — reverse proxy: `/` → frontend, `/api/*` → backend

### Authentication flow

JWT (HS256, 24h expiry) issued by `POST /api/auth/login`. The frontend stores the token in `localStorage` and injects it via `authFetch()` (`$lib/auth.svelte.ts`). The backend enforces auth with `@require_authentication` and optionally `@require_admin` decorators — these inject `(user_id, role)` as the first two positional args of the route handler.

### Data model

- **User** — id, username (unique), pw_hash (bcrypt), role (`0=ADMIN`, `1=USER`), M2M experiments
- **Experiment** — id, name, O2M videos, M2M users
- **Video** — id, filename, path, status (IntEnum 0–3), FK experiment

### API blueprints

Registered in `backend/app/__init__.py`: `/api/auth`, `/api/user`, `/api/video`, `/api/audio`, `/api/experiment`. Swagger docs at `/api/docs/`.

## Frontend

### Commands

```sh
pnpm dev          # dev server
pnpm build        # production build
pnpm check        # svelte-check + TypeScript
pnpm lint         # prettier --check + eslint
pnpm format       # prettier --write
```

### Conventions

- **Svelte 5 runes** — use `$state()`, `$props()`, `$derived()`, `{@render children()}`. Do not use Svelte 4 stores or `$:` reactive declarations.
- **Styling** — Tailwind CSS 4 utilities + Skeleton UI v4 presets (e.g. `preset-filled-surface-500`, `preset-outlined-surface-200-800`).
- **Formatting** — tabs, single quotes, no trailing commas, 100 char width (`.prettierrc`).
- **API calls** — always use `authFetch()` from `$lib/auth.svelte.ts` with URLs built from `API_BASE_URL` (`$lib/constants.js`).
- **Role-based UI** — admin is `role === 0`, regular user is `role === 1`.
- **Page data loading** — use `PageLoad` / `LayoutLoad` in `+page.ts` / `+layout.ts` (not server files — SSR is disabled).

## Backend

### Commands

```sh
cd backend
python run.py                              # dev server on port 8000
pytest                                     # all tests
pytest tests/test_login.py                 # single test file
pytest tests/test_login.py -k "test_name"  # single test by name
```

### Conventions

- **SQLAlchemy 2.0 style** — `Mapped[]`, `mapped_column()`, `db.select()`. Do not use the legacy `Query` API.
- **Route pattern** — Flask Blueprints. Stack `@require_authentication` (outermost), then optionally `@require_admin`. These inject `(user_id, role)` before other route args.
- **Request validation** — Pydantic `BaseModel` DTOs in `app/schemas.py`, applied via `@validate_body(SchemaClass)`.
- **Swagger** — OpenAPI 3.0 YAML docstrings on route handlers, rendered by Flasgger at `/api/docs/`.
- **Tests** — pytest with in-memory SQLite (`StaticPool`). Fixtures in `conftest.py` provide `app`, `client`, `admin_token`, `experiment`, `member_user`, etc.

## Development setup

1. Copy `env.example` → `.env` and fill in secrets
2. Start backend services: `docker-compose up backend video_processor nginx`
3. In `frontend/`: `pnpm install && pnpm dev`

The frontend dev server talks directly to `http://127.0.0.1:8000/api` (hardcoded in `$lib/constants.js`). In production, Nginx proxies `/api/*` to the backend container.
