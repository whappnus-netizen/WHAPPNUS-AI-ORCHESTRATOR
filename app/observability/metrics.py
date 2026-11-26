from collections import Counter
from threading import Lock

class InMemoryMetrics:
    """Process-local development counters; replace with shared metrics in production."""
    def __init__(self):
        self._counts=Counter(); self._lock=Lock()
    def increment(self,name,amount=1):
        with self._lock: self._counts[name]+=amount
    def snapshot(self):
        with self._lock: return dict(self._counts)

metrics=InMemoryMetrics()
