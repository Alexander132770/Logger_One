import psutil
import time
from .base import Metric


class CpuUsageMetric(Metric):
    def collect(self):
        return {"cpu_percent": psutil.cpu_percent(interval=0.5)}

    def reset(self):
        pass


class MemoryUsageMetric(Metric):
    def collect(self):
        mem = psutil.virtual_memory()
        return {"memory_percent": mem.percent, "available_mb": mem.available / 1024 / 1024}

    def reset(self):
        pass


class RequestCountMetric(Metric):
    def __init__(self, name, description):
        super().__init__(name, description)
        self.count = 0

    def inc(self, n=1):
        self.count += n

    def collect(self):
        return {"requests_total": self.count}

    def reset(self):
        self.count = 0
