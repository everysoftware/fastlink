import base64
import os
from typing import Any


def generate_random_state(length: int = 64) -> str:
    bytes_length = int(length * 3 / 4)
    return base64.urlsafe_b64encode(os.urandom(bytes_length)).decode("utf-8")


def replace_localhost(url: Any) -> str:
    return str(url).replace("localhost", "127.0.0.1", 1)
