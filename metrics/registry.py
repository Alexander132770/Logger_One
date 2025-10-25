from typing import Dict
from .base import Metric
from .storage import ReliableStorage


class MetricsRegistry:
    """Глобальный реестр метрик."""

    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._storage = ReliableStorage()

    def register(self, metric: Metric):
        self._metrics[metric.name] = metric

    def collect_all(self):
        result = {}
        for name, metric in self._metrics.items():
            result[name] = metric.collect()
            self._storage.set(name, result[name])
        return result
