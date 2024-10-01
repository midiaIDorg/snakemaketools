%load_ext autoreload
%autoreload 2
from __future__ import annotations

import dataclasses
import pathlib
import typing
from abc import ABC, abstractmethod
from functools import partial
from pprint import pprint
from types import SimpleNamespace
from typing import Callable, Protocol

import toml
from pony.orm import (Database, Optional, PrimaryKey, Required, Set, commit,
                      composite_index, db_session, set_sql_debug)

# from midia_pipe_hull.pipelines.base import fill_DB_with_paths
from snakemaketools.datastructures import DotDict
from snakemaketools.models2 import db
from snakemaketools.rules import Path, Root, Rule

# from snakemaketools.rules import Path, PathStorage, Root, Rule




set_sql_debug()
db.bind(provider='sqlite', filename=':memory:', create_db=True)
# db.bind(provider='sqlite', filename='/home/matteo/Projects/midia/pipelines/devel/midia_pipe/base.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


db_path_storage = DBPathStorage()



# seems we do not need distinction between Rule and RuleType.


dataset = "G8027"
calibration = "G8045"
fasta = "Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer"
config = "default"
pipeline = "base"

with open(f"configs/consolidated/{config}.toml", "r") as f:
    CONFIG = toml.load(f)
    # pprint(config)
subconfigs = CONFIG["subconfigs"]

subconfigs["tims_precursor_clustering_config"]["config"]


register_raw_data = dict(
    expected_outputs=dict(
        folder_d=dict(type="raw_data", path="spectra/{}.d"),
        analysis_tdf=dict(type="sqlite", path="spectra/{}.d/analysis.tdf"),
        analysis_tdf_bin=dict(type="tdf_bin", path="spectra/{}.d/analysis.tdf_bin"),
    )
)
# turn that into a function? without reusing Rule?

def register_raw_data(dataset: str) -> tuple[Path,Path,Path]:
    folder_d = Path(data_type="raw_data", location=f"spectra/{dataset}.d")
    analysis_tdf = Path(data_type="analysis_tdf", location=f"spectra/{dataset}/analysis.tdf")
    analysis_tdf_bin = Path(data_type="analysis_tdf_bin", location=f"spectra/{dataset}/analysis.tdf_bin")
    return folder_d, analysis_tdf, analysis_tdf_bin

def register_fasta(fasta: str) -> Path:
    fasta = Path(data_type="fasta", location=f"fastas/{fasta}.fasta")
    return fasta

# the same for every other config

roots_config = dict(
    register_raw_data = dict(
        expected_outputs=dict(
            folder_d=dict(type="raw_data", path="spectra/{}.d"),
            analysis_tdf=dict(type="sqlite", path="spectra/{}.d/analysis.tdf"),
            analysis_tdf_bin=dict(type="tdf_bin", path="spectra/{}.d/analysis.tdf_bin"),
        )
    ),
    register_fasta = dict(
        expected_outputs=dict(
            fasta=dict(type="fasta", path="fastas/{}.fasta"),
        )
    ),
    get_tims_precursor_clustering_config=dict(
        expected_inputs=dict(),
        expected_outputs=dict(
            tims_precursor_clustering_config=dict(
                name="tims_precursor_clustering_config",
                path_template="tmp/configs/tims_precursor_clustering_config/{}.config",
            ),
        ),
    ),
    get_tims_fragment_clustering_config=dict(
        expected_inputs=dict(),
        expected_outputs=dict(
            tims_fragment_clustering_config=dict(
                name="tims_fragment_clustering_config",
                path_template="tmp/configs/tims_fragment_clustering_config/{}.config",
            )
        ),
    ),
    get_precursor_cluster_stats_config=dict(
        expected_inputs=dict(),
        expected_outputs=dict(
            precursor_cluster_stats_config=dict(
                name="precursor_cluster_stats_configl",
                path_template="tmp/configs/precursor_cluster_stats_config/{}.toml",
            )
        ),
    ),
    get_fragment_cluster_stats_config=dict(
        expected_inputs=dict(),
        expected_outputs=dict(
            name="fragment_cluster_stats_config",
            path_template="tmp/configs/fragment_cluster_stats_config/{}.toml",
        ),
    ),
    get_matching_config=dict(
        expected_inputs=dict(),
        expected_outputs=dict(
            matching_config=dict(
                name="matching_config",
                path_template="tmp/configs/matching_config/{}.toml",
            )
        ),
    ),

)


# this should be a PathStorage methode.
def get_config(meta) -> Path:



# also: roots won't be reused? of course they will: dataset + calibration
@dataclasses.dataclass
class RootsRule:
    rule_type: str
    expected_outputs: DotDict[str, str]
    path_storage: PathStorage

    def __call__(self, meta: dict) -> DotDict[str, Path]:
        return tuple(
            Path(data_type=data_type, location=)
            for _, data_type in self.expected_outputs
        )



