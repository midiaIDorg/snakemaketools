# TODO: add names to rule.nodes (perhaps, any nodes?). This will make it simpler to refer to.

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
from pandas_ops.io import read_df, save_df
from pandas_ops.lex_ops import LexicographicIndex
from pandas_ops.stats import weighted_mean_and_var
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import setup_db
from snakemaketools.debug_tools import (copy_path, replace_filesystem_entry,
                                        restore_backup)
from snakemaketools.import_ops import dynamically_import_foo
from snakemaketools.longsnake import LongSnakeConfiguration
from kilograms import scatterplot_matrix

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
old_pipeline_folder = "/home/matteo/Projects/midia/midia_experiments/pipelines/dockerhubregression"


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

list(nodes)

%sx snakemake -call {nodes.edge_refinement_config.location}
with open(nodes.edge_refinement_config.location, "rb") as f:
    conf = tomllib.load(f)

old_pipeline_folder = Path(old_pipeline_folder)
with open(old_pipeline_folder/"partial/paths.json") as f:
    old_pipeline_partials = DotDict(json.load(f))
for name, path in old_pipeline_partials.items():
    old_pipeline_partials[name] = old_pipeline_folder / path


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

%sx snakemake {nodes.fragment_clusters_hdf.location} {nodes.precursor_clusters_hdf.location}

# replacing clusters things
%sx mv {nodes.fragment_clusters_hdf.location} {nodes.fragment_clusters_hdf.location}.bkp
%sx cp {old_pipeline_partials.MS2_clusters_hdf} {nodes.fragment_clusters_hdf.location}

%sx mv {nodes.precursor_clusters_hdf.location} {nodes.precursor_clusters_hdf.location}.bkp
%sx cp {old_pipeline_partials.MS1_clusters_hdf} {nodes.precursor_clusters_hdf.location}


# add methods like prev and next:
assert old_pipeline_partials.MS2_clusters_hdf.exists()
assert old_pipeline_partials.MS2_cluster_stats.exists()

old_frag_stats = read_df(old_pipeline_partials.MS2_cluster_stats)


%sx snakemake {nodes.fragment_cluster_stats.parents['combine_cluster_stats'].table_0.location} {nodes.precursor_cluster_stats.location}
%sx snakemake {nodes.fragment_cluster_stats.location}


new_frag_stats = read_df(nodes.fragment_cluster_stats.location)
commonCols, *_ = VennIt(old_frag_stats.columns, new_frag_stats.columns)
abs(old_frag_stats[commonCols] - new_frag_stats[commonCols]).max()

dict(zip(['step_wmean', 'step_wvar', 'step_min', 'step_max'], np.abs(old_frag_stats[['step_wmean', 'step_wvar', 'step_min', 'step_max']].to_numpy() - new_frag_stats[['midia_step_wmean', 'midia_step_wvar', 'midia_step_min', 'midia_step_max']].to_numpy()).max(axis=0)))

deciles(old_frag_stats.precursor_mz_pred_fastmist - new_frag_stats.predicted_precursor_mz)
deciles(old_frag_stats.precursor_mz_pred_fastmist - new_frag_stats.isolationmz_wmean)
deciles(old_frag_stats.isolationmz_wmean - new_frag_stats.isolationmz_wmean)


# quadrupole_positions = dia_common.quadrupole.get_quadrupole_positions(
#     analysis_tdf=nodes.dataset_analysis_tdf.location,
#     calibration_results=(lambda x: None if x == "none" else x)(nodes.calibration_results.location)
# )

# clusters = IndexedReader(nodes.fragment_clusters.location, "ClusterID")
# npp = dia_common.precursor_prediction.PrecursorPredictor(
#     clusters=clusters,
#     quadrupole_positions=quadrupole_positions,
#     midia_steps=get_midia_steps(nodes.dataset_analysis_tdf.location),
#     # transmission_aggregator=intensity_weighted_transmission_aggregator,
#     # top_predictor=trivial_top_predictor,
#     # transmission_profile_predictor=predict_cluster_precursor_profile,
#     # **config["precursor_mz_predictors_kwargs"],
#     normalization = "to_max",
#     # normalization = "probabilistic",
#     rounding_digits = 1
# )
# new_predictions = npp.predict_precursors_mzs()

# deciles(old_frag_stats.precursor_mz_pred_fastmist - new_predictions.flatten())

# exchanging the new predictions for old ones:
new_frag_stats["predicted_precursor_mz_bkp"] = new_frag_stats.predicted_precursor_mz
new_frag_stats["predicted_precursor_mz"] = old_frag_stats.precursor_mz_pred_fastmist

