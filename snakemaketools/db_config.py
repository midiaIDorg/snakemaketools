from pathlib import Path

from pony.orm import Database
from pony.orm import set_sql_debug


import tomllib

# TODO: perhaps this should not be here at all??? Move it out elsewhere.
db = Database()


def setup_db(
    provider: str = "sqlite",
    filename: str = "base.sqlite",
    create_db: bool = True,
    create_tables: bool = True,
    verbose: bool = False,
    db: Database = db,
) -> None:
    """A wrapper to setup the DB."""
    if verbose:
        set_sql_debug()

    if filename == "base.sqlite":
        filename = str(Path.cwd() / "base.sqlite")

    db.bind(provider=provider, filename=filename, create_db=create_db)
    db.generate_mapping(create_tables=create_tables)


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
