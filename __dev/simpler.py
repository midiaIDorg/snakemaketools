%load_ext autoreload
%autoreload 2
from pprint import pprint
from typing import Callable

import toml
from pony.orm import set_sql_debug
from snakemaketools.datastructures import DotDict
from snakemaketools.models import Node, db

set_sql_debug()
db.bind(provider='sqlite', filename=':memory:', create_db=True)
# db.bind(provider='sqlite', filename='/tmp/test.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


def cluster(raw_data: Node, config: Node) -> tuple[Node,Node,Node]:
    for arg in (raw_data,config):
        assert arg.id is not None

    _origin = dict(
        rule='cluster',
        inputs=dict(raw_data=raw_data.id, config=config.id),
    )

    data = Node.GETINSERT(origin=_origin, type="clusters.startrek")
    stdout = Node.GETINSERT(origin=_origin, type="stdoud.txt")
    stderr = Node.GETINSERT(origin=_origin, type="stderr.txt")

    return data, stdout, stderr

cluster_fragments = cluster_precursors = cluster


def get_cluster_stats(clusters: Node, config: Node) -> Node:
    for arg in (clusters,config):
        assert arg.id is not None

    _origin = dict(
        rule='get_cluster_stats',
        inputs=dict(clusters=clusters.id, config=config.id),
    )

    cluster_stats = Node.GETINSERT(origin=_origin, type="cluster_stats.parquet")
    return cluster_stats



def remove_rawdata_baseline(raw_data: Node, config: Node) -> Node:
    for arg in (raw_data, config):
        assert arg.id is not None

    _origin = dict(
        rule="remove_rawdata_baseline",
        inputs=dict(raw_data=raw_data.id, config=config.id),
    )

    raw_data_without_baseline = Node.GETINSERT(origin=_origin, type="tdf.d")
    return raw_data_without_baseline


def match_precursors_and_fragments(precursor_stats: Node, fragment_stats: Node, matching_config: Node) -> Node:
    for arg in (precursor_stats, fragment_stats, matching_config):
        assert arg.id is not None

    _origin = dict(
        rule="match_precursors_and_fragments",
        inputs=dict(precursor_stats=precursor_stats.id, fragment_stats=fragment_stats.id, matching_config=matching_config.id)
    )
    
    rough_matches = Node.GETINSERT(origin=_origin, type="rough_matches.startrek")

    return rough_matches



roots = DotDict(
    raw_data = Node.GETINSERT(origin={'dataset':'G8027'}, type="tdf.d"),
    precursor_clustering_config = Node.GETINSERT(origin={'hash':'adf23vs232'}, type="precursor_clustering_config"),
    fragment_clustering_config = Node.GETINSERT(origin={'hash':'fafgdfvsdf23'}, type="fragment_clustering_config"),
    config_baseline_removal = Node.GETINSERT(origin={'hash':'trhcfghr'}, type="baseline_removal_config"),
    precursor_cluster_stats_config = Node.GETINSERT(origin={'hash':'rgrfdzExcerf'}, type="precursor_cluster_stats_config"),
    fragment_cluster_stats_config = Node.GETINSERT(origin={'hash':'sfewfewf'}, type="fragment_cluster_stats_config"),
    matching_config = Node.GETINSERT(origin={'hash':'dagaddsafdsafsa'}, type="matching_config"),
)


# script
def pipeline(
    raw_data: Node,
    precursor_clustering_config: Node,
    fragment_clustering_config: Node,
    precursor_cluster_stats_config: Node,
    fragment_cluster_stats_config: Node,
    matching_config: Node,
    # defaults
    config_baseline_removal: Node | None = None,# not passed
) -> DotDict:

    N = DotDict(
        raw_data=raw_data,
        config_baseline_removal=config_baseline_removal,
        precursor_clustering_config=precursor_clustering_config,
        fragment_clustering_config=fragment_clustering_config,
        precursor_cluster_stats_config=precursor_cluster_stats_config,
        fragment_cluster_stats_config=fragment_cluster_stats_config,
        matching_config=matching_config,
    )# N stands for Nodes.

    if config_baseline_removal is not None:
        N.raw_data = remove_rawdata_baseline(N.raw_data, N.config_baseline_removal)

    (
        N.precursors,
        N.precursor_clustering_stdout,
        N.precursor_clustering_stderr,
    ) = cluster_precursors(N.raw_data, N.precursor_clustering_config)

    (
        N.fragments,
        N.fragment_clustering_stdout,
        N.fragment_clustering_stderr,
    ) = cluster_fragments(N.raw_data, N.fragment_clustering_config)

    N.precursor_stats = get_cluster_stats(
        N.precursors,
        N.precursor_cluster_stats_config,
    )

    N.fragment_stats = get_cluster_stats(
        N.fragments,
        N.fragment_cluster_stats_config,
    )

    N.rough_matches = match_precursors_and_fragments(
        N.precursor_stats,
        N.fragment_stats,
        N.matching_config,
    )

    return N # Nodes: paths ids.

