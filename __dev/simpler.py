%load_ext autoreload
%autoreload 2
import json
import shutil
import subprocess
import timeit
from functools import partial
from pathlib import Path
from statistics import median
from subprocess import run

import toml
from numba_progress import ProgressBar

import dia_common
import dia_common.precursor_prediction
import numba
import numpy as np
import numpy.typing as npt
import pandas as pd
import tomllib
from midia_schemes.main import get_midia_steps
from mmapped_df import IndexedReader
from pandas_ops.io import read_df
from pandas_ops.lex_ops import LexicographicIndex
from pandas_ops.stats import weighted_mean_and_var
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import setup_db
from snakemaketools.debug_tools import (copy_path, replace_filesystem_entry,
                                        restore_backup)
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration

pd.set_option('display.max_columns', None)

def VennIt(A, B):
    sA, sB = map(set, (A, B) )
    return list(map(list, (sA & sB, sA - sB, sB - sA)))

def deciles(xx):
    return xx.quantile(np.linspace(0,1,11))

RUN = partial(run, shell=True, check=True)

def exists(path: str):
    return Path(path).exists()




consolidated_config_path = "configs/consolidated/debug.toml"
get_nodes_path = "midia_pipe_hull.pipelines.base::get_nodes"
diff = "G8027/None"
# diff = "G8602/None"



setup_db(verbose=True)

with open(consolidated_config_path, "r") as f:
    consolidated_config = DotDict.Recursive(toml.load(f))

longsnake = LongSnakeConfiguration(
    consolidated_config=consolidated_config,
    get_nodes=dynamically_import_foo(get_nodes_path),
    smk_file_paths=Path("workflow").glob("**/*.smk"),
)
longsnake.update_consolidated_config(diff)

rules = longsnake.rules
configs = longsnake.configs
wildcards = longsnake.wildcards
nodes = longsnake.nodes


# perhaps most sense to update the DB ot a new path?
# soft link it?
# simpler not to do it.

# node = nodes.precursor_clusters_hdf
# replacement = Path("/home/matteo/Projects/midia/docker_images/midia_docker/dockerhub/outputs/debug/G8027/None/clusters/MS1.hdf")

# replace_filesystem_entry(node, replacement)


# we export paths to other files!!!
# read_df(nodes.first_gen_search_precursors.location)

old_pipeline_folder = Path("/home/matteo/Projects/midia/midia_experiments/pipelines/dockerhubregression")
with open(old_pipeline_folder/"partial/paths.json") as f:
    old_pipeline_partials = DotDict(json.load(f))

for name, path in old_pipeline_partials.items():
    old_pipeline_partials[name] = old_pipeline_folder / path
    if "{" in path:
        print(name, path)
    else:
        if not old_pipeline_partials[name].exists():
            print(f"Missing {name} at \n{old_pipeline_partials[name]}")


RUN(f"snakemake {nodes.precursor_clusters_hdf.location}")
exists(nodes.precursor_clusters_hdf.location)

replace_filesystem_entry(nodes.precursor_clusters_hdf, old_pipeline_partials.MS1_clusters_hdf)
RUN(f"snakemake {nodes.precursor_cluster_stats.location}")

## debugging diffs in cluster stats
old_pipeline_partials.MS1_clusters_hdf.exists()
old_pipeline_partials.MS1_cluster_stats.exists()
old_prec_stats = read_df(old_pipeline_partials.MS1_cluster_stats)
new_prec_stats = read_df(nodes.precursor_cluster_stats.location)
commonCols, *_ = VennIt(old_prec_stats.columns, new_prec_stats.columns)
abs(old_prec_stats[commonCols] - new_prec_stats[commonCols]).max()

deciles(old_prec_stats.tof_wmean - new_prec_stats.tof_wmean)
# Problem solved.

RUN(f"snakemake {nodes.fragment_clusters_hdf.location}")
replace_filesystem_entry(nodes.fragment_clusters_hdf, old_pipeline_partials.MS2_clusters_hdf)
RUN(f"snakemake {nodes.fragment_cluster_stats.location}")

# add methods like prev and next:

old_pipeline_partials.MS2_clusters_hdf.exists()
old_pipeline_partials.MS2_cluster_stats.exists()

old_frag_stats = read_df(old_pipeline_partials.MS2_cluster_stats)

new_frag_stats = read_df(nodes.fragment_cluster_stats.location)
commonCols, *_ = VennIt(old_frag_stats.columns, new_frag_stats.columns)
abs(old_frag_stats[commonCols] - new_frag_stats[commonCols]).max()

dict(zip(['step_wmean', 'step_wvar', 'step_min', 'step_max'], np.abs(old_frag_stats[['step_wmean', 'step_wvar', 'step_min', 'step_max']].to_numpy() - new_frag_stats[['midia_step_wmean', 'midia_step_wvar', 'midia_step_min', 'midia_step_max']].to_numpy()).max(axis=0)))

