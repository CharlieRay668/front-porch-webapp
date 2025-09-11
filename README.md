# Volunteer Signup App

Fast to develop, easy to deploy web app using FastAPI + SQLite.

- Single-page grid: Monday-Sunday columns, hours 7am–11pm rows
- Friday 7–4 only, Sunday 9–5 only, Saturday unavailable (dimmed in UI)
- Each hour/day cell holds up to 3 volunteers; shows spots left
- Click a cell to sign up (name, email, phone). Names shown publicly; contact info hidden.
- Admin login to view/manage signups

## Quickstart

1. Create and activate a virtual environment (optional but recommended)

   macOS/Linux (zsh):

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Run the server using your venv’s Python:

   ```sh
   .venv/bin/python -m uvicorn app.main:app --reload
   ```

4. Open http://127.0.0.1:8000/

Admin: http://127.0.0.1:8000/admin (username: frontporchadmin, password: toomanymugs)

## Docker

Build and run:

```sh
docker build -t volunteer-app .
docker run -p 8000:8000 volunteer-app
```

Or with Makefile:

```sh
make build
make run PORT=8000
make logs
# Stop and clean
make stop
make clean
```

## Database

- SQLite file lives at `app/volunteers.db` (gitignored).
- Reset locally:

```sh
make db-reset
```

## Deploy

- The provided Dockerfile runs `uvicorn app.main:app` on port 8000.
- Works on most container platforms (Fly.io, Railway, Azure App Service, etc.).

