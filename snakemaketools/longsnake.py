from __future__ import annotations

import functools
import toml
import typing

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import snakemaketools

from pprint import pprint
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db as pony_db
from snakemaketools.models import SimplePonyNodeStorage
from snakemaketools.rules import NodeStorage

from snakemake.io import expand
from warnings import warn


def partial_format(string: str, **wildcards):
    return expand(string, allow_missing=True, **wildcards)[0]


CONFDICT = dict[str, typing.Any]
CONFDOTDICT = DotDict[str, typing.Any]


_default_smk_file_paths = tuple(Path("workflow").glob("**/*.smk"))


def update_nested_dict(original, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            update_nested_dict(original[key], value)
        else:
            if not key in original:
                msg = f"Key `{key}` not found in original dictionary. Adding it with `{key}={value}`."
                warn(msg)
            elif value == "ELIMINATE_ME_FOR_GOOD":
                msg = f"Eliminating key `{key}` after seeing `ELIMINATE_ME_FOR_GOOD`."
                warn(msg)
                continue
            original[key] = value


def apply_value_update(original: str | int | float | bool, update: str):
    if type(original) in (int, float):
        return type(original)(update)
    elif type(original) == bool:
        return update.lower() == "true"
    elif isinstance(original, str):
        return update
    else:
        raise ValueError("Unrecognized type.")


@dataclass
class LongSnakeConfiguration:
    """Configure LongSnake.

    This class is intended for use mainly by Snakemake itself.
    Make sure that Pony DB is properly set up for NodeStorage to work.
    """

    consolidated_config: CONFDICT
    get_nodes: typing.Callable[[CONFDICT, CONFDICT, CONFDICT], CONFDOTDICT]
    node_storage: NodeStorage = field(default_factory=SimplePonyNodeStorage)
    smk_file_paths: tuple = _default_smk_file_paths
    input_locations: DotDict = field(default_factory=DotDict)
    raw_rule_configs: DotDict = field(default_factory=DotDict)
    rules: DotDict = field(default_factory=DotDict)
    diff_tag = "diff_"
    diff_config_path_template: str = "configs/diffs/{}.toml"

    def __post_init__(self):
        for file, configs in snakemaketools.parsers.iter_configs(self.smk_file_paths):
            for config in configs:
                self.raw_rule_configs[config["rule_name"]] = config
                self.rules[config["rule_name"]] = snakemaketools.rules.Rule.from_config(
                    node_storage=self.node_storage,
                    **config,
                )

    def update_consolidated_config_with_diff_toml(self, diff):
        config_diff_name, diff = diff.split("/", 1)
        diff_config_path = Path(self.diff_config_path_template.format(config_diff_name))
        assert (
            diff_config_path.exists()
        ), f"Missing diff config under `{diff_config_path}`."
        self.input_locations["diff_config"] = str(diff_config_path)

        with diff_config_path.open("r") as f:
            diff_config = toml.load(f)
        update_nested_dict(self.consolidated_config, diff_config)
        return diff

    def update_consolidated_config(self, diff) -> None:
        if diff[: len(self.diff_tag)] == self.diff_tag:
            diff = self.update_consolidated_config_with_diff_toml(diff)
        assert (
            "diff_parametrization" in self.consolidated_config
        ), "consolidated config without a `diff_parametrization` field is not allowed (for now)."
        diff_parametrization = self.consolidated_config["diff_parametrization"]

        keys = diff_parametrization.split("/")
        command_line_updates = diff.split("/")
        assert len(keys) == len(
            command_line_updates
        ), f"\n\nERROR!!!\n\nInconsitency between your config's\ndiff_parametrization=`{diff_parametrization}`,\nand the actually passed in command_line_updates, `{diff}`.\nWe would expect to pass in {len(keys)} command_line_updates separated by `/`; instead, we got `{len(command_line_updates)}`.\n\n\n."

        # TODO: if last config entry does not exist, create it??
        for keys, update in zip(keys, command_line_updates):
            try:
                _keys = keys.split(".")
                last_key = _keys.pop()
                dct = self.consolidated_config
                for key in _keys:
                    dct = dct[key]
                dct[last_key] = apply_value_update(
                    original=dct[last_key], update=update
                )

            except ValueError as e:
                print(f"dct[last_key] = {dct[last_key]}")
                print(f"update = {update}")
                raise
            except KeyError as e:
                print(f"\nERROR!!!\nPath `{keys}` does not occur in the config.\n\n")
                raise

    @property
    def configs(self) -> CONFDOTDICT:
        configs: DotDict = DotDict()
        if "config" in self.consolidated_config:
            for name, config in self.consolidated_config["config"].items():
                configs[name] = snakemaketools.rules.Config.new(
                    **config, rule_name=name
                )
        return configs

    @property
    def str_wildcards(self) -> CONFDICT:
        return self.consolidated_config["wildcards"]

    @property
    def wildcards(self) -> CONFDOTDICT:
        return DotDict(
            (
                wildcard_name,
                snakemaketools.rules.Wildcard(name=wildcard_name, value=wildcard_value),
            )
            for wildcard_name, wildcard_value in self.str_wildcards.items()
        )

    @property
    def nodes(self) -> CONFDOTDICT:
        return self.get_nodes(
            rules=self.rules,
            configs=self.configs,
            wildcards=self.wildcards,
        )

    @property
    def wished_for_nodes(self) -> CONFDOTDICT:
        wished_for_nodes = {}
        for wish, final_location in self.consolidated_config["wishlist"].items():
            assert (
                wish in self.nodes
            ), f"You are wishing for unwishable: `{wish}`. Wish for something wishable or whoosh!"
            wished_for_nodes[wish] = dict(self.nodes[wish])
            wished_for_nodes[wish]["final_location"] = partial_format(
                final_location, **self.str_wildcards
            )
        return DotDict.Recursive(wished_for_nodes)

    def reset_input_locations(self, **additional_inputs: str):
        self.input_locations.update(
            DotDict(
                (node, info.location) for node, info in self.wished_for_nodes.items()
            )
        )
        for key, value in additional_inputs.items():
            assert (
                key not in self.input_locations
            ), f"Make sure `{key}` is not among the '[wishlist]' entries in your pipeline's consolidated config."
            self.input_locations[key] = value
