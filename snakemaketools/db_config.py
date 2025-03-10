from pathlib import Path

from pony.orm import Database
from pony.orm import set_sql_debug


import tomllib

# TODO: perhaps this should not be here at all??? Move it out elsewhere.
db = Database()


def setup_db(
    provider: str = "sqlite",
    filename: str | Path = "dbs/base.sqlite",
    create_db: bool = True,
    create_tables: bool = True,
    verbose: bool = False,
    db: Database = db,
) -> Database:
    """A wrapper to setup the DB."""
    if verbose:
        set_sql_debug()

    filename = Path(filename)
    filename = filename if filename.is_absolute() else Path.cwd() / filename

    db.bind(provider=provider, filename=str(filename), create_db=create_db)
    db.generate_mapping(create_tables=create_tables)

    return db


def setup_db_from_config(
    config_path: str | Path,
    db: Database,
    create_tables: bool = True,
    verbose: bool = False,
) -> dict:
    if verbose:
        set_sql_debug()

    with open(config_path, "rb") as file:
        config = tomllib.load(file)

    if len(config) > 0:
        if (
            "filename" in config
            and config["filename"] != ":memory:"
            and not Path(config["filename"]).is_absolute()
        ):
            config["filename"] = str(Path.cwd() / config["filename"])

        db.bind(**config)
        db.generate_mapping(create_tables=create_tables)

    return config