# w sumie, to czemu potrzebuję tych klass , skoro to de-facto wrappery na PathStorage??? Czy tak istotnie jest?
# Tylko po to, żeby unikać wywołań zależnych od root_type i rule_type i mieć `funkcje`.
# Te checki z Rule.__call__ dać do PathStorega.output_paths? nie można: bo to nie powinno nic wiedzieć o inputach. Jak jest, jest OK.





# Question: how to pass in the version of the software? Tims must be specified alongside other configs? No, better: simply one of the inputs should contain the proper path. But when is it passed in? Likely in the pipeline function: this is where we have access to configs anyway.
# OK, so the pipeline should get the consolidated config and decide upon all of that. It anyway needs to read in the configs below that specify the rules too.
# so a pipeline will get 2 files.

# try to write some rules for the configs.

config = dict(
    path_types=dict(
        raw_data
    )
)


rule_config = dict(
    remove_raw_data_baseline = dict(
        expected_inputs=dict(
            raw_data="folder_d",
            config="baseline_removal_config",
        ),
        expected_outputs=dict(
            folder_d = dict(
                name = "raw_data",
                folder_d = "tmp/spectra/no_baseline/{rule_id}.d",
            ),
            analysis_tdf = dict(
                name = "sqlite",
                path_template="tmp/spectra/no_baseline/{rule_id}.d/analysis.tdf",
            ),
            analysis_tdf_bin = dict(
                name = "tdf_bin",
                path = "tmp/spectra/no_baseline/{rule_id}.d/analysis.tdf_bin",
            ),
        ),
    ),
    hash256 = dict(
        expected_inputs=dict(
            path_template="", # empty = no specific type
        ),
        expected_outputs=dict(
            hashfile = dict(
                name = "sha256",
                path = "tmp/hashes/{rule.id}.sha256",
            ),
        ),
    ),
    report_if_dataset_and_calibration_comply = dict(
        expected_inputs = dict(
            dataset = "raw_data",
            calibration = "raw_data",
        ),
        expected_outputs = dict(
            dataset_matches_calibration_assertion = dict(
                name = "dataset_matches_calibration_assertion",
                path = "tmp/assertions/dataset_matches_calibration/{rule.id}.d"
            )
        ),
    ),
    get_tims_executable = dict(
        expected_inputs = dict(),
        expected_outputs = dict(
            tims_executable=dict(
                name="tims_executable",
                path_template="tmp/executables/{rule_id}",
            )
        ),
    ),
)



with open("configs/rules/default.toml", "w") as f:
    toml.dump(rule_config, f)

# r = Rule(outputs_maker=lambda x:x, rule_type="hash256", **rule_config["hash256"])
# r

# for rule_name, subconfig in config.items():

rules = parse_rules(rule_config, lambda x:x)


# def register_fasta(fasta: str) -> Path:
#     rule = RuleOrConfig.GETINSERT(
#         meta=dict(fasta=fasta, inputs={}),
#         type="register_fasta",
#     )
#     fasta = Path.GETINSERT(
#         path=f"fastas/{fasta}.fasta",
#         type="fasta",
#         rule_or_config=rule,
#     )
#     return fasta


# def register_tdf_rawdata(rawdata_tdf: str) -> tuple[Path, Path, Path]:
#     rule = RuleOrConfig.GETINSERT(
#         meta=dict(rawdata_tdf=rawdata_tdf, inputs={}),
#         type="register_tdf_rawdata",
#     )
#     folder_d = Path.GETINSERT(
#         path=f"spectra/{rawdata_tdf}.d",
#         type="raw_data",
#         rule_or_config=rule,
#     )
#     analysis_tdf = Path.GETINSERT(
#         path=f"spectra/{rawdata_tdf}.d/analysis.tdf",
#         type="analysis_tdf",
#         rule_or_config=rule,
#     )
#     analysis_tdf_bin = Path.GETINSERT(
#         path=f"spectra/{rawdata_tdf}/analysis.tdf_bin",
#         type="tdf_bin",
#         rule_or_config=rule,
#     )
#     return folder_d, analysis_tdf, analysis_tdf_bin

paths = DotDict()
paths.fasta = register_fasta(fasta=fasta_str)




fasta = register_fasta(fasta=fasta_str)
fasta.parent_paths()
fasta.path

(
    paths.dataset,
    paths.dataset_analysis_tdf,
    paths.dataset_analysis_tdf_bin,
) = rules.register_raw_data(raw_data=dataset_str)

paths.dataset_analysis_tdf_hash = hash256(paths.dataset_analysis_tdf)
paths.dataset_analysis_tdf_bin_hash = hash256(paths.dataset_analysis_tdf_bin)
paths.dataset_marginals_plots = raw_data_marginals_plots_folder(paths.dataset)

# OK, somewhere we need to use the path_templates





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
