import asyncio
import logging
import os
import random
import time

import httpx
from celery import Celery

from extractor import extract_video
from scraper import TikTokScraper

logger = logging.getLogger(__name__)

BROKER_URL = os.environ.get("BROKER_URL", "amqp://guest:guest@localhost:5672//")

app = Celery("worker_tiktok_item", broker=BROKER_URL)

QUEUE_NAME = "tiktok_videos_scraper"

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_backend=None,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_routes={"tiktok.scrape_video": {"queue": QUEUE_NAME}},
)


def _post_webhook(webhook_url: str, payload: dict, retries: int = 3, backoff: float = 2.0) -> None:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(webhook_url, json=payload)
                resp.raise_for_status()
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("Webhook POST attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff ** attempt)
    logger.error("Webhook POST to %s gave up after %d attempts: %s", webhook_url, retries, last_exc)


@app.task(
    bind=True,
    name="tiktok.scrape_video",
    max_retries=2,
)
def scrape_video(self, request_id: str, url: str, webhook_url: str, extras: dict | None = None):
    delay = random.uniform(3, 5)
    logger.info("[%s] Waiting %.1fs before scraping", request_id, delay)
    time.sleep(delay)

    logger.info("[%s] Scraping %s", request_id, url)

    base = {"request_id": request_id, "extras": extras or {}}

    try:
        raw = asyncio.run(TikTokScraper(headless=True).scrape(url))
        video = extract_video(raw)
    except Exception as exc:
        logger.warning("[%s] Attempt %d failed: %s", request_id, self.request.retries + 1, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        logger.error("[%s] All retries exhausted", request_id)
        _post_webhook(webhook_url, {**base, "status": "error", "error": str(exc)})
        return

    logger.info("[%s] Done, posting to webhook", request_id)
    _post_webhook(webhook_url, {**base, "status": "success", "data": video})
