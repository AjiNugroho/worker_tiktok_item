# Agent Instructions — TikTok Scraper API

Build a small HTTP API that accepts scrape requests and publishes them to RabbitMQ
to be consumed by the `worker_tiktok_item` Celery worker.

---

## What to build

A single-endpoint REST API. No auth required for now.

**Stack:** FastAPI + uvicorn. Python 3.12. Use `uv` as the package manager.

---

## Endpoint

### `POST /scrape`

**Request body:**
```json
{
  "request_id": "any-string-identifier",
  "url": "https://www.tiktok.com/@user/video/123456",
  "webhook_url": "https://your-service.com/webhook/result"
}
```

All three fields are required. Validate with Pydantic.

**Response `202 Accepted`:**
```json
{
  "request_id": "any-string-identifier",
  "status": "queued"
}
```

**Response `422`** on validation error (FastAPI default).

---

## Publishing to RabbitMQ

Use the Celery client to publish — do NOT use `pika` or `aio-pika` directly.
This ensures the message format matches what the worker expects.

```python
from celery import Celery

celery_app = Celery(broker=BROKER_URL)

celery_app.send_task(
    "tiktok.scrape_video",           # must match exactly
    kwargs={
        "request_id": request_id,
        "url": url,
        "webhook_url": webhook_url,
    },
    queue="tiktok_videos_scraper",   # must match exactly
)
```

The Celery app in the API is **client-only** — no tasks are defined in it, it only
sends. Do not start a worker from the API.

---

## Environment variables

| Var | Example | Notes |
|---|---|---|
| `BROKER_URL` | `amqp://user:pass@host:5672/vhost` | Same RabbitMQ as the worker |
| `PORT` | `8000` | API listen port |

Load from `.env` via `python-dotenv` or just `os.environ`.

---

## Project structure

```
api/
├── main.py         — FastAPI app, POST /scrape
├── pyproject.toml
├── Dockerfile
└── .env.example
```

Keep it flat — no need for routers or service layers for a single endpoint.

---

## Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install fastapi uvicorn celery python-dotenv
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## What the worker does with the message

The worker (`worker_tiktok_item`) receives the task, launches a headless Chromium
browser, scrapes the TikTok video URL, extracts structured data, and POSTs the
result to `webhook_url` with this shape:

```json
// success
{ "request_id": "...", "status": "success", "data": { ...video fields... } }

// failure after retries
{ "request_id": "...", "status": "error", "error": "..." }
```

The API does not need to handle the webhook — that is between the worker and
the caller.
