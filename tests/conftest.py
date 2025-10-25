import pytest
import os
from logger.core import get_logger

@pytest.fixture(scope="function")
def logger_instance(tmp_path):
    log_file = tmp_path / "test.log"
    os.environ["LOGGER_PATH"] = str(log_file)
    logger = get_logger("test_component")
    yield logger
    if log_file.exists():
        log_file.unlink()