save_df(new_frag_stats, nodes.fragment_cluster_stats.location)
# NEED TO MAKE THE PIPELINE SLIGHTLY BETTER TO AVOID READING IN THOSE UNNECESSARY TABLES.

%sx snakemake {nodes.rough_matches.location}

# # expected difference
# read_df(old_pipeline_partials.rough_matches)
# read_df(nodes.rough_matches.location)

# %sx snakemake {nodes.rough_mgf.location}

# from collections import Counter

# from tqdm import tqdm


# def iter_spectra(
#     codelines,
#     _start_tag: str = "BEGIN IONS",
#     _stop_tag: str = "END IONS",
# ) -> list[dict]:
#     recording = False
#     for line in codelines:
#         line = line.strip()
#         # Detect sections based on the keywords
#         if line.startswith(_start_tag):
#             recording = True
#             buffer: list[str] = []
#         elif line.startswith(_stop_tag):
#             assert recording
#             recording = False
#             yield buffer
#         elif recording:
#             buffer.append(line)
#         else:
#             pass
#     assert not recording


# def parse_line_spectrum(line_spectrum):
#     header = line_spectrum[:4]
#     peaks = []
#     for l in line_spectrum[4:]:
#         mz, intensity = l.split(" ")
#         peaks.append((float(mz), int(intensity)))
#     return header, peaks


# def parse_mgf(mgf_path, sort_peaks=False):
#     MS1_ClusterIDs = []
#     peak_cnts = []
#     peak_list = []
#     with open(mgf_path, "r") as file:
#         for line_spectrum in tqdm(iter_spectra(file)):
#             header, peaks = parse_line_spectrum(line_spectrum)
#             MS1_ClusterID = int(header[0].split(".", 2)[1])
#             MS1_ClusterIDs.append(MS1_ClusterID)
#             if sort_peaks:
#                 peaks.sort()
#             peak_cnt = len(peaks)
#             peak_cnts.append(peak_cnt)
#             peak_list.append(peaks)
#     return np.array(MS1_ClusterIDs), np.array(peak_cnts), peak_list

# parsed_mgf = parse_mgf(nodes.rough_mgf.location, sort_peaks=True)
# parsed_mgf_old = parse_mgf(old_pipeline_partials.rough_matches_sage_mgf, sort_peaks=True)
# old_MS1_ClusterIDs, old_peak_cnts, old_peak_list = parsed_mgf_old
# new_MS1_ClusterIDs, new_peak_cnts, new_peak_list = parsed_mgf

# np.all(new_MS1_ClusterIDs + 1 == old_MS1_ClusterIDs)

# np.all(old_peak_cnts == new_peak_cnts)

# len(new_peak_cnts)
# np.sum(old_peak_cnts != new_peak_cnts)

# fishy = old_peak_cnts != new_peak_cnts
# old_peak_cnts[old_peak_cnts != new_peak_cnts] - new_peak_cnts[old_peak_cnts != new_peak_cnts]

# fishy_idxs = np.nonzero(fishy)[0]


# # fishy_idx = fishy_idxs[0]
# fishy_idx = int(fishy_idxs[old_peak_cnts[fishy_idxs] - new_peak_cnts[fishy_idxs] == 32])

# old_mzs, old_intensities = map(np.array, zip(*old_peak_list[fishy_idx]))
# new_mzs, new_intensities = map(np.array, zip(*new_peak_list[fishy_idx]))

# new_rough_matches = read_df(nodes.rough_matches.location)
# old_rough_matches = read_df(old_pipeline_partials.rough_matches)
# fishy_new_MS1_ClusterID = new_MS1_ClusterIDs[fishy_idx]
# fishy_old_MS1_ClusterID = old_MS1_ClusterIDs[fishy_idx]

# spec_mask = (new_rough_matches.MS1_ClusterID.to_numpy() == fishy_new_MS1_ClusterID)
# rough = new_rough_matches.iloc[spec_mask]

# diffs_per_spectrum = pd.DataFrame({
#     "delta_mz": new_frag_stats.iloc[rough.MS2_ClusterID].predicted_precursor_mz.to_numpy() - new_prec_stats.iloc[[fishy_new_MS1_ClusterID]].mz_wmean.to_numpy(),
#     "delta_scan": new_frag_stats.iloc[rough.MS2_ClusterID].scan_wmean.to_numpy() - new_prec_stats.iloc[[fishy_new_MS1_ClusterID]].scan_wmean.to_numpy(),
#     "delta_frame": new_frag_stats.iloc[rough.MS2_ClusterID].frame_wmean.to_numpy() - new_prec_stats.iloc[[fishy_new_MS1_ClusterID]].frame_wmean.to_numpy(),
# })



# scatterplot_matrix(diffs_per_spectrum)


