"""Worker entry point.

Run via: python -m app.worker
In docker-compose the worker service uses: command: python -m app.worker

Currently a no-op stub. A future story will hook a real job queue (SQS, etc.)
and have this process poll and execute jobs.
"""
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("ILM worker started (stub — no queue configured)")
    while True:
        logger.debug("Worker idle — waiting for jobs...")
        time.sleep(30)


if __name__ == "__main__":
    main()
