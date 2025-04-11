from __future__ import annotations

import functools
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

CONFDICT = dict[str, typing.Any]
CONFDOTDICT = DotDict[str, typing.Any]


_default_smk_file_paths = tuple(Path("workflow").glob("**/*.smk"))


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

    def __post_init__(self):
        for file, configs in snakemaketools.parsers.iter_configs(self.smk_file_paths):
            for config in configs:
                self.raw_rule_configs[config["rule_name"]] = config
                self.rules[config["rule_name"]] = snakemaketools.rules.Rule.from_config(
                    node_storage=self.node_storage,
                    **config,
                )

    def update_consolidated_config(self, diff) -> None:
        assert (
            "diff_parametrization" in self.consolidated_config
        ), "consolidated config without a `diff_parametrization` field is not allowed (for now)."
        diff_parametrization = self.consolidated_config["diff_parametrization"]

        keys = diff_parametrization.split("/")
        values = diff.split("/")
        assert len(keys) == len(
            values
        ), f"\n\nERROR!!!\n\nInconsitency between your config's\ndiff_parametrization=`{diff_parametrization}`,\nand the actually passed in values, `{diff}`.\nWe would expect to pass in {len(keys)} values separated by `/`; instead, we got `{len(values)}`.\n\n\n."

        # TODO: if last config entry does not exist, create it??
        for keys, value in zip(keys, values):
            try:
                _keys = keys.split(".")
                last_key = _keys.pop()
                dct = self.consolidated_config
                for key in _keys:
                    dct = dct[key]
                dct[last_key] = type(dct[last_key])(value)
            except ValueError as e:
                print(f"dct[last_key] = {dct[last_key]}")
                print(f"value = {value}")
                raise
            except KeyError as e:
                print(f"\nERROR!!!\nPath `{keys}` does not occur in the config.\n\n")
                raise

    @property
    def configs(self) -> CONFDOTDICT:
        configs: DotDict = DotDict()
        for name, config in self.consolidated_config["config"].items():
            configs[name] = snakemaketools.rules.Config.new(**config, rule_name=name)
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
            wished_for_nodes[wish]["final_location"] = final_location.format(
                **self.str_wildcards
            )
        return DotDict.Recursive(wished_for_nodes)

    def reset_input_locations(self, **additional_inputs: str):
        self.input_locations = DotDict(
            (node, info.location) for node, info in self.wished_for_nodes.items()
        )
        for key, value in additional_inputs.items():
            assert (
                key not in self.input_locations
            ), f"Make sure `{key}` is not among the '[wishlist]' entries in your pipeline's consolidated config."
            self.input_locations[key] = value
