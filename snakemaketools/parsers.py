import dataclasses
import json
import pathlib
import typing
from collections import defaultdict
from typing import Iterable

import toml


def comment_based_toml_extractor(
    codelines: Iterable[str],
    _start_tag: str = "# TOML START",
    _stop_tag: str = "# TOML STOP",
    _comment_tag: str = "# TOML",
) -> list[dict]:
    """
    Parse code lines for presence of toml configs.

    The toml config is defined as section of text between a start and end tag.

    Arguments:
        codelines (Iterable[str]): An iterable of code lines to analyse one by one for the presence of toml-encoded settings.

    Returns:
        list[dict]: A list of dictionaries with parsed configs.
    """
    tomls = []
    recording = False
    for line in codelines:
        line = line.strip()
        # Detect sections based on the keywords
        if line.startswith(_start_tag):
            recording = True
            buffer: list[str] = []
        elif line.startswith(_stop_tag):
            assert recording
            recording = False
            conf = "\n".join(buffer)
            tomls.append(toml.loads(conf))
        elif recording:
            assert line.startswith(_comment_tag), line
            line = line[len(_comment_tag) :]
            buffer.append(line)
        else:
            pass

    assert not recording

    return tomls


def iter_lines_recursively(root: pathlib.Path | str, pattern: str = "**/*.smk"):
    for path in pathlib.Path(root).glob(pattern):
        with open(path, "r") as f:
            for line in f:
                yield line


def cast_to_int_or_float(x):
    if "." in x:
        return float(x)
    return int(x)


def dotConfig_loads(text: str) -> dict:
    """Read .config files for 4DFF and 5DFF."""
    res = {}
    for l in text.split("\n"):
        l = l.strip()
        if "=" in l:
            LHS, RHS = l.split("=")
            LHS = LHS.strip()
            RHS = RHS.strip()
            assert LHS not in res, f"Key `{LHS}` appears more than once."
            try:
                RHS = cast_to_int_or_float(RHS)
            except ValueError:
                pass
            res[LHS] = RHS
    return res


@dataclasses.dataclass
class DictSerializer:
    loads: typing.Callable[[str], dict]
    dumps: typing.Callable[[dict], str]


serializers = {
    ".toml": DictSerializer(toml.loads, toml.dumps),
    ".json": DictSerializer(json.loads, json.dumps),
    ".config": DictSerializer(dotConfig_loads, toml.dumps),
}
