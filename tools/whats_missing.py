#!/usr/bin/env python3

import argparse
import pathlib

from snakemaketools.io_ops import expand_path

parser = argparse.ArgumentParser(
    description="Find out which folders / files are missing among submitted bash expandable paths and print to STD_OUT."
)
parser.add_argument(
    "expandable_bash_paths",
    help="Paths that could be expanded by bash lang into a set of path.",
    nargs="+",
    type=str,
)
args = parser.parse_args()


if __name__ == "__main__":
    expandable_bash_paths = args.expandable_bash_paths
    for expandable_bash_path in expandable_bash_paths:
        for expanded_path in expand_path(expandable_bash_path):
            expanded_path = pathlib.Path(expanded_path)
            if not expanded_path.exists():
                print(expanded_path)


# expandable_bash_paths = [
#     "out/base/{_old/first_gen_search_engine_config=p12f15_old/second_gen_search_engine_config=p12f15_old,default/first_gen_search_engine_config=p12f15/second_gen_search_engine_config=p12f15}/{dataset=O11557,dataset=O11558}/calibration=none/first_gen_fasta=HYE_2024_02_16_6066entries_contaminant_tenzer/second_gen_fasta=HYE_2024_02_16_6066entries_contaminant_tenzer/edge_refinement_config={_maxRankLeq6,_maxRankLeq12,_ms2_norm_score_geq_q10}/sage/edge_node_counts_summary.csv",
#     "out/base/{_old/first_gen_search_engine_config=p12f15_old/second_gen_search_engine_config=p12f15_old,default/first_gen_search_engine_config=p12f15/second_gen_search_engine_config=p12f15}/{dataset=G10271,dataset=B6230,dataset=B6699}/calibration=none/first_gen_fasta=Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer/second_gen_fasta=Human_2024_02_16_UniProt_Taxon9606_Reviewed_20434entries_contaminant_tenzer/edge_refinement_config={_maxRankLeq6,_maxRankLeq12,_ms2_norm_score_geq_q10}/sage/edge_node_counts_summary.csv",
#     "out/base/{_old/first_gen_search_engine_config=phospho_old/second_gen_search_engine_config=phospho_old,default/first_gen_search_engine_config=phospho/second_gen_search_engine_config=phospho}/dataset=O12981/calibration=none/first_gen_fasta=Mouse_2024_02_16_UniProt_Taxon10090_Reviewed_17208entries_contaminant_tenzer/second_gen_fasta=Mouse_2024_02_16_UniProt_Taxon10090_Reviewed_17208entries_contaminant_tenzer/edge_refinement_config={_maxRankLeq6,_maxRankLeq12,_ms2_norm_score_geq_q10}/sage/edge_node_counts_summary.csv",
#     "out/base/{_old/first_gen_search_engine_config=p12f15_old/second_gen_search_engine_config=p12f15_old,default/first_gen_search_engine_config=p12f15/second_gen_search_engine_config=p12f15}/dataset=B6613/calibration=none/first_gen_fasta=Yeast_2024_02_16_UniProt_Taxon643680_5984entries_contaminant_tenzer/second_gen_fasta=Yeast_2024_02_16_UniProt_Taxon643680_5984entries_contaminant_tenzer/edge_refinement_config={_maxRankLeq6,_maxRankLeq12,_ms2_norm_score_geq_q10}/sage/edge_node_counts_summary.csv",
# ]