deciles(old_frag_stats.precursor_mz_pred_fastmist - new_frag_stats.predicted_precursor_mz)

#####BAL


# fragment_cluster_stats = "tmp/clusters/tims/reformated/50/cluster_stats.parquet"
# fragment_clusters = "tmp/clusters/tims/reformated/45/clusters.startrek"
# calibration_results = None
# analysis_tdf = "spectra/G8027.d/analysis.tdf"
# config_path = "tmp/configs/precursor_prediction_config/52.toml"
# out_stats = "tmp/clusters/tims/reformated/54/predicted_precursors.parquet"
# verbose = True

deciles(old_frag_stats.precursor_mz_pred_fastmist - new_frag_stats.isolationmz_wmean)
deciles(old_frag_stats.isolationmz_wmean - new_frag_stats.isolationmz_wmean)


calibration_results = nodes.calibration_results.location
quadrupole_positions = dia_common.quadrupole.get_quadrupole_positions(
    analysis_tdf=nodes.dataset_analysis_tdf.location,
    calibration_results=calibration_results
    if calibration_results != "none"
    else None,
)

with open(nodes.precursor_prediction_config.location, "rb") as config_file_handler:
    config = tomllib.load(config_file_handler)

# fragment_clusters_df = read_df()
# clusters = IndexedReader(nodes.fragment_clusters.location, "ClusterID")

# clusters_df = read_df("/tmp/frag_clust.startrek", read_write=True)
# clusters_df.scan = clusters_df.scan - 1
# clusters_df.append_column(new_scan, clusters_df.scan - 1)

# clusters_df.scan.min()
# clusters_df.midia_step = clusters_df.midia_step - 1
# del clusters_df

# clusters = IndexedReader("/tmp/frag_clust.startrek", "ClusterID")
# clusters.dataset["scan"] = clusters.dataset["original_scan"]-1
# clusters_df = pd.DataFrame(clusters.dataset, copy=False)
# clusters_df


analysis_tdf = nodes.dataset_analysis_tdf.location
npp = dia_common.precursor_prediction.PrecursorPredictor(
    clusters=clusters,
    quadrupole_positions=quadrupole_positions,
    midia_steps=get_midia_steps(analysis_tdf),
    # transmission_aggregator=intensity_weighted_transmission_aggregator,
    # top_predictor=trivial_top_predictor,
    # transmission_profile_predictor=predict_cluster_precursor_profile,
    # **config["precursor_mz_predictors_kwargs"],
    normalization = "none",
    # normalization = "probabilistic",
    rounding_digits = 1
)
new_predictions = npp.predict_precursors_mzs()


deciles(old_frag_stats.precursor_mz_pred_fastmist - new_predictions.flatten())

clusters_df.iloc[[0]]

npp.quadrupole_positions.get_transmission_curve(8, 579)





# OK, the scans have been updated or what???
# but why the window groups work????

self.mz_grid[
    start : start + self.tensor_mzbins_cnt
]  # border effect
assert len(local_grid) == self.tensor_mzbins_cnt
self.transmissions[
    midia_step, scan, :
] = self.quadrupole_positions.get_transmission_curve(
    midia_step, scan
).value(
    local_grid
)

# TODO: all those pshells should be moved out of pipeline and into snakemaketools
# load partial/paths.json and turn int SimpleNamespace as old_pipeline_partials

args = SimpleNamespace()
args.MS2_clusters = old_pipeline_partials.MS2_clusters_hdf
args.calibration_hdf = old_pipeline_partials.calibration
args.folder_d = old_pipeline_partials.dataset
args.config = old_pipeline_partials.MS2_cluster_stats_config
args.MS2_clusters_startrek = old_pipeline_partials.MS2_clusters_startrek
args.precursor_prediction_algorithm = "fast"
args.verbose = True

# pshell(f"get_MS2_stats {input.MS2_clusters} {input.calibration} {input.dataset} {input.config} {output} --MS2_clusters_startrek {input.MS2_clusters_startrek} --precursor_prediction_algorithm {wildcards.cluster_stats_2} --verbose")

# REDOING PREDICTIONS




with ProgressBar(
    desc='Building Cluster Index',
    total=len(fragment_clusters_df.ClusterID)
) as progress_proxy:
    lexIdx = LexicographicIndex(
        fragment_clusters_df.ClusterID.to_numpy(),
        progress_proxy=progress_proxy
    )

@numba.njit
def first(frames, scans, tofs, intensities, *args):
    res = np.zeros(shape=4, dtype=float)
    res[0] = frames[0]
    res[1] = scans[0]
    res[2] = tofs[0]
    res[3] = intensities[0]
    return res

@numba.njit
def first(frames, scans, tofs, intensities, *args):
    return frames[0], scans[0], tofs[0], intensities[0]


lexIdx.map(first, fragment_clusters_df.frame, fragment_clusters_df.scan, fragment_clusters_df.tof, fragment_clusters_df.intensity)

def 

fragment_clusters_df.iloc[:20]
