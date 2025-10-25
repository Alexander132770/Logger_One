import concurrent.futures
import json
import os

def test_concurrent_logging(logger_instance):
    logger = logger_instance
    messages = [f"message_{i}" for i in range(50)]

    def log_msg(msg):
        logger.info(msg)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(log_msg, messages))

    log_file = os.environ["LOGGER_PATH"]
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    logged_messages = [json.loads(l)["message"] for l in lines]
    assert set(messages).issubset(set(logged_messages))
