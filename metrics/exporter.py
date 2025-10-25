from prometheus_client import start_http_server, Gauge
import threading
import time


class PrometheusExporter:
    """Экспортер метрик Prometheus + защита от падения сервера."""

    def __init__(self, registry, port=9100):
        self.registry = registry
        self.port = port
        self.gauges = {}
        self.running = False

    def _export_loop(self):
        while self.running:
            try:
                data = self.registry.collect_all()
                for metric_name, values in data.items():
                    for key, val in values.items():
                        full_name = f"{metric_name}_{key}"
                        if full_name not in self.gauges:
                            self.gauges[full_name] = Gauge(full_name, f"Auto metric {full_name}")
                        self.gauges[full_name].set(val)
            except Exception as e:
                print(f"[metrics] Error in export loop: {e}")
            time.sleep(5)

    def start(self):
        start_http_server(self.port)
        self.running = True
        threading.Thread(target=self._export_loop, daemon=True).start()
        print(f"[metrics] Prometheus exporter started on :{self.port}")
