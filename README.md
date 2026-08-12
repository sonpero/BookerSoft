# BookerSoft
A personal ebook library: upload EPUB/PDF, browse metadata, rate and
review, search and filter, all from a browser. See `CLAUDE.md` for the
full spec and milestone plan.

## Setup

```
uv sync
cd frontend && npm install
```

## Frontend

The frontend lives in `frontend/` (React + Vite + TypeScript) and builds
into `src/bookersoft/static/`, which FastAPI serves directly — that
output directory is gitignored (regenerated, not versioned), so it must
be built at least once before the server has anything to serve:

```
cd frontend && npm run build
```

For frontend development with hot reload:

```
cd frontend && npm run dev
```

This runs a Vite dev server on `:5173` that proxies API/auth requests to
the FastAPI backend on `:8000` (start that separately, see below). Visit
`:5173`, not `:8000`, while developing.

## Configuration

Environment variables:

- `DATA_DIR` — where the database, book files and covers live. Defaults
  to `./data` in dev. Point it at a mounted volume in deployment.
- `SESSION_SECRET` — secret key used to sign session cookies. Required;
  the app raises an error on first use if it's missing. Never commit it.

## Running

```
DATA_DIR=./data SESSION_SECRET=<a-long-random-value> uv run uvicorn bookersoft.main:app --reload
```

The app is invite-only: there is no self-signup. Before anyone can log
in, the owner must create at least their own account with the CLI below.

## Managing user accounts

Accounts are created and reset from the command line — never through the
app itself:

```
DATA_DIR=./data uv run bookersoft-users <username> [--owner]
```

- Prompts for a new password (twice, hidden input).
- If the username doesn't exist yet, it's created. If it already exists,
  its password is reset — same command either way.
- `--owner` grants library-owner privileges (can delete any book, not
  just their own uploads). Omitting `--owner` on a later password reset
  never revokes ownership from an account that already has it.

There is no self-service password reset: if someone forgets their
password, the owner runs this command again for their username.

## Tests

```
uv run pytest
```
