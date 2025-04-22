# TODO: add names to rule.nodes (perhaps, any nodes?). This will make it simpler to refer to.
"""
%load_ext autoreload
%autoreload 2
"""
import toml

from pathlib import Path
from snakemaketools.db_config import setup_db
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration


setup_db(verbose=True)
get_nodes_path = "midia_pipe_hull.pipelines.base::get_nodes"
consolidated_config_path = "configs/consolidated/debug_clustering.toml"

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
longsnake.update_consolidated_config("diff_adding_back_physical_4DFF/F9477")

longsnake.consolidated_config["wildcards"]
longsnake.configs.precursor_clusterer.parsed
longsnake.configs.precursor_clusterer.location_wildcards
longsnake.configs
