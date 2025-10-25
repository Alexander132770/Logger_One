import json
import os

def test_basic_log_write(logger_instance):
    logger = logger_instance
    logger.info("Simple log message")

    log_file = os.environ["LOGGER_PATH"]
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert "Simple log message" in content
    assert '"level": "INFO"' in content

def test_all_levels(logger_instance):
    logger = logger_instance
    logger.debug("debug message")
    logger.warning("warn message")
    logger.error("error message")
    log_file = os.environ["LOGGER_PATH"]

    with open(log_file, "r", encoding="utf-8") as f:
        data = f.read()

    assert "debug message" in data
    assert "warn message" in data
    assert "error message" in data
