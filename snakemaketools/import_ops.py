import importlib
from pathlib import Path


def script_to_globals(path: str | Path) -> dict:
    _globals = {}
    with open(path, "r") as f:
        exec(f.read(), _globals)
    return _globals


def dynamically_import_foo(path: str, _object_sep: str = "::"):
    module_str, foo = path.split(_object_sep)
    return getattr(importlib.import_module(module_str), foo)
