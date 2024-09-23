%load_ext autoreload
%autoreload 2
from __future__ import annotations

import dataclasses
import pathlib
from functools import partial
from pprint import pprint
from types import SimpleNamespace
from typing import Callable

import toml
from pony.orm import commit, db_session, set_sql_debug

from midia_pipe_hull.pipelines.base import fill_DB_with_paths
from snakemaketools.datastructures import DotDict
from snakemaketools.models import (Path, RuleOrConfig,
                                   add_rule_and_paths_to_DB, db)
from snakemaketools.rules import Rules

set_sql_debug()
db.bind(provider='sqlite', filename=':memory:', create_db=True)
# db.bind(provider='sqlite', filename='/home/matteo/Projects/midia/pipelines/devel/midia_pipe/base.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

dataset = "G8027"
calibration = "G8045"
fasta = "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer"
config = "default"
pipeline = "base"

with open(f"configs/consolidated/{config}.toml", "r") as f:
    CONFIG = toml.load(f)
    # pprint(config)
subconfigs = CONFIG["subconfigs"]

# Question: how to pass in the version of the software? Tims must be specified alongside other configs? No, better: simply one of the inputs should contain the proper path. But when is it passed in? Likely in the pipeline function: this is where we have access to configs anyway.
# OK, so the pipeline should get the consolidated config and decide upon all of that. It anyway needs to read in the configs below that specify the rules too.
# so a pipeline will get 2 files.

# try to write some rules for the configs.

rule_config = dict(
    # likely: do the same as with choosing the clustering algo
    #   decide upon the pipeline paths construction.
    register_fasta = dict(
        inputs=dict(),
        outputs=dict(
            # argument name
            fasta=dict(
                type="fasta",# argument type
                path="tmp/fastas/{rule_id}.fasta", # path template
            ),
            # likely this should be a soft link after all?
            # or we provide and override. Soft link for simplicity.
        )
    ),
    register_rawdata = dict(
        inputs=dict(),
        outputs=dict(
            folder_d=dict(type="raw_data", path="tmp/raw_data/{rule_id}.d"),
            analysis_tdf=dict(type="sqlite", path="tmp/raw_data/{rule_id}.d/analysis.tdf"),
            analysis_tdf_bin=dict(type="tdf_bin", path="tmp/raw_data/{rule_id}.d/analysis.tdf_bin"),
        )
    ),
    get_tims_precursor_clustering_config=dict(
        inputs=dict(),
        outputs=dict(
            tims_precursor_clustering_config=dict(
                type="tims_precursor_clustering_config",
                path="tmp/configs/tims_precursor_clustering_config/{rule_id}.config",
            ),
        ),
    ),
    get_tims_fragment_clustering_config=dict(
        inputs=dict(),
        outputs=dict(
            tims_fragment_clustering_config=dict(
                type="tims_fragment_clustering_config",
                path="tmp/configs/tims_fragment_clustering_config/{rule_id}.config",
            )
        ),
    ),
    get_precursor_cluster_stats_config=dict(
        inputs=dict(),
        outputs=dict(
            type="precursor_cluster_stats_config",
            path="tmp/configs/precursor_cluster_stats_config/{rule_id}.toml",
        ),
    ),
    get_fragment_cluster_stats_config=dict(
        inputs=dict(),
        outputs=dict(
            type="fragment_cluster_stats_config",
            path="tmp/configs/fragment_cluster_stats_config/{rule_id}.toml",
        ),
    ),
    get_matching_config=dict(
        inputs=dict(),
        outputs=dict(
            matching_config=dict(
                type="matching_config",
                path="tmp/configs/matching_config/{rule_id}.toml",
            )
        ),
    ),
    remove_raw_data_baseline = dict(
        inputs=dict(
            raw_data="folder_d",
            config="baseline_removal_config",
        ),
        outputs=dict(
            folder_d = dict(
                type = "raw_data",
                path = "tmp/spectra/no_baseline/{rule_id}.d",
            ),
            analysis_tdf = dict(
                type = "analysis_tdf",
                path="tmp/spectra/no_baseline/{rule_id}.d/analysis.tdf",
            ),
            analysis_tdf_bin = dict(
                type = "analysis_tdf_bin",
                path = "tmp/spectra/no_baseline/{rule_id}.d/analysis.tdf_bin",
            ),
        ),
    ),
    hash256 = dict(
        inputs=dict(
            path="type_not_important", # gets neglected: set in Rule._type_ignore
        ),
        outputs=dict(
            hashfile = dict(
                type = "sha256",
                path = "tmp/hashes/{rule.id}.sha256",
            ),
        ),
    ),
    report_if_dataset_and_calibration_comply = dict(
        inputs = dict(
            dataset = "raw_data",
            calibration = "raw_data",
        ),
        outputs = dict(
            dataset_matches_calibration_assertion = dict(
                type = "dataset_matches_calibration_assertion",
                path = "tmp/assertions/dataset_matches_calibration/{rule.id}.d"
            )
        ),
    ),
    get_tims_executable = dict(
        inputs = dict(),
        outputs = dict(
            tims_executable=dict(
                type="tims_executable",
                path="tmp/executables/{rule_id}",
            )
        ),
    ),
)

with open("configs/rules/default.toml", "w") as f:
    toml.dump(rule_config, f)


rules = Rules.from_config(rule_config)


paths = DotDict()
rules.register_fasta(fasta=fasta)


rules.get_matching_config


rules.remove_raw_data_baseline_parametrization
rules.remove_raw_data_baseline_parametrization.type


add_rule_and_paths_to_DB(
    **config_kwargs    
)

subconfigs["precursor_clustering_config"]



paths = fill_DB_with_paths(subconfigs=subconfigs, dataset=dataset, calibration=calibration, fasta=fasta,)

path_ids = {k: node.id for k, node in paths.items() if node != None}
wishes = {wish: path_ids[wish] for wish in CONFIG["wishlist"]} 

with db_session:
    rule = RuleOrConfig.GETINSERT(
        meta=dict(
            inputs=wishes,
            path_ids=path_ids,
            kwargs=dict(dataset=dataset, calibration=calibration, fasta=fasta, config=CONFIG, pipeline=pipeline,)
        ),
        type=f"populating_DB",
    )
    path = Path.GETINSERT(
        path=f"tmp/populating_DB/{rule.id}.toml",
        type=f"populating_DB",
        rule_or_config=rule,
    )



mapping_path = pathlib.Path(f"tmp/pipelines/{path.id}.toml")
mapping_path.parent.mkdir(exist_ok=True, parents=True)



with open(mapping_path, "w") as f:
    toml.dump(wishes, f)
# later on, some other programme can pass on the path_id.




paths["fasta"].path

paths["dataset"].parent_paths()
paths["dataset_analysis_tdf_hash"].parent_paths()
paths["dataset_analysis_tdf_hash"].path

paths["dataset"].path

# would be nice to put some meta info during the run into the DB. 
# like runtime.

# how to pass in calibration=None?
# how to pass in a fasta?

# subconfig_name, subconfig = next(iter(config["subconfigs"].items()))


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
