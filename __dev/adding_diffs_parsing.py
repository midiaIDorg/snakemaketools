# TODO: add names to rule.nodes (perhaps, any nodes?). This will make it simpler to refer to.
"""
%load_ext autoreload
%autoreload 2
"""
import json
import shutil
import subprocess
import timeit
from functools import partial
from pathlib import Path
from statistics import median
from subprocess import run

import toml
from numba_progress import ProgressBar

import dia_common
import dia_common.precursor_prediction
import numba
import numpy as np
import numpy.typing as npt
import pandas as pd
import tomllib
from midia_schemes.main import get_midia_steps
from mmapped_df import IndexedReader
from pandas_ops.io import read_df, save_df
from pandas_ops.lex_ops import LexicographicIndex
from pandas_ops.stats import weighted_mean_and_var
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import setup_db
from snakemaketools.debug_tools import (
    copy_path,
    replace_filesystem_entry,
    restore_backup,
)
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration


setup_db(verbose=True)
get_nodes_path = "midia_pipe_hull.pipelines.base::get_nodes"
consolidated_config_path = "configs/consolidated/devel.toml"

with open(consolidated_config_path, "r") as f:
    consolidated_config = toml.load(f)
longsnake = LongSnakeConfiguration(
    consolidated_config=consolidated_config,
    get_nodes=dynamically_import_foo(get_nodes_path),
    smk_file_paths=Path("workflow").glob("**/*.smk"),
)
longsnake.consolidated_config["wildcards"]
longsnake.consolidated_config["config"]["precursor_clusterer"]["config"][
    "aggregateScale1"
]
longsnake.update_consolidated_config("diff_test/G8027/G8053/False")

longsnake.consolidated_config["wildcards"]

rules = longsnake.rules
configs = longsnake.configs
wildcards = longsnake.wildcards
nodes = longsnake.nodes

list(nodes)

config.mgf_config.config.verbose = false


update = "True"
bool("True")
bool("False")


type("False")
type(False)
from snakemaketools.datastructures import DotDict

x = DotDict(a=10, b=50)
x.update(c=10, a=4)
y = DotDict(a=100, c=100)
x.update(y)
Path("tets.xed").suffix
Path("tets").suffix

".{ext}" in "tets.{ext}"


def apply_value_update(original: str | int | float | bool, update: str):
    if type(original) in (int, float):
        return type(original)(update)
    elif type(original) == bool:
        return update.lower() == "true"
    elif isintance(original, str):
        return update
    else:
        raise ValueError("Unrecognized type.")


apply_value_update(True, "false")
apply_value_update(True, "true")
apply_value_update(10, "10")
apply_value_update(10, "10.1")
apply_value_update(10.2, "10.1")
