"""
Redis Queue Module - Background Job Processing

Provides scalable job queuing for:
- Task execution
- Webhook processing
- Long-running agent operations

Falls back to in-memory queue if Redis is unavailable.
"""

import os
import json
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

logger = logging.getLogger(__name__)

# Optional Redis support
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("redis not installed. Using in-memory queue.")


@dataclass
class Job:
    """Represents a queued job."""

    id: str
    type: str  # "agent_run", "webhook", etc.
    payload: Dict[str, Any]
    created_at: str
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QueueManager:
    """
    Manages job queuing.
    Uses Redis if available, falls back to in-memory queue.
    """

    QUEUE_NAME = "kita:jobs"
    RESULTS_PREFIX = "kita:result:"

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self._redis: Optional[redis.Redis] = None
        self._memory_queue: queue.Queue = queue.Queue()
        self._memory_results: Dict[str, Job] = {}
        self._handlers: Dict[str, Callable] = {}
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        if self.redis_url and REDIS_AVAILABLE:
            self._init_redis()
        else:
            logger.info("Using in-memory job queue (no REDIS_URL or redis-py)")

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self._redis = redis.from_url(self.redis_url)
            self._redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            logger.info("Falling back to in-memory queue")

    @property
    def is_redis(self) -> bool:
        """Returns True if using Redis."""
        return self._redis is not None

    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a job type."""
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    def enqueue(self, job: Job) -> str:
        """Add a job to the queue."""
        job_data = asdict(job)

        if self.is_redis:
            self._redis.lpush(self.QUEUE_NAME, json.dumps(job_data))
            self._redis.set(f"{self.RESULTS_PREFIX}{job.id}", json.dumps(job_data))
        else:
            self._memory_queue.put(job)
            self._memory_results[job.id] = job

        logger.debug(f"Enqueued job {job.id} of type {job.type}")
        return job.id

    def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get the status of a job."""
        if self.is_redis:
            data = self._redis.get(f"{self.RESULTS_PREFIX}{job_id}")
            if data:
                return Job(**json.loads(data))
        else:
            return self._memory_results.get(job_id)
        return None

    def _update_job_status(self, job: Job):
        """Update job status in storage."""
        job_data = asdict(job)
        if self.is_redis:
            self._redis.set(f"{self.RESULTS_PREFIX}{job.id}", json.dumps(job_data))
        else:
            self._memory_results[job.id] = job

    def _process_job(self, job: Job):
        """Process a single job."""
        handler = self._handlers.get(job.type)
        if not handler:
            logger.error(f"No handler for job type: {job.type}")
            job.status = "failed"
            job.error = f"No handler for type: {job.type}"
            self._update_job_status(job)
            return

        try:
            job.status = "processing"
            self._update_job_status(job)

            result = handler(job.payload)

            job.status = "completed"
            job.result = result
            self._update_job_status(job)
            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            self._update_job_status(job)

    def _worker_loop(self):
        """Background worker loop."""
        logger.info("Queue worker started")
        while self._running:
            try:
                if self.is_redis:
                    # Blocking pop with 1 second timeout
                    result = self._redis.brpop(self.QUEUE_NAME, timeout=1)
                    if result:
                        _, job_data = result
                        job = Job(**json.loads(job_data))
                        self._process_job(job)
                else:
                    try:
                        job = self._memory_queue.get(timeout=1)
                        self._process_job(job)
                    except queue.Empty:
                        pass
            except Exception as e:
                logger.error(f"Worker error: {e}")

        logger.info("Queue worker stopped")

    def start_worker(self):
        """Start the background worker thread."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop_worker(self):
        """Stop the background worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)


# Global queue instance
job_queue = QueueManager()


# Helper function to create and enqueue a job
def enqueue_agent_run(
    job_id: str,
    task: str,
    repo_path: str,
    openai_key: str = None,
    anthropic_key: str = None,
) -> str:
    """Convenience function to enqueue an agent run job."""
    job = Job(
        id=job_id,
        type="agent_run",
        payload={
            "task": task,
            "repo_path": repo_path,
            "openai_api_key": openai_key,
            "anthropic_api_key": anthropic_key,
        },
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return job_queue.enqueue(job)
