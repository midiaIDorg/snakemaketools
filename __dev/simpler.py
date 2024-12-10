# TODO: get the infrastructure to get the outputs back to the users.
# TODO: the test run can be simply executed first on the in-memory DB. only then in the perment one.
# TODO: turn this thing below into a click script shiped with snakemaketools.

%load_ext autoreload
%autoreload 2
from __future__ import annotations

import copy
import dataclasses
import json
import pathlib
import typing
from abc import ABC, abstractmethod
from functools import partial
from pprint import pprint
from types import SimpleNamespace

import duckdb
import toml
from mmapped_df import open_dataset_dct

import midia_pipe_hull.pipelines.base
import snakemaketools.models
import snakemaketools.rules
import tomllib
from pony.orm import (Database, Optional, PrimaryKey, Required, Set, commit,
                      composite_index, db_session, set_sql_debug)
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db
from snakemaketools.encodings import iter_brackets, partial_format
from snakemaketools.models import *
from snakemaketools.parsers import iter_configs
from snakemaketools.rules import Config, Node, Rule, Wildcard

# TODO:
# rename 
# configs.precursor_clusterer.location_wildcards.name -> 
# configs.precursor_clusterer.location_wildcards.mslevel
# expeced_wildcards should be a DotDict.

# set_sql_debug()
# wildcards
dataset = "G8027"
calibration = "G8045" # | = None
fasta = "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer"
consolidated_config_path = "configs/consolidated/default.toml"
# consolidated_config_path = "configs/consolidated/experimental_sagepy.toml"
# db_path = ":memory:"
db_path = "/home/matteo/Projects/midia/pipelines/devel/midia_pipe/base.sqlite"

db.bind(provider='sqlite', filename=db_path, create_db=True)
db.generate_mapping(create_tables=True)

with open(consolidated_config_path, "r") as f:
    consolidated_config = DotDict(toml.load(f))

configs = DotDict()
for name, config in consolidated_config.items():
    if name not in ("wildcards", "wishlist"):
        configs[name] = snakemaketools.rules.Config.new(**config, rule_name=name)

# somehow Wildcards are directly saved to DB....
# location wildcards must be Wildcards.
node_storage = SimplePonyNodeStorage()
raw_rule_configs = DotDict()
rules = DotDict()
for file, rule_configs in iter_configs(pathlib.Path("workflow").glob("**/*.smk")):
    for rule_config in rule_configs:
        raw_rule_configs[rule_config["rule_name"]] = rule_config
        rules[rule_config["rule_name"]] = snakemaketools.rules.Rule.from_config(
            node_storage=node_storage,
            **rule_config,
        )

str_wildcards = DotDict(
    dataset=dataset,
    calibration=calibration,
    fasta=fasta,
    **consolidated_config["wildcards"]
)
wildcards = DotDict()
for wildcard_name, wildcard_value in str_wildcards.items():
    wildcards[wildcard_name] = snakemaketools.rules.Wildcard(name=wildcard_name, value=wildcard_value)




nodes = midia_pipe_hull.pipelines.base.get_nodes(
    rules=rules,
    configs=configs,
    wildcards=wildcards
)


json.dumps({ node_name: dict(node) for node_name, node in nodes.items()})



# node_storage = SimplePonyNodeStorage(debug=True)
# rules = DotDict()
# for rule_name, rule_config in rule_configs.items():
#     rules[rule_name] = snakemaketools.rules.Rule.from_config(
#         rule_name=rule_name,
#         node_storage=node_storage,
#         **rule_config
#     )


# for rule in rules.values():
#     for expected_output in rule.expected_outputs:
#         expected_output.location = partial_format(
#             string=expected_output.location, **wildcards
#         )


path_ids = {k: node.id for k, node in paths.items() if node != None}
wishes = {wish: path_ids[wish] for wish in CONFIG["wishlist"]} 


class T:
    def __init__(self):
        self.data = {'a': 1, 'b': 2, 'c': 3}
    
    def __iter__(self):
        return iter(self.data)  # Return an iterator over the keys
    
    def __getitem__(self, key):
        return self.data[key]  # Return the value for the given key

t = T()
print(dict(t))

??dict
