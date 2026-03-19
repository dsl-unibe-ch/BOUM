# Backend

Flask REST API with SQLite, JWT authentication, and video processing.

## Setup
See `entry.sh`.

## API Docs

Swagger UI is available at `/apidocs` when the server is running.

## Architecture

```
app/
├── routes/
│   ├── auth.py          # Login
│   ├── users.py         # User management
│   ├── experiments.py   # Experiments, membership, video upload
│   ├── videos.py        # Admin video listing
│   └── audio.py         # Audio analysis (upstream LLM)
├── models.py            # SQLAlchemy models (User, Video, Experiment)
├── extensions.py        # DB setup
├── constants.py         # Enums, config constants
├── config.py            # App configuration
├── schemas.py           # Request validation DTOs
└── utils.py             # Auth decorators, JWT helpers
```

## Permissions

### Access levels

Every endpoint requires one of the following:

- **Public** -- no token needed. Only the login endpoint.
- **Authenticated** -- any valid JWT, regardless of role.
- **Participant** -- the caller must be a member of the specific experiment being accessed, or an admin. Admins implicitly satisfy all participant checks.
- **Admin** -- the caller must have the admin role.

### Anti-enumeration

All experiment-scoped endpoints return `404` both when the experiment does not exist and when the caller is not a participant. This prevents unauthenticated or unauthorized users from discovering valid experiment IDs.

### What each level can do

**Authentication**

Login is the only public endpoint. It returns a JWT (24h, HS256).

**User management (admin only)**

Creating users, listing users, and looking up a user by ID all require admin. The one exception is `/api/user/me`, which any authenticated user can call to see their own info.

**Experiment lifecycle (authenticated)**

Any authenticated user can create an experiment. The creator is automatically added as the first participant. Listing all experiments in the system is admin-only; regular users can only list the experiments they belong to.

**Experiment operations (participant)**

Participants (and admins) can:

- View, update, and delete the experiment
- Upload, view, download, and delete videos
- Read and set experiment-level metadata defaults
- Read and set per-video metadata
- Add other users to the experiment

Removing a user from an experiment is admin-only.

**Audio transcription (authenticated)**

The audio endpoint is a stateless service proxy. Any authenticated user can send an audio file for transcription and metadata extraction, independent of experiment membership.

### Design notes

- There is no "owner" concept on experiments. All participants have equal privileges, including deletion. This may be revisited in the future.
- Experiment deletion cascades to metadata (experiment defaults and video metadata are removed), but the video records themselves are detached, not deleted.
- The video processing worker operates outside the HTTP permission model. It accesses the shared SQLite database directly.
