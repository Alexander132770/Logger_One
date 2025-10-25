import os
import json
from logger.config import reload_config

def test_logger_reloads_config(logger_instance):
    logger = logger_instance
    logger.info("before reload")

    reload_config({"level": "ERROR"})
    logger.debug("debug message")  # should not appear
    logger.error("critical failure")

    log_file = os.environ["LOGGER_PATH"]
    with open(log_file, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f.readlines()]

    assert any(l["message"] == "critical failure" for l in logs)
    assert not any(l["message"] == "debug message" for l in logs)
