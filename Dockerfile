ARG PLAYWRIGHT_VERSION=1.62.0
FROM mcr.microsoft.com/playwright/python:v${PLAYWRIGHT_VERSION}-noble
ARG PLAYWRIGHT_VERSION

WORKDIR /app

# Install Python deps. The base image ships the browsers only, not the playwright package,
# so pin it to the image version — unpinned, pip pulls the latest and its browsers are missing.
COPY pyproject.toml .
RUN pip install --no-cache-dir "playwright==${PLAYWRIGHT_VERSION}" celery httpx playwright-stealth

COPY scraper.py extractor.py worker.py ./

ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=4", "--pool=prefork", "--queues=tiktok_videos_scraper"]
