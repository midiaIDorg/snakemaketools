# TODO: cool idea: make a script that checks for the all constrained occurences of an object in a database.
# TODO: make a scipt that given a path, reports back all of the steps needed to make this. But for that: we will need the rules to actually save their names.
#TODO: the test run can be simply executed first on the in-memory DB. only then in the perment one.
# TODO: there shouuld be a default node location corresponding to the general rule.
# TODO: there should be a mapping between name of script and its executable?
# TODO; these functions should be simply declared somehow in scripts.
# FOR NOW, assume that they are using named arguments.
%load_ext autoreload
%autoreload 2
from __future__ import annotations

import copy
import dataclasses
import pathlib
import typing
from abc import ABC, abstractmethod
from functools import partial
from pprint import pprint
from types import SimpleNamespace

import toml
from pony.orm import (Database, Optional, PrimaryKey, Required, Set, commit,
                      composite_index, db_session, set_sql_debug)

import midia_pipe_hull.pipelines.base
import snakemaketools.rules
from snakemaketools.datastructures import DotDict
from snakemaketools.encodings import partial_format
from snakemaketools.models import *

# set_sql_debug()

db.bind(provider='sqlite', filename=':memory:', create_db=True)

# db.bind(provider='sqlite', filename='/home/matteo/Projects/midia/pipelines/devel/midia_pipe/base.sqlite', create_db=True)

db.generate_mapping(create_tables=True)



config = "default"
with open(f"configs/consolidated/default.toml", "r") as f:
    consolidated_config = toml.load(f)
configs = DotDict(copy.deepcopy(consolidated_config["subconfigs"]))

configs.fragment_cluster_stats_config

dataset = "G8027"
calibration = "G8045" # | = None
fasta = "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer"

with open(f"configs/rules.json", "r") as f:
    rule_config = json.load(f)

node_storage = SimplePonyNodeStorage(debug=True)
rules = DotDict()
for rule_name, rule_subconfig in rule_config.items():
    rules[rule_name] = snakemaketools.rules.Rule(
        name=rule_name,
        node_storage=node_storage,
        expected_inputs=rule_subconfig["expected_inputs"],
        expected_outputs=tuple(
            node_storage.node_factory(**expected_output)
            for expected_output in rule_subconfig["expected_outputs"]
        )
    )

root_wildcards = dict(
    dataset=dataset,
    calibration=calibration,
    fasta=fasta,
)
for rule in rules.values():
    for expected_output in rule.expected_outputs:
        expected_output.location = partial_format(
            string=expected_output.location, **root_wildcards
        )

nodes = midia_pipe_hull.pipelines.base.get_nodes(
    rules=rules,
    configs=configs,
    **root_wildcards
)






nodes.additional_precursor_cluster_stats
nodes.tims_fragment_clusterer_config
subconfigs.tims_fragment_clusterer_config

path_ids = {k: node.id for k, node in paths.items() if node != None}
wishes = {wish: path_ids[wish] for wish in CONFIG["wishlist"]} 







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


# roots = DotDict(
#     raw_data = Node.GETINSERT(origin={'dataset':'G8027'}, type="tdf.d"),
#     precursor_clustering_config = Node.GETINSERT(origin={'hash':'adf23vs232'}, type="precursor_clustering_config"),
#     fragment_clustering_config = Node.GETINSERT(origin={'hash':'fafgdfvsdf23'}, type="fragment_clustering_config"),
#     config_baseline_removal = Node.GETINSERT(origin={'hash':'trhcfghr'}, type="baseline_removal_config"),
#     precursor_cluster_stats_config = Node.GETINSERT(origin={'hash':'rgrfdzExcerf'}, type="precursor_cluster_stats_config"),
#     fragment_cluster_stats_config = Node.GETINSERT(origin={'hash':'sfewfewf'}, type="fragment_cluster_stats_config"),
#     matching_config = Node.GETINSERT(origin={'hash':'dagaddsafdsafsa'}, type="matching_config"),
# )
# graph = pipeline(**roots)
# graph["rough_matches"].origin


# likely: do the same as with choosing the clustering algo
#   decide upon the pipeline paths construction.
# register_fasta = dict(
#     expected_inputs=dict(),
#     expected_outputs=dict(
#         # argument name
#         fasta=dict(
#             type="fasta",# argument type
#             path="fastas/{rule_id}.fasta", # path template
#         ),
#         # likely this should be a soft link after all?
#         # or we provide and override. Soft link for simplicity.
#     ),
#     meta=dict()
# ),
# register_raw_data = dict(
#     expected_outputs=dict(
#         folder_d=dict(type="raw_data", path="spectra/{rule_id}.d"),
#         analysis_tdf=dict(type="sqlite", path="spectra/{rule_id}.d/analysis.tdf"),
#         analysis_tdf_bin=dict(type="tdf_bin", path="spectra/{rule_id}.d/analysis.tdf_bin"),
#     )
# ),

    # get_tims_precursor_clustering_config=dict(
    #     expected_inputs=dict(),
    #     expected_outputs=dict(
    #         tims_precursor_clustering_config=dict(
    #             name="tims_precursor_clustering_config",
    #             path_template="tmp/configs/tims_precursor_clustering_config/{rule_id}.config",
    #         ),
    #     ),
    # ),
    # get_tims_fragment_clustering_config=dict(
    #     expected_inputs=dict(),
    #     expected_outputs=dict(
    #         tims_fragment_clustering_config=dict(
    #             name="tims_fragment_clustering_config",
    #             path_template="tmp/configs/tims_fragment_clustering_config/{rule_id}.config",
    #         )
    #     ),
    # ),
    # get_precursor_cluster_stats_config=dict(
    #     expected_inputs=dict(),
    #     expected_outputs=dict(
    #         precursor_cluster_stats_config=dict(
    #             name="precursor_cluster_stats_config",
    #             path_template="tmp/configs/precursor_cluster_stats_config/{rule_id}.toml",
    #         )
    #     ),
    # ),
    # get_fragment_cluster_stats_config=dict(
    #     expected_inputs=dict(),
    #     expected_outputs=dict(
    #         name="fragment_cluster_stats_config",
    #         path_template="tmp/configs/fragment_cluster_stats_config/{rule_id}.toml",
    #     ),
    # ),
    # get_matching_config=dict(
    #     expected_inputs=dict(),
    #     expected_outputs=dict(
    #         matching_config=dict(
    #             name="matching_config",
    #             path_template="tmp/configs/matching_config/{rule_id}.toml",
    #         )
    #     ),
    # ),
