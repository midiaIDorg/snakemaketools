import json
from pathlib import Path
from warnings import warn

import click
import snakemaketools
import toml
import yaml
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db as pony_db
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.models import SimplePonyNodeStorage


# consolidated_config = "configs/consolidated/default.toml"
# pipeline_definition = "base"
# # where to `pipeline_definition` that??? it should be importable
# snakemake_config = "configs/snakemake.yaml"
# output_nodes = "/tmp/output_nodes.json"
# db = "base.sqlite"
# wildcard = (
#     ("dataset", "G8027"),
#     ("calibration", "G8045"),
#     (
#         "fasta",
#         "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer",
#     ),
# )
@click.command(context_settings={"show_default": True})
@click.argument("consolidated_config", type=Path)
@click.argument("pipeline_definition")
@click.argument("snakemake_config", type=Path)
@click.argument("output_nodes", type=Path)
@click.option(
    "--db",
    help="Override `db` from yaml-based `snakemake_config`.",
    default=None,
)
@click.option(
    "--wildcard",
    "-w",
    type=(str, str),
    multiple=True,
    help="Pass in name of the wildcard and value tuples.",
    default=None,
)
@click.option("--verbose", is_flag=True, help="Be verbose.")
def snake_out_paths(
    consolidated_config,
    pipeline_definition,
    snakemake_config,
    output_nodes,
    db: str | None = None,
    wildcard: tuple[tuple[str, str], ...] = (),
    verbose: bool = False,
) -> None:
    """Make paths: fill up out_db.

    To mock, pass in `db` equal to `:memory:`; otherwise, the provide `connection` will be used directly and contain paths.
    """

    # TODO: find a nicer way to say which pipelines are OK to choose from.
    if not pipeline_definition in ("base",):
        msg = f"You are trying to use an unauthorized python script `pipeline_definition` that someone maliciously put in `midia_pipe_hull.pipelines.{pipeline_definition}`."
        warn(msg)

    with open(snakemake_config, "r") as file:
        snakemake_conf = yaml.safe_load(file)

    db_setup = snakemake_conf["db"]

    if db is not None:
        db_setup["filename"] = db
    db_setup["filename"] = str(Path.cwd() / db_setup["filename"])

    pony_db.bind(**db_setup)
    pony_db.generate_mapping(create_tables=True)

    with open(consolidated_config, "r") as f:
        consolidated_conf: dict = DotDict(toml.load(f))

    configs: DotDict = DotDict()
    for name, config in consolidated_conf.items():
        if name not in ("wildcards", "wishlist"):
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

    str_wildcards = consolidated_conf["wildcards"]
    str_wildcards.update(dict(wildcard))
    wildcards = DotDict()
    for wildcard_name, wildcard_value in str_wildcards.items():
        wildcards[wildcard_name] = snakemaketools.rules.Wildcard(
            name=wildcard_name, value=wildcard_value
        )

    get_nodes = dynamically_import_foo(
        f"midia_pipe_hull.pipelines.{pipeline_definition}::get_nodes"
    )
    nodes = get_nodes(rules=rules, configs=configs, wildcards=wildcards)
    wished_for_nodes = {}
    for wish, final_location in consolidated_conf["wishlist"].items():
        assert (
            wish in nodes
        ), f"You are wishing for unwishable: `{wish}`. Wish something else or whoosh!"
        wished_for_nodes[wish] = dict(nodes[wish])
        wished_for_nodes[wish]["final_location"] = final_location.format(
            **str_wildcards
        )

    with open(output_nodes, "w") as file:
        json.dump(wished_for_nodes, file, indent=4)
