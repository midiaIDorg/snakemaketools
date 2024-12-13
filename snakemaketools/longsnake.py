from __future__ import annotations

import functools
import typing
from dataclasses import dataclass
from pathlib import Path

import snakemaketools
import typ
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db as pony_db
from snakemaketools.models import SimplePonyNodeStorage
from snakemaketools.rules import NodeStorage

CONFDICT = dict[str, typing.Any]
CONFDOTDICT = DotDict[str, typing.Any]


@dataclass
class LongSnakeConfiguration:
    """Configure LongSnake.

    This class is intended for use mainly by Snakemake itself.
    Make sure that Pony DB is properly set up for NodeStorage to work.
    """

    consolidated_config: CONFDICT
    get_nodes: typing.Callable[[CONFDICT, CONFDICT, CONFDICT], CONFDOTDICT]
    node_storage: NodeStorage = SimplePonyNodeStorage()
    smk_file_paths: typing.Iterable = Path("workflow").glob("**/*.smk")

    @functools.cached_property
    def configs(self) -> CONFDOTDICT:
        configs: DotDict = DotDict()
        for name, config in consolidated_config["config"].items():
            configs[name] = snakemaketools.rules.Config.new(**config, rule_name=name)
        return configs

    @functools.cache
    def rule_config(self) -> CONFDOTDICT:
        raw = DotDict()
        parsed = DotDict()
        for file, configs in snakemaketools.parsers.iter_configs(self.smk_file_paths):
            for config in configs:
                raw[config["rule_name"]] = config
                parsed[config["rule_name"]] = snakemaketools.rules.Rule.from_config(
                    node_storage=self.node_storage,
                    **config,
                )
        return DotDict(dict(raw=raw, parsed=parsed))

    @property
    def raw_rule_configs(self) -> CONFDOTDICT:
        return self.rule_config.raw

    @property
    def rules(self) -> CONFDOTDICT:
        return self.rule_config.parsed

    @property
    def str_wildcards(self) -> CONFDICT:
        return self.consolidated_config["wildcards"]

    @functools.cached_property
    def wildcards(self) -> CONFDOTDICT:
        return DotDict(
            (
                wildcard_name,
                snakemaketools.rules.Wildcard(name=wildcard_name, value=wildcard_value),
            )
            for wildcard_name, wildcard_value in self.str_wildcards.items()
        )

    @functools.cached_property
    def nodes(self) -> CONFDOTDICT:
        return self.get_nodes(
            rules=self.rules,
            configs=self.configs,
            wildcards=self.wildcards,
        )

    @functools.cached_property
    def wished_for_nodes(self) -> CONFDICT:
        wished_for_nodes = {}
        for wish, final_location in self.consolidated_config["wishlist"].items():
            assert (
                wish in self.nodes
            ), f"You are wishing for unwishable: `{wish}`. Wish for something wishable or whoosh!"
            wished_for_nodes[wish] = dict(self.nodes[wish])
            wished_for_nodes[wish]["final_location"] = final_location.format(
                **str_wildcards
            )
        return wished_for_nodes


# def parse_config_fill_db_get_wishlist(
#     consolidated_config: dict,
#     get_nodes: typing.Callable,
# ) -> dict:
#     """Make paths. Fill up the DB. Provide wishlist.

#     This code assumes that Pony db is already setup.
#     """
#     configs: DotDict = DotDict()
#     for name, config in consolidated_config["config"].items():
#         configs[name] = snakemaketools.rules.Config.new(**config, rule_name=name)

#     node_storage = SimplePonyNodeStorage()
#     raw_rule_configs = DotDict()
#     rules = DotDict()
#     for file, rule_configs in snakemaketools.parsers.iter_configs(
#         Path("workflow").glob("**/*.smk")
#     ):
#         for rule_config in rule_configs:
#             raw_rule_configs[rule_config["rule_name"]] = rule_config
#             rules[rule_config["rule_name"]] = snakemaketools.rules.Rule.from_config(
#                 node_storage=node_storage,
#                 **rule_config,
#             )

#     str_wildcards = consolidated_config["wildcards"]
#     wildcards = DotDict()
#     for wildcard_name, wildcard_value in str_wildcards.items():
#         wildcards[wildcard_name] = snakemaketools.rules.Wildcard(
#             name=wildcard_name, value=wildcard_value
#         )

#     nodes = get_nodes(rules=rules, configs=configs, wildcards=wildcards)
#     wished_for_nodes = {}
#     for wish, final_location in consolidated_config["wishlist"].items():
#         assert (
#             wish in nodes
#         ), f"You are wishing for unwishable: `{wish}`. Wish something else or whoosh!"
#         wished_for_nodes[wish] = dict(nodes[wish])
#         wished_for_nodes[wish]["final_location"] = final_location.format(
#             **str_wildcards
#         )

#     return wished_for_nodes
