%load_ext autoreload
%autoreload 2
from pathlib import Path

import toml

from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import setup_db
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration

setup_db(verbose=True)

consolidated_config_path = "configs/consolidated/default.toml"
with open(consolidated_config_path, "r") as f:
    consolidated_config = DotDict.Recursive(toml.load(f))

get_nodes_path = "midia_pipe_hull.pipelines.base::get_nodes"
longsnake = LongSnakeConfiguration(
    consolidated_config=consolidated_config,
    get_nodes=dynamically_import_foo(get_nodes_path),
    smk_file_paths=Path("workflow").glob("**/*.smk"),
)
diff = "G8027/None"
longsnake.update_consolidated_config(diff)

rules = longsnake.rules
configs = longsnake.configs
wildcards = longsnake.wildcards


longsnake.nodes


# this is stupidly repeated

nodes = longsnake.nodes

nodes.refined_matches_stats
nodes.first_gen_search_fragments
nodes.remaining_first_gen_edges_counts
nodes.refined_matches_qc
nodes.refined_nodes_quality_checks
