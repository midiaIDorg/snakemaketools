%load_ext autoreload
%autoreload 2
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
    for arg in (raw_data,config):
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


roots = DotDict(
    raw_data=Node.GETINSERT(origin={'dataset':'G8027'}, type="tdf.d"),
    config_precursor_clustering = Node.GETINSERT(origin={'hash':'adf23vs232'}, type="precursors_clustering.config"),
    config_fragment_clustering = Node.GETINSERT(origin={'hash':'fafgdfvsdf23'}, type="fragments_clustering.config"),
    config_baseline_removal = Node.GETINSERT(origin={'hash':'trhcfghr'}, type="baseline_removal.config"),
)

# script
def pipeline(
    raw_data: Node,
    config_baseline_removal: Node | None,
    config_precursor_clustering: Node,
    config_fragment_clustering: Node,
) -> DotDict:

    N = DotDict(
        raw_data=raw_data,
        config_baseline_removal=config_baseline_removal,
        config_precursor_clustering=config_precursor_clustering,
        config_fragment_clustering=config_fragment_clustering,
    )# N stands for Nodes.

    if config_baseline_removal is not None:
        N.raw_data = remove_rawdata_baseline(N.raw_data, N.config_baseline_removal)

    (
        N.precursors,
        N.precursor_clustering_stdout,
        N.precursor_clustering_stderr,
    ) = cluster_precursors(N.raw_data, N.config_precursor_clustering,)

    (
        N.fragments,
        N.fragment_clustering_stdout,
        N.fragment_clustering_stderr,
    ) = cluster_fragments(N.raw_data, N.config_fragment_clustering)

    return N# Nodes: ids of paths.



pipeline(**roots)
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
