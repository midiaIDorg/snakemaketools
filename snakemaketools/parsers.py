import dataclasses
import json
import pathlib
import typing
from collections import defaultdict, deque
from pathlib import Path
from pprint import pformat
from typing import Iterable
from warnings import warn

import toml
from snakemaketools.encodings import iter_brackets


def comment_based_toml_extractor(
    codelines: Iterable[str],
    _start_tag: str = "# TOML START",
    _stop_tag: str = "# TOML STOP",
    _comment_tag: str = "# TOML",
    _fifo_len: int = 20,
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
    last_few_lines = deque(maxlen=_fifo_len)
    for line in codelines:
        last_few_lines.append(line)
        line = line.strip()
        # Detect sections based on the keywords
        if line.startswith(_start_tag):
            recording = True
            buffer: list[str] = []
        elif line.startswith(_stop_tag):
            assert recording
            recording = False
            conf = "\n".join(buffer)
            try:
                tomls.append(toml.loads(conf))
            except toml.TomlDecodeError as ex:
                last_few_lines = "".join(list(last_few_lines))
                raise ValueError(f"Error in lines:\n{last_few_lines}:\n{str(ex)}")
        elif recording:
            assert line.startswith(_comment_tag), f"Problem in:\n{buffer}"
            line = line[len(_comment_tag) :]
            buffer.append(line)
        else:
            pass

    assert not recording

    return tomls


def iter_configs(
    paths: typing.Iterable[pathlib.Path],
    config_extractor=comment_based_toml_extractor,
) -> typing.Iterable[tuple[pathlib.Path, list[dict]]]:
    for path in paths:
        with open(path, "r") as f:
            try:
                configs = list(config_extractor(f.readlines()))
                if len(configs) > 0:
                    yield path, configs
            except AssertionError as exc:
                raise AssertionError(f"Problem in {path}: {exc}")


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

    def load(self, file) -> dict:
        return self.loads(file.read())

    def dump(self, content, file) -> None:
        file.write(self.dumps(content))


def dump_to_config_format(config: dict) -> str:
    """Dump to .config format used by Bruker."""

    def iter_config(config, prefix=""):
        assert isinstance(
            config, dict
        ), f"Pass in some form of dict. Got `{type(config)}`"
        for key, value in config.items():
            key = key if prefix == "" else f"{prefix}.{key}"
            if isinstance(value, dict):
                yield from iter_config(value, prefix=key)
            else:
                yield f"{key}={value}"

    return "\n".join(iter_config(config))


toml_serializer = DictSerializer(toml.loads, toml.dumps)
json_serializer = DictSerializer(json.loads, json.dumps)
config_serializer = DictSerializer(dotConfig_loads, dump_to_config_format)

serializers = {
    ".toml": toml_serializer,
    ".json": json_serializer,
    ".config": config_serializer,
}


def get_wildcards(text: str) -> set[str]:
    return set(iter_brackets(text, "{", "}"))


def parse_config_file_and_optional_diff(config_and_optional_diff: str):
    config_and_optional_diff = str(config_and_optional_diff)
    filename, *rest = config_and_optional_diff.split("/", 1)
    if len(rest) == 0:
        rest = ""
    elif len(rest) == 1:
        rest = rest.pop()
    else:
        raise ValueError(f"`rest` still has some entries: {rest}")
    return filename, rest
