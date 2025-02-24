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

from snakemaketools.network import get_local_ip
from snakemaketools.network import get_pipeline_location
from snakemaketools.network import get_server
from snakemaketools.network import get_user


results_db = Database()


# registered only in the results_db
class Result(results_db.Entity):
    id = PrimaryKey(int, auto=True)
    date = Required(
        datetime,
        precision=0,
        default=lambda: datetime.now(),
    )  # Date of the arrival of message.
    ip_address = Optional(str, default=get_local_ip)
    user_name = Optional(str, default=get_user)
    server_name = Optional(str, default=get_server)
    cwd = Optional(str, default=get_pipeline_location)
    config_initial = Optional(str)
    config_freezed = Optional(str)
    command = Optional(str, default="")
    consolidated_config = Optional(str, default="")
    results = Required(str)


# def open_result(path: str | Path) -> list | dict:
#     path = Path(path)
#     match path.suffix:
#         case ".json":
#             with open(path, "r") as file:
#                 return json.load(file)
#         case ".toml":
#             with open(path, "rb") as file:
#                 return tomllib.load(file)
#         case ".csv" | ".parquet" | ".startrek" | ".tsv":
#             from pandas_ops.io import read_df

#             return read_df(path).to_dict(orient="records")
#         case other:
#             raise NotImplementedError(f"Have no idea how to open `{path}`.")


def open_result(path: str | Path) -> list | dict:
    path = Path(path)
    match path.suffix:
        case ".json" | ".csv" | ".tsv" | ".toml":
            with open(path, "r") as file:
                return file.read()
        case ".parquet" | ".startrek":
            from pandas_ops.io import read_df

            return json.dumps(read_df(path).to_dict(orient="records"))
        case other:
            raise NotImplementedError(f"Have no idea how to open `{path}`.")


@db_session
def send_results(
    config_initial_path: str | Path,
    config_freezed_path: str | Path,
    consolidated_config_path: str | Path,
    command: str,
    result_paths: list[str | Path],
) -> Result:
    with open(config_initial_path, "r") as file:
        # config_initial = tomllib.load(file)
        config_initial = file.read()

    with open(config_freezed_path, "r") as file:
        # config_freezed = tomllib.load(file)
        config_freezed = file.read()

    with open(consolidated_config_path, "r") as file:
        # consolidated_config = tomllib.load(file)
        consolidated_config = file.read()

    results = {str(path): open_result(path) for path in result_paths}

    return Result(
        command=command,
        config_initial=config_initial,
        config_freezed=config_freezed,
        consolidated_config=consolidated_config,
        results=results,
    )


@db_session
def get_results() -> list[dict]:
    return [r.to_dict() for r in Result.select()]
