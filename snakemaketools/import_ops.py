import importlib
from pathlib import Path


def script_to_globals(path: str | Path) -> dict:
    _globals = {}
    with open(path, "r") as f:
        exec(f.read(), _globals)
    return _globals
