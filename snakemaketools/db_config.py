import pathlib

from pony.orm import Database, set_sql_debug

db = Database()


def setup_db(
    provider: str = "sqlite",
    filename: str = "base.sqlite",
    create_db: bool = True,
    create_tables: bool = True,
    verbose: bool = False,
) -> None:
    """A wrapper to setup the DB."""
    if verbose:
        set_sql_debug()

    if filename == "base.sqlite":
        filename = str(pathlib.Path.cwd() / "base.sqlite")

    db.bind(provider=provider, filename=filename, create_db=create_db)
    db.generate_mapping(create_tables=create_tables)