# OK, make a consolidated config for the simple pipeline above.


# OK, this is really awesome: there will be no distinction between the configs made automatically and those we provide.


# def parser(id):
#     node = Node.GETINSERT(id)
#     origin = json.loads(node.origin)
#     return dict(
#         a = origin.inputs["a"],
#         b = origin.inputs["b"],
#         c = origin.inputs["c"],
#     )

# rule cluster:
#     input:
#         unpack(parser)
#     output: 
#         "blablalba/{id}.parquet"



# how to proceed now? 

# plan it well: 

# how should one deal with the config -> configs?
# * a script should simply put all of those configs in proper places while filling the DB about them. No, first fill it in, then copy all in right places.
# * fill in the DB with other nodes
# * finally, call Snakemake

# how should the script know what are the configs?
# Node._origin json can 
# We need to know which of the thing was filled.

with open("__dev/consolidated_config.toml", "r") as f:
    config = toml.load(f)
    pprint(config)

# we should somehow turn that to None?
# config["baseline_removal_config"]
config["precursor_clustering_config"]["config"]
config["matching_config"]["config"]
config["precursor_cluster_stats_config"]["config"]


roots = DotDict()
for subconfig_name, subconfig in config["subconfigs"].items():
    print(subconfig_name, subconfig["config"])
    roots[subconfig_name] = Node.GETINSERT(origin=subconfig["config"], type=subconfig_name),

# what about the other things?
# dataset
# calibration (optional)
# fasta (1 and 2)

# what about if we want to test multiple configs?
# that's error prone: we could do it, but there won't be clear cut answer what was run.
# what about control flow?




# roots = DotDict()
# roots

roots = DotDict(
    raw_data = Node.GETINSERT(origin={'dataset':'G8027'}, type="tdf.d"),
    precursor_clustering_config = Node.GETINSERT(origin={'hash':'adf23vs232'}, type="precursor_clustering_config"),
    fragment_clustering_config = Node.GETINSERT(origin={'hash':'fafgdfvsdf23'}, type="fragment_clustering_config"),
    config_baseline_removal = Node.GETINSERT(origin={'hash':'trhcfghr'}, type="baseline_removal_config"),
    precursor_cluster_stats_config = Node.GETINSERT(origin={'hash':'rgrfdzExcerf'}, type="precursor_cluster_stats_config"),
    fragment_cluster_stats_config = Node.GETINSERT(origin={'hash':'sfewfewf'}, type="fragment_cluster_stats_config"),
    matching_config = Node.GETINSERT(origin={'hash':'dagaddsafdsafsa'}, type="matching_config"),
)

pipeline(**roots)
# who makes a config?
# a rule makes a config!
# a fucking snakemake rule that is asked for a fucking:
# configs/{configuration_of_what}/id.{extension}
# and asks the fucking DB for that fucking config!
# and the Snakemake makes that fucking config.
# And angels cry.
# And Michał stares in amazement.

# And what about the silly willy other inputs? like:
# * datasets
# * optional calibration datasets
# * fastas
# those can be stuck by the silly 

# the pipeline can simply copy them to the id-based location / or soft link.


# big question: if we have two ways of executing a Node, how do we call it?
# That's like indpendent of the setup of ids. But should be encoded in the rules.
# But should a rule decide upon the script used? 
# Not a bad idea: we could simply encode the path to the executable as we did and that will match the right rule.

# Another idea: we can put configs with wildcards: these could be filled up automatically.
# It would be nice to have some assertions at some point.

# but the idea of storing paths in the rules is not a bad one? but how could those be of importance? Because when Snakemake asks for an id it could also ask for its parents ids and paths.

# input:
#     parent_node.path.fill() for parent_node in node.origin
