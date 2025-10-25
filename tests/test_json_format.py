import json
import os

def test_json_log_structure(logger_instance):
    logger = logger_instance
    msg = "Transaction processed"
    logger.info(msg)

    log_file = os.environ["LOGGER_PATH"]
    with open(log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    assert "timestamp" in data
    assert "level" in data
    assert "message" in data
    assert "component" in data
    assert data["message"] == msg
    assert data["level"] == "INFO"
