import click

from pathlib import Path


from snakemaketools.db_config import setup_db
from snakemaketools.models import Node


@click.command(context_settings={"show_default": True})
@click.argument("location", type=Path)
@click.option("--path_db", help="DB with paths.", default="dbs/base.sqlite", type=Path)
@click.option("--verbose", help="Talk to your stdout.", is_flag=True)
def get_node_lineage(
    location: Path,
    path_db: Path,
    verbose: bool = False,
):
    """Establish all of the parent nodes of a given pipeline location."""
    match path_db.suffix:
        case ".sqlite":
            db = setup_db(
                provider="sqlite",
                filename=str(path_db),
                create_db=False,
                create_tables=False,
                verbose=verbose,
            )
            try:
                for path in Node.GET_LINEAGE(str(location)):
                    print(path)
            except KeyError as exc:
                print(f"`{location}` absent in the DB.")

        case other:
            raise NotImplementedError(f"Do not know how to connect to `{path_db}`.")
