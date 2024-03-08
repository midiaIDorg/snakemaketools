import base64
import os
import textwrap
import types
import typing
from pathlib import Path

import brotli


def iter_brackets(
    path,
    open_bracket="[",
    close_bracket="]",
):
    current_open_brackets = 0
    for idx, letter in enumerate(path):
        if letter == open_bracket:
            if current_open_brackets == 0:
                prev_idx = idx
            current_open_brackets += 1
        if letter == close_bracket:
            current_open_brackets -= 1
            if current_open_brackets == 0:
                assert idx < len(path), "Some brackets were not closed."
                yield path[prev_idx + 1 : idx]
    assert current_open_brackets == 0, "Some brackets were not closed."


def extract_outermost_brackets(path):
    return tuple(iter_brackets(str(path)))


def compress(
    path: str,
    compressor: typing.Callable[[bytes], bytes] = brotli.compress,
) -> str:
    _compressed = compressor(path.encode())
    _compressed_base64 = base64.urlsafe_b64encode(_compressed).decode()
    max_file_size = os.pathconf("/", "PC_NAME_MAX")
    _compressed_slashed = "/".join(textwrap.wrap(_compressed_base64, max_file_size))
    return _compressed_slashed


def decompress(
    compressed_str: str,
    decompressor: typing.Callable[[bytes], bytes] = brotli.decompress,
) -> str:
    compressed_str = str(compressed_str).replace("/", "")
    compressed_bin = base64.urlsafe_b64decode(compressed_str)
    decompressed = decompressor(compressed_bin).decode("utf-8")
    return decompressed


def get_compressed_part(path: Path | str, compressed_folder="CMPR") -> str:
    """First two folders and file name are Snakemake rule recognition."""
    path = Path(path)
    path_parts = path.parts
    assert path_parts[0] == compressed_folder, f"No compressed part in `{path}`."
    middle = "/".join(path_parts[2:-1])
    return middle


class PathTemplates:
    def __init__(
        self,
        wildcards: dict[str, typing.Any],
        compress: typing.Callable[[str], str] = compress,
        compressed_folder: str = "CMPR",
    ):
        self._wildcards = wildcards
        self.compress = compress
        self.raw = types.SimpleNamespace()
        self.real = types.SimpleNamespace()
        self.full = types.SimpleNamespace()
        self.compressed_folder = compressed_folder

    def encode(self, path: Path | str) -> Path:
        """The compressed part contain all of the path, including beginning and filename."""
        path = Path(path)
        path_parts = path.parts
        if path_parts[0] != self.compressed_folder:
            return path
        beginning = Path("/".join(path_parts[:2]))
        filename = path_parts[-1]
        return beginning / self.compress(str(path)) / filename

    def set(self, **kwargs: Path | str) -> None:
        for alias, path in kwargs.items():
            self.raw.__dict__[alias] = Path(path)
            filled_path = Path(str(path).format(**self._wildcards))
            self.full.__dict__[alias] = filled_path
            self.real.__dict__[alias] = self.encode(filled_path)

    def __repr__(self):
        return f"full:\n{repr(self.full)}\nreal\n{repr(self.real)}"
