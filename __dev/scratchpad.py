%load_ext autoreload
%autoreload 2
import json
from collections import OrderedDict
from dataclasses import dataclass

import networkx as nx
from pony.orm import *
from snakemaketools.datastructures import DotDict

# nodes = ints
# OK, so lexicographically sorted list of edges will go to the DB.
# G = nx.Graph()
# G.add_edge(1, 3)
# G.add_edge(3, 4)
# G.add_edge(1, 2)
# G.add_edge(4, 5)
# G.add_edge(2, 4)
# G_serialized = json.dumps(sorted(G.edges))
# G_serialized
# # The DB will contain a mapping:
# serialized_graph: str -> (id: uint, output_type: str, extension: str)

set_sql_debug()
db = Database()


class Root(db.Entity):
    id = PrimaryKey(int, unsigned=True, auto=True)
    description = Required(str)  # Check for ordering.
    datatype = Required(str)
    extension = Required(str)
    composite_index(description, datatype, extension)

class Node(db.Entity):
    id = PrimaryKey(int, unsigned=True, auto=True)
    genealogy = Required(str)  # Lexicographically sorted edges of indices.
    datatype = Required(str)
    extension = Required(str)
    composite_index(genealogy, datatype, extension)


db.bind(provider='sqlite', filename=':memory:', create_db=True)
# db.bind(provider='sqlite', filename='/tmp/test.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

@db_session
def get_or_create_entry(Table, info: dict):
    info = {k: json.dumps(v) if isinstance(v,dict) else v for k, v in info.items()}
    entry = Table.get(**info)
    commit()
    if entry:
        return entry
    else:
        new_entry = Table(**info)
        commit()
        return new_entry

# this will need to be prepped by a script parsing the inputs for the pipeline.
root_candidates = dict(
    clustering_config=dict(description={'hash':'adf23vs232'}, datatype="clustering_config", extension=".config"),
    raw_data_root = dict(description={'dataset':'G8027'}, datatype="tdf", extension=".d"),
)

def get_root_and_node(root_info: dict) -> tuple[Root, Node]:
    root = get_or_create_entry(Root, root_info)
    commit()
    node_info = root_info.copy()
    del node_info["description"]
    node_info["genealogy"] = dict(nodes = [root.id], edges = [])
    node = get_or_create_entry(Node, node_info)
    commit()
    return root_id, node_id

roots = {k: get_root_and_node(kwargs) for k, kwargs in root_candidates.items()}

def root_candidate_to_node_candidate(root):
    del root[]
    return 




# Should I not have an optional 
# why do I need to distinguish roots in the DB? cause they have a description and that has a different index than a node.
# and I need to put it into the graph.

clustering_config.id
commit()
clustering_config.id


w = Root.get(description=json.dumps({'dataset':'G8027'}), datatype="tdf", extension=".d")
json.loads(w.description)

# OK, so until we commit, we don't have no id.
list(select( r for r in Root))[0].description# this needs to be @db_session(-ed) to work outside the interpreter.



G = nx.Graph()
G.add_node(clustering_config)





def Cluster(raw_data: Node, config: Node) -> tuple[Node, Node, Node, Node]:
    rule_node = Node(local_id=len(G.nodes), data_type="rule_cluster")

    assert raw_data.data_type == "raw_data"
    assert config.data_type == "clustering_config"

    G.add_edge(raw_data, rule_node)
    G.add_edge(config, rule_node)

    def add_edge(**kwargs):
        node = Node(**kwargs)
        G.add_edge(rule_node, node)
        return node

    outs = (
        add_edge(
            local_id=len(G.nodes),
            data_type="cluster",
            file_extension=".startrek",
        ),
        add_edge(
            local_id=len(G.nodes),
            data_type="cluster_stats",
            file_extension=".startrek",
        ),
        add_edge(
            local_id=len(G.nodes),
            data_type="stdout",
            file_extension=".txt",
        ),
        add_edge(
            local_id=len(G.nodes),
            data_type="stderr",
            file_extension=".txt",
        ),
    )

    for out in outs:
        G.add_edge(rule_node, out)

    return outs


clustering_config = Node(len(G.nodes), -1, "clustering_config", ".toml")
raw_data = Node(len(G.nodes), -1, "raw_data", ".startrek")

roots = [clustering_config, raw_data]
for root in roots:
    G.add_node(root)

clusters, cluster_stats, clustering_stdout, clustering_stderr = Cluster(
    raw_data, clustering_config
)

G.edges
# @dataclass
# class Root :

# @dataclass
# class Node:
#     subgraph: nx.Graph
#     db_id: int = -1
#     data_type: str = ""  # Maybe this should be some subinstance.
#     file_extension: str = ""

# @dataclass
# class Node:
#     local_id: int
#     db_id: int = -1
#     data_type: str = ""
#     file_extension: str = ""

#     def __hash__(self):
#         return self.local_id


# def get_raw_data() -> Node:
#     return Node(local_id=len(G.nodes), data_type="raw_data", file_extension=".startrek")
