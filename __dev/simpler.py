%load_ext autoreload
%autoreload 2
from pathlib import Path

import pony.orm
import toml

from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration

consolidated_config_path = "configs/consolidated/default.toml"
with open(consolidated_config_path, "r") as f:
    consolidated_config = DotDict.Recursive(toml.load(f))

pony.orm.set_sql_debug()
db_path = "base.sqlite"
db_path = "/home/matteo/MIDIA/midia_experiments/matteo_devel/pipelines/devel/midia_pipe/base.sqlite"

db.bind(provider='sqlite', filename=db_path, create_db=True)
db.generate_mapping(create_tables=True)

get_nodes_path = "midia_pipe_hull.pipelines.base::get_nodes"
longsnake = LongSnakeConfiguration(
    consolidated_config=consolidated_config,
    get_nodes=dynamically_import_foo(get_nodes_path),
    smk_file_paths=Path("workflow").glob("**/*.smk"),
)
longsnake.wildcards
longsnake.rules
longsnake.nodes

# this is stupidly repeated

nodes = longsnake.nodes

nodes.refined_matches_stats
nodes.first_gen_search_fragments
nodes.remaining_first_gen_edges_counts
nodes.refined_matches_qc
nodes.refined_nodes_quality_checks
