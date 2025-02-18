import snakemaketools.db_config

import json
import tomllib

from datetime import datetime

from pathlib import Path
from pony.orm import Database
from pony.orm import Json
from pony.orm import Optional
from pony.orm import PrimaryKey
from pony.orm import Required
from pony.orm import db_session

from snakemaketools.network import whoami


results_db = Database()


# registered only in the results_db
class Result(results_db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Required(
        datetime,
        precision=0,
        default=lambda: datetime.now(),
    )  # Date of the arrival of message.
    whoami = Optional(Json, default=whoami)
    reproducibility = Optional(Json)
    command = Optional(str, default="")
    consolidated_config = Optional(Json, default="")
    results = Required(Json)


def open_result(path: str | Path) -> list | dict:
    path = Path(path)
    match path.suffix:
        case ".json":
            with open(path, "r") as file:
                return json.load(file)
        case ".toml":
            with open(path, "rb") as file:
                return tomllib.load(file)
        case ".csv" | ".parquet" | ".startrek" | ".tsv":
            from pandas_ops.io import read_df

            return read_df(path).to_dict(orient="records")
        case other:
            raise NotImplementedError(f"Have no idea how to open `{path}`.")


@db_session
def send_results(
    config_initial_path: str | Path,
    consolidated_config_path: str | Path,
    command: str,
    result_paths: list[str | Path],
) -> Result:
    with open(config_initial_path, "rb") as file:
        config_initial = tomllib.load(file)

    with open(consolidated_config_path, "rb") as file:
        consolidated_config = tomllib.load(file)

    results = {str(path): open_result(path) for path in result_paths}

    return Result(
        command=command,
        reproducibility=config_initial,
        consolidated_config=consolidated_config,
        results=results,
    )


@db_session
def get_results() -> list[dict]:
    return [r.to_dict() for r in Result.select()]
