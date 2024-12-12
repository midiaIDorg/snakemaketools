import typing
from pathlib import Path

import snakemaketools
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db as pony_db
from snakemaketools.models import SimplePonyNodeStorage


def parse_config_fill_db_get_wishlist(
    consolidated_config: dict,
    get_nodes: typing.Callable,
) -> dict:
    """Make paths. Fill up the DB. Provide wishlist.

    This code assumes that Pony db is already setup.
    """
    configs: DotDict = DotDict()
    for name, config in consolidated_config["config"].items():
        configs[name] = snakemaketools.rules.Config.new(**config, rule_name=name)

    node_storage = SimplePonyNodeStorage()
    raw_rule_configs = DotDict()
    rules = DotDict()
    for file, rule_configs in snakemaketools.parsers.iter_configs(
        Path("workflow").glob("**/*.smk")
    ):
        for rule_config in rule_configs:
            raw_rule_configs[rule_config["rule_name"]] = rule_config
            rules[rule_config["rule_name"]] = snakemaketools.rules.Rule.from_config(
                node_storage=node_storage,
                **rule_config,
            )

    str_wildcards = consolidated_config["wildcards"]
    wildcards = DotDict()
    for wildcard_name, wildcard_value in str_wildcards.items():
        wildcards[wildcard_name] = snakemaketools.rules.Wildcard(
            name=wildcard_name, value=wildcard_value
        )

    nodes = get_nodes(rules=rules, configs=configs, wildcards=wildcards)
    wished_for_nodes = {}
    for wish, final_location in consolidated_config["wishlist"].items():
        assert (
            wish in nodes
        ), f"You are wishing for unwishable: `{wish}`. Wish something else or whoosh!"
        wished_for_nodes[wish] = dict(nodes[wish])
        wished_for_nodes[wish]["final_location"] = final_location.format(
            **str_wildcards
        )

    return wished_for_nodes
