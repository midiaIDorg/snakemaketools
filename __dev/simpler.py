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

    return DotDict(
        data = Node.GETINSERT(origin=_origin, type="clusters.startrek"),
        stdout = Node.GETINSERT(origin=_origin, type="stdoud.txt"),
        stderr = Node.GETINSERT(origin=_origin, type="stderr.txt"),
    )

cluster_fragments = cluster_precursors = cluster

def get_cluster_stats(clusters: Node, config: Node) -> Node:
    for arg in (raw_data,config):
        assert arg.id is not None

    _origin = dict(
        rule='get_cluster_stats',
        inputs=dict(clusters=clusters.id, config=config.id),
    )

    return DotDict(data=Node.GETINSERT(origin=_origin, type="cluster_stats.parquet"))


def remove_rawdata_baseline(raw_data: Node, config: Node) -> Node:
    for arg in (raw_data, config):
        assert arg.id is not None

    _origin = dict(
        rule="remove_rawdata_baseline",
        inputs=dict(raw_data=raw_data.id, config=config.id),
    )

    return DotDict(data=Node.GETINSERT(origin=_origin, type="tdf.d"))


# script

#roots
roots = DotDict(
    raw_data=Node.GETINSERT(origin={'dataset':'G8027'}, type="tdf.d"),
)
configs = DotDict(
    precursors_clustering = Node.GETINSERT(origin={'hash':'adf23vs232'}, type="precursors_clustering.config"),
    fragments_clustering = Node.GETINSERT(origin={'hash':'fafgdfvsdf23'}, type="fragments_clustering.config"),
    baseline_removal = Node.GETINSERT(origin={'hash':'trhcfghr'}, type="baseline_removal.config"),
)

raw = remove_rawdata_baseline(roots.raw_data, configs.baseline_removal)

# might fall back to using DotDict...
precursors = cluster_precursors(raw.data, configs.precursors_clustering)

# for _ in range(3):
#     if else:
raw = remove_rawdata_baseline(raw.data, configs.baseline_removal)



precursors2 = cluster(raw.data, configs.precursors_clustering)

fragments = cluster_fragments(raw.data, configs.fragments_clustering)




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
