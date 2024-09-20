%load_ext autoreload
%autoreload 2
from functools import partial
from pprint import pprint
from types import SimpleNamespace
from typing import Callable

import toml
from midia_pipe_hull.pipelines.base import pipeline
from pony.orm import commit, db_session, set_sql_debug
from snakemaketools.datastructures import DotDict
from snakemaketools.models import Path, RuleOrConfig, db

set_sql_debug()
db.bind(provider='sqlite', filename=':memory:', create_db=True)
# db.bind(provider='sqlite', filename='/home/matteo/Projects/midia/pipelines/devel/midia_pipe/base.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


with open("configs/consolidated/default.toml", "r") as f:
    config = toml.load(f)
    # pprint(config)

dataset = "G8027"
calibration = "G8045"
fasta = "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer"
subconfigs = config["subconfigs"]


paths = pipeline(subconfigs=subconfigs, dataset=dataset, calibration=calibration, fasta=fasta,)

paths["fasta"].path

paths["dataset"].parent_paths
paths["dataset_analysis_tdf_hash"].parent_paths
paths["dataset_analysis_tdf_hash"].parent_paths

RuleOrConfig[]

# would be nice to put some meta info during the run into the DB. 
# like runtime.

# how to pass in calibration=None?
# how to pass in a fasta?

# subconfig_name, subconfig = next(iter(config["subconfigs"].items()))



node_ids = {k: node.id for k, node in graph.items() if node != None}
node_ids# drop this to a json/toml.
# likely one rule should output that and the chosen things
# another shoud take it as input and produce the final thing.


Node[1].origin
Node[1].type
Node[1].id
Node[1].extension
 


# simpler solution: use raw strings.

Node[3].origin
Node[16].origin
Node[19].origin
Node[17].origin
Node[17].type


wildcards = SimpleNamespace(extension="toml")

node = Node[int(7)]
assert wildcards.extension == node.origin["extension"]
with
node.origin["config"]

Node[22].origin


# OK, this is really awesome: there will be no distinction between the configs made automatically and those we provide.


# should the consolidated config contain any paths or not? 
# It cannot now: snakemake might not know where to search for stuff.
# if it does not have it though, how would we call the outputs?
# again some convention likely necessary:
# where to store things?

# awesome: so pipeline can create the config roots.
# what about the other roots?
# this looks like a good place for softlinks.



# 

# what about the other things?
# dataset
# calibration (optional)
# fasta (1 and 2)

# what about if we want to test multiple configs?
# that's error prone: we could do it, but there won't be clear cut answer what was run.
# what about control flow?





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