# set(old_mzs.round(K)) - set(new_mzs.round(K))
# set(new_mzs.round(K)) - set(old_mzs.round(K))

# diffs = set(map(int, set(old_intensities) - set(new_intensities)))

# rough_old = pd.merge(old_rough_matches[old_rough_matches.MS1_ClusterID == fishy_old_MS1_ClusterID], old_frag_stats, left_on="MS2_ClusterID", right_on="ClusterID")
# fishy_events = rough_old.loc[rough_old.intensity.isin(set(old_intensities) - set(new_intensities))]

# plt.hist(rough_old.precursor_mz_pred_fastmist, bins="auto")
# plt.show()

# fishy_events[["scan_wmean","frame_wmean","precursor_mz_pred_fastmist"]] - old_prec_stats.loc[ old_prec_stats.ClusterID == int(fishy_old_MS1_ClusterID), ["scan_wmean", "frame_wmean", "mz_wmean"] ].to_numpy()[0]
# find out those clusters


# old_clusters = read_df(old_pipeline_partials.MS2_clusters_startrek)

# choose = old_clusters.ClusterID.isin(fishy_events.MS2_ClusterID.to_numpy())

# old_clusters.loc[choose]

# rough_old.loc[rough_old.mz_wmean.round(2) == 427.33]
# old_prec_stats.query("ClusterID == 13474")
# old_frag_stats.query("ClusterID == 629560")


# list(old_pipeline_partials)

# old_rough_matches = read_df(old_pipeline_partials.rough_matches)
old_mapped_back_first_gen_search_edges = read_df(old_pipeline_partials.mapped_back_first_gen_search_edges)
old_mapped_back_first_gen_search_edges.MS1_ClusterID -= 1
old_mapped_back_first_gen_search_edges.MS2_ClusterID -= 1

%sx snakemake {nodes.first_gen_fdr_filtered_edges.location}
new_mapped_back_first_gen_search_edges = read_df(nodes.first_gen_fdr_filtered_edges.location)


old_edges = set(zip(old_mapped_back_first_gen_search_edges.MS1_ClusterID, old_mapped_back_first_gen_search_edges.MS2_ClusterID))
new_edges = set(zip(new_mapped_back_first_gen_search_edges.MS1_ClusterID, new_mapped_back_first_gen_search_edges.MS2_ClusterID))
len(old_edges & new_edges)
len(old_edges - new_edges)
len(new_edges - old_edges)

diff_edges = old_edges - new_edges
diff_edges = new_edges - old_edges
diff_edges = new_edges & old_edges


MS1_ClusterIDs, MS2_ClusterIDs = map(np.array, zip(*diff_edges))

MS1_cols = ["scan_wmean","frame_wmean","mz_wmean"]
MS2_cols = ["scan_wmean","frame_wmean","precursor_mz_pred_fastmist"]

old_prec_stats = read_df(old_pipeline_partials.MS1_cluster_stats)
diffs = old_prec_stats.iloc[MS1_ClusterIDs][MS1_cols].to_numpy() - old_frag_stats.iloc[MS2_ClusterIDs][MS2_cols].to_numpy()
diffs = pd.DataFrame(diffs, columns=list(map(lambda x: x.replace("_wmean","_diff"), MS1_cols)))

scatterplot_matrix(diffs)

old_frag_stats
new_frag_stats

%sx snakemake {nodes.edge_refinement_config.location}
with open(nodes.edge_refinement_config.location, "rb") as f:
    conf = tomllib.load(f)


%sx snakemake {nodes.refined_matches.location}



precursor_stats = "tmp/refinement/nodes/91/refined_precursor_stats.parquet"
fragment_stats = "tmp/refinement/nodes/91/refined_fragment_stats.parquet"
all_edges = "tmp/edges/rough/64/rough_edges.startrek"
filtered_edges = "tmp/search/sage/mapping_back_edges/84/filtered_matches.startrek"
hard_filtered_edges = "tmp/search/sage/mapping_back_edges/84/filtered_matches.startrek"
config = "tmp/configs/edge_refinement_config/192.toml"
verbose = True


new_refined_matches = read_df(nodes.refined_matches.location)
old_refined_matches = read_df(old_pipeline_partials.refined_edges)


# so there are differences and so what?
old_edges = set(zip(old_refined_matches.MS1_ClusterID-1, old_refined_matches.MS2_ClusterID-1))
new_edges = set(zip(new_refined_matches.MS1_ClusterID, new_refined_matches.MS2_ClusterID))
len(old_edges & new_edges)
len(old_edges - new_edges)
len(new_edges - old_edges)

diff_edges = old_edges - new_edges
diff_edges = new_edges - old_edges
diff_edges = new_edges & old_edges
