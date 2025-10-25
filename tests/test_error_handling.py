import pytest
from unittest.mock import patch

def test_logger_handles_write_error(logger_instance):
    logger = logger_instance

    with patch("builtins.open", side_effect=IOError("Disk full")):
        try:
            logger.error("This should not crash")
        except Exception as e:
            pytest.fail(f"Logger raised exception: {e}")
