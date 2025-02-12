import click

from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import setup_db
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration

import tomllib

from pathlib import Path


@click.command(context_settings={"show_default": True})
@click.argument("config", type=Path)
@click.argument("output", type=Path)
@click.argument("diff")
@click.option("--pipeline_name", help="Pipeline file.", default="base")
@click.option("--verbose", help="Be verbose.", is_flag=True)
def get_pipeline_nodes(
    config: Path,
    output: Path,
    diff: str,
    pipeline_name: str = "base",
    verbose: bool = True,
):
    setup_db(verbose=verbose, filename=":memory:")
    with open(config, "rb") as f:
        consolidated_config = DotDict.Recursive(tomllib.load(f))

    longsnake = LongSnakeConfiguration(
        consolidated_config=consolidated_config,
        get_nodes=dynamically_import_foo(
            f"midia_pipe_hull.pipelines.{pipeline_name}::get_nodes"
        ),
        smk_file_paths=Path("workflow").glob("**/*.smk"),
    )
    longsnake.update_consolidated_config(diff)
    nodes = list(longsnake.nodes)

    with open(output, "w") as f:
        for node in nodes:
            f.writelines(f"{node}\n")
