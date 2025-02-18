import os
import socket

from pathlib import Path


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # Doesn't actually send data
        return s.getsockname()[0]


def whoami():
    return dict(
        ip_address=get_local_ip(),
        user_name=os.getlogin(),
        server_name=socket.gethostname(),
        pipeline_location=str(Path.cwd()),
    )
