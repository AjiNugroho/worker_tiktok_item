# worker_tiktok_item

Celery worker that scrapes TikTok video pages and delivers structured data to a webhook.

## Project layout

```
scraper.py      — TikTokScraper class (Playwright, async)
extractor.py    — extract_video(raw) → clean dict from rehydration JSON
worker.py       — Celery app + scrape_video task
Dockerfile      — playwright/python base image, concurrency=1
docker-compose.yml — worker + Redis
```

## Package manager

**uv** — always use `uv pip install`, `uv run`, never bare `pip`.

```bash
uv pip install -e .
uv run python scraper.py <url>
```

## Running locally

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start worker
uv pip install -e .
celery -A worker worker --loglevel=info --concurrency=1
```

## Running with Docker

```bash
docker compose up --build        # start
docker compose up --scale worker=3  # scale
```

## Task contract

Enqueue via Celery:
```python
from worker import scrape_video
scrape_video.delay(
    request_id="your-identifier",
    url="https://www.tiktok.com/@user/video/123",
    webhook_url="https://your-api.com/webhook",
)
```

Webhook POST body:
```json
// success
{ "request_id": "...", "status": "success", "data": { ...video fields... } }

// failure (after 2 retries)
{ "request_id": "...", "status": "error", "error": "..." }
```

## Environment variables

| Var | Default | Notes |
|---|---|---|
| `BROKER_URL` | `amqp://guest:guest@localhost:5672//` | RabbitMQ broker URL |

## Playwright notes

- Base Docker image: `mcr.microsoft.com/playwright/python:v1.60.0-noble` — browsers pre-installed, no `playwright install` in Dockerfile.
- If upgrading Playwright, update **both** `pyproject.toml` and the Dockerfile `FROM` tag.
- `playwright-stealth` 2.x API: `Stealth().apply_stealth_async(page)` (not the old `stealth_async`).
- `wait_for_selector` needs `state="attached"` for `<script>` tags (they are never "visible").

## Extraction map

Data root: `__DEFAULT_SCOPE__["webapp.video-detail"].itemInfo.itemStruct`

See [video_extraction.md](video_extraction.md) for the full field map.

Key gotchas:
- Use `statsV2` (strings) over `stats` (ints) — cast to int yourself.
- Product anchor is double-escaped JSON: `anchors[type==35].extra → JSON[0].extra → JSON`.
- Cookies / proxy / stealth are optional — all wired into `TikTokScraper.__init__`, off by default.

## Future work planned

- Cookie file injection (load `cookies.json` → `context.add_cookies()`) — toggle via `cookie_file=Path(...)`
- Stealth mode — toggle via `stealth=True` in `TikTokScraper`
- Proxy support — pass `proxy={"server": "..."}` to `TikTokScraper`
