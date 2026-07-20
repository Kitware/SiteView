"""No-op performance-timing shim (SiteView carries no perf instrumentation)."""
from contextlib import contextmanager


class perf:
    @staticmethod
    def is_enabled():
        return False

    @staticmethod
    @contextmanager
    def timed(_label):
        yield
