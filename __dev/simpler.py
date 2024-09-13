%load_ext autoreload
%autoreload 2
import json
from collections import OrderedDict
from dataclasses import dataclass

import networkx as nx
from pony.orm import *
from snakemaketools.datastructures import DotDict

set_sql_debug()
db = Database()


class Node(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    input_to_rule = Optional("Rule", reverse="inputs", index=True)
    rule_output = Optional("Rule", reverse="outputs")
    description = Required(str, index=True)
    datatype = Optional(str)
    extension = Optional(str)


class Rule(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    name = Required(str)  # Representation of a script.
    inputs = Set(Node, reverse="input_to_rule", index=True)
    outputs = Set(Node, reverse="rule_output")

db.bind(provider='sqlite', filename=':memory:', create_db=True)
db.generate_mapping(create_tables=True)


clustering_config = Node(
    description=json.dumps({'hash':'adf23vs232'}),
    datatype="clustering_config",
    extension=".config",
)
raw_data_root = Node(
    description=json.dumps({'dataset':'G8027'}),
    datatype="tdf",
    extension=".d",
)
commit()

clustering_config.id
raw_data_root.id

Rule.get()
