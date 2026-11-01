"""Process-local bounded worker pool. Persistent runs are not a durable job queue."""

from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from uuid import UUID

from app.core.config import Settings
from app.db import SessionLocal
from app.discovery.errors import DiscoveryError
from app.services.discovery import execute_discovery, fail_run


class DiscoveryExecutor:
    def __init__(self, settings: Settings, session_factory=SessionLocal):
        self.settings = settings
        self.factory = session_factory
        self.pool = ThreadPoolExecutor(
            max_workers=settings.discovery_workers, thread_name_prefix="opportunity"
        )
        self.slots = BoundedSemaphore(settings.discovery_workers + settings.discovery_queue_size)
        self.closed = False

    def submit(self, run_id: UUID) -> None:
        if self.closed or not self.slots.acquire(blocking=False):
            fail_run(self.factory, run_id, "executor_capacity")
            raise DiscoveryError(
                "executor_capacity",
                "Discovery capacity is full; try later with a new idempotency key",
                503,
            )
        try:
            future = self.pool.submit(execute_discovery, run_id, self.factory, self.settings)
        except RuntimeError:
            self.slots.release()
            fail_run(self.factory, run_id, "executor_unavailable")
            raise DiscoveryError(
                "executor_unavailable", "Discovery executor is unavailable", 503
            ) from None

        def finished(job):
            self.slots.release()
            if job.cancelled():
                fail_run(self.factory, run_id, "executor_shutdown")

        future.add_done_callback(finished)

    def close(self) -> None:
        self.closed = True
        self.pool.shutdown(wait=False, cancel_futures=True)
