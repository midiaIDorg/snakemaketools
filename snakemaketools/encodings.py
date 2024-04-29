import abc
import base64
import functools
import json
import os
import textwrap
import typing
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from types import SimpleNamespace

from snakemake.exceptions import WildcardError

#         path = Path(decompressed_path)
#         path_parts = path.parts
#         assert (
#             path_parts[0] == self._compressed_folder
#         ), f"No compressed part in `{path}`."
#         middle = "/".join(path_parts[2:-1])
#         return middle
from snakemake.io import expand

import brotli


def expand_dict_partially(name_to_path_pattern: dict[str, str], wildcards, **kwargs):
    """
    Prefill a dictionary with path patterns with provided **kwargs and allow snakemake to fill in the rest.

     _________________________________________
    / Like snakamake.io.expand, but accepting \
    | dictionary name->pattern instead of a   |
    | list of patterns only, so that one can  |
    \ use names in the run command            /
     -----------------------------------------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||
    """
    res = {}
    for name, pattern in name_to_path_pattern.items():
        try:
            res[name] = expand(
                [pattern],
                allow_missing=True,
                **wildcards,
                **kwargs,
            )[0]
        except WildcardError as wildcard_error:
            print(f"name={name} pattern={pattern}")
            raise wildcard_error
    return res


def partial_format(string: str, **kwargs):
    assert "allow_missing" not in kwargs
    res = expand(string, allow_missing=True, **kwargs)
    if len(res) == 1:
        return res[0]
    return res


def fill_path_templates_with_wildcards(
    path_templates: SimpleNamespace,
    wildcards: dict,
) -> SimpleNamespace:
    return SimpleNamespace(
        **{
            name: Path(str(path_template).format(**wildcards))
            for name, path_template in path_templates.__dict__.items()
        }
    )


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


def first_bra_last_ket(path: str) -> tuple[int, int]:
    path = str(path)
    i = 0
    for i in range(len(path)):
        if path[i] == "[":
            break
    for j in reversed(range(len(path))):
        if path[j] == "]":
            break
    return i, j


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


@dataclass
class PathEncoder(abc.ABC):
    _compress: typing.Callable[[str], str] = compress
    _decompress: typing.Callable[[str], str] = decompress
    _wildcard_indicating_compressed: str = "compressed"

    @abc.abstractmethod
    def encode(self, path: Path | str) -> Path:
        """Encode a path to make a valid FS path."""

    # @functools.lru_cache(maxsize=None)
    def get_inputs(
        self,
        compressed: str,
    ) -> typing.Iterable[Path]:
        decompressed = self._decompress(str(compressed))
        brackets_content = extract_outermost_brackets(decompressed)
        return map(self.encode, brackets_content)

    def get_full_inputs(self, compressed: str, *inputs_names: str) -> dict[str, str]:
        decompressed = self._decompress(str(compressed))
        brackets_content = extract_outermost_brackets(decompressed)
        return dict(zip(inputs_names, brackets_content))

    def print_decompressed_inputs(self, compressed: str, *names: str) -> None:
        print("Real Arguments")
        pprint(
            self.get_full_inputs(
                compressed,
                *names,
            )
        )
        print()

    # @functools.lru_cache(maxsize=None)
    def parse_output(
        self,
        *inputs_names: str,
    ) -> typing.Callable:
        """Return a parser of inputs from outputs given input names."""
        for name in inputs_names:
            assert isinstance(name, str)

        def _parser(wildcards):
            res = dict(
                zip(
                    inputs_names,
                    self.get_inputs(
                        wildcards.__dict__[self._wildcard_indicating_compressed]
                    ),
                )
            )
            return res

        return functools.cache(_parser)

    def encode_paths(self, paths: SimpleNamespace) -> SimpleNamespace:
        return SimpleNamespace(
            **{name: self.encode(path) for name, path in paths.__dict__.items()}
        )


@dataclass
class BestPathEncoder(PathEncoder):
    compressable_tag: str = "P"

    def is_to_compress(self, path: Path | str) -> bool:
        return str(path)[: len(self.compressable_tag)] == self.compressable_tag

    def encode(self, decompressed) -> Path:
        """The compressed part contains all of the path, including beginning and filename."""
        decompressed = str(decompressed)
        if not self.is_to_compress(decompressed):
            return Path(decompressed)
        start, end = first_bra_last_ket(decompressed)
        if start >= end:
            return Path(decompressed)
        compressed = decompressed[:start]
        compressed += self._compress(decompressed[start : end + 1])
        if end + 1 < len(decompressed):
            compressed += decompressed[end + 1 :]
        return Path(compressed)


@dataclass
class DBPathEncoder(PathEncoder):
    """A general place holder for a path encoder that uses a thread-safe DB to generate individual path names."""


def embracket(*paths: Path | str) -> str:
    res = "][".join(map(str, paths))
    if len(res) > 0:
        res = f"[{res}]"
    return res


def join_paths(
    prefix: str,
    suffix: str,
    *paths: Path | str,
) -> Path:
    """Create a path following pattern "<prefix>/[path]..[path]/<suffix>".

    To be used upon the long path templates generation in the pipeline scripts.
    """
    res = Path(prefix)
    res /= embracket(*paths)
    res /= suffix
    assert str(res) != ".", "Cannot have prefix, suffix, and all paths empty."
    return res
