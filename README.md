# AI Research Assistant

Clarity is a private, document-grounded research workspace. Create an account,
upload text-based PDFs, and ask questions with answers grounded in retrieved
excerpts from your own documents.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Set `SECRET_KEY` to a private random value of at least 32 characters and
   set `AI_API_KEY` for your chosen AI provider. Never commit `.env`.
5. Start the app: `uvicorn app.main:app --reload`.
6. Open `http://localhost:8000/`. The interactive API documentation is at
   `http://localhost:8000/docs`.

The AI provider must expose the OpenAI-compatible `/embeddings` and
`/chat/completions` endpoints. OpenAI-compatible providers use
`AI_BASE_URL`, `AI_CHAT_MODEL`, and `AI_EMBEDDING_MODEL`.

Google Gemini uses its OpenAI-compatible endpoint for chat and Gemini's native
batch-embedding endpoint for PDF search. Set `AI_BASE_URL` to
`https://generativelanguage.googleapis.com/v1beta/openai/`,
`AI_CHAT_MODEL` to a model enabled for your Google AI Studio key,
`AI_API_KEY` to your Gemini API key, and
`AI_GEMINI_EMBEDDING_MODEL` to `gemini-embedding-001` (or another supported
Gemini embedding model).

## What it does

- Email/password registration and bearer-token sign-in.
- Private PDF upload with size, extension, and signature checks.
- Text extraction, chunking, and embedding-based indexing.
- Persistent SQLite vector chunks, scoped to their document owner.
- Similarity retrieval and answers with source excerpts.
- Saved conversations with message history, plus document and conversation
  deletion.
- One-page frontend served by FastAPI, with upload/reindex status and readable
  provider configuration errors.

Uploads are limited by `MAX_UPLOAD_SIZE_MB`. The default SQLite database and
uploaded files live under `data/`. Existing local databases receive additive
schema updates at startup. For production deployments, use managed database and
file storage with explicit backups, HTTPS, rate limiting, and reviewed schema
migrations.

## API

- `POST /api/auth/register`, `POST /api/auth/login`
- `POST /api/documents/upload`, `GET /api/documents/`
- `POST /api/documents/{id}/index`, `DELETE /api/documents/{id}`
- `POST /api/conversations/`, `GET /api/conversations/`
- `GET /api/conversations/{id}/messages`, `DELETE /api/conversations/{id}`
- `POST /api/chat/`
- `GET /health`

All document, conversation, and chat routes require a bearer token.

## Tests

Run `pytest`. Provider-dependent integration tests stub provider responses and
do not need an AI API key or internet access.

## Docker

Build with `docker build -t ai-research-assistant .`, then run with a secure
`SECRET_KEY` and valid AI provider settings. Mount `data/` as a persistent
volume.
