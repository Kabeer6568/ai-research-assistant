# AI Research Assistant

A FastAPI backend foundation with a static research-desk frontend, user accounts,
PDF upload and extraction, conversation persistence, and clearly isolated RAG
service interfaces.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `SECRET_KEY` to a private random value
   of at least 32 characters. Keep `.env` out of source control.
4. Start the API: `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000/docs` for the API and `frontend/index.html` for
   the current standalone frontend prototype.

The database defaults to a local SQLite file under `data/`. Uploaded PDFs are
stored under `data/uploads/`; extracted text is associated with the document
record. Uploads are limited by `MAX_UPLOAD_SIZE_MB`.

## API foundation

- `POST /api/auth/register` and `POST /api/auth/login`
- `POST /api/documents/upload` and `GET /api/documents/` (bearer token required)
- `POST /api/conversations/` and `GET /api/conversations/` (bearer token required)
- `POST /api/chat/` (bearer token required)
- `GET /health`

Chat deliberately returns HTTP 503 until embedding, vector-store, and language
model providers are configured in `app/services/`. The current frontend is
still a prototype and is not yet wired to these API endpoints.

## Tests

Run `pytest`.

## Docker

Build with `docker build -t ai-research-assistant .`, then run with a secure
`SECRET_KEY` environment variable. Mount `data/` as a persistent volume when
running the container.
