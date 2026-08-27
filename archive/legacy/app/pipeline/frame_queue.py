"""Thread-safe Bounded Frame Queue with Drop-Stale Policy."""
import queue
from typing import Any, Tuple

class BoundedFrameQueue:
    def __init__(self, maxsize: int = 2):
        self.queue = queue.Queue(maxsize=maxsize)
        self.dropped_count = 0

    def put_latest(self, item: Any):
        if self.queue.full():
            try:
                self.queue.get_nowait()
                self.dropped_count += 1
            except queue.Empty:
                pass
        self.queue.put(item)

    def get(self, timeout: float = 0.1) -> Any:
        return self.queue.get(timeout=timeout)

    def empty(self) -> bool:
        return self.queue.empty()
