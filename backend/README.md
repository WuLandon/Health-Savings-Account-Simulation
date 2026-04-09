# Backend Setup

## 1) Create local env file

From repository root:

```bash
cp .env.example .env
```

## 2) Run with Docker Compose (recommended)

From repository root:

```bash
docker compose up --build
```

API will be available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

## 3) Alembic migrations

Run Alembic from the `backend/` directory:

```bash
cd backend
alembic revision -m "init" --autogenerate
alembic upgrade head
```

## 4) Optional local (non-Docker) run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
