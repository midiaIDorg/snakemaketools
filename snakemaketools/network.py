import os
import socket

from pathlib import Path


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # Doesn't actually send data
        return s.getsockname()[0]


def get_pipeline_location():
    return str(Path.cwd())


def get_user():
    return os.getlogin()


def get_server():
    return socket.gethostname()


def whoami():
    return dict(
        ip_address=get_local_ip(),
        user_name=get_user(),
        server_name=get_server(),
        pipeline_location=get_pipeline_location(),
    )
