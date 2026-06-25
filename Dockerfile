FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

WORKDIR /app

# Install Python deps (playwright + browsers already in base image)
COPY pyproject.toml .
RUN pip install --no-cache-dir celery httpx playwright-stealth

COPY scraper.py extractor.py worker.py ./

ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=2", "--pool=prefork", "--queues=tiktok_videos_scraper"]
