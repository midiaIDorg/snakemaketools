#!/usr/bin/env python3

import argparse
import pathlib
import typing
from warnings import warn

import pandas as pd
from pandas_ops.io import read_df, save_df
from snakemaketools.io_ops import expand_path, parse_path

parser = argparse.ArgumentParser(
    description="Combine statistics from a collection of bash extendable paths."
)
parser.add_argument(
    "expandable_bash_paths",
    help="Paths that could be expanded by bash lang into a set of path.",
    nargs="+",
    type=str,
)
parser.add_argument(
    "--output",
    type=str,
    help="Path to the output. If ommited, redirects to STD_OUT.",
    default=None,
)
parser.add_argument(
    "--strict_on_path_existance",
    help="Raise OSError if a given file does not exist.",
    action="store_true",
)
args = parser.parse_args()


def iter_dfs(
    *paths: str,
    _warn_if_missing: bool = True,
) -> typing.Iterable[pd.DataFrame]:
    """
    Iterate over tables specified in the sequence of passed in paths.

    Arguments:
        *paths (str): A variadic number of string path descriptors.
        _warn_if_missing (bool): Only raise a warning if a path does not exist in the file system. Otherwise, raise ValueError.

    Yields:
        pd.DataFrame: A dataframe with parsed in description.

    Raises:
        OSError: Path does not exist.
    """
    for path in paths:
        for expanded_path in expand_path(path):
            expanded_path = pathlib.Path(expanded_path)
            if expanded_path.exists():
                data = read_df(expanded_path)
                description = pd.DataFrame([parse_path(str(expanded_path))] * len(data))
                yield pd.concat([description, data], axis=1)

            else:
                msg = f"File `{expand_path}` does not exist!"
                if _warn_if_missing:
                    warn(msg)
                else:
                    raise OSError(msg)


if __name__ == "__main__":
    all_stats = pd.concat(
        iter_dfs(
            *args.expandable_bash_paths,
            _warn_if_missing=not args.strict_on_path_existance,
        ),
        ignore_index=True,
    )
    if args.output is None:
        print(all_stats.to_csv(index=False))
    else:
        save_df(all_stats, args.output)

# # path = "out/base/{default,_old}/dataset=G8602/calibration=G8605/matches_config=_mz8/fragment_clusters_postprocessing=simple/fragment_clusters_postprocessing_config=default/edge_refinement_config=_ms2_norm_score_geq_{40,50,60,q10} out/base/{default,_old}/dataset=G8602/calibration=G8605/matches_config=_mz8/fragment_clusters_postprocessing=simple/fragment_clusters_postprocessing_config=default/edge_refinement_config=_maxRankLeq{6,8,10,12}"
# path = "out/base/_old/fragment_stats_config={default,no_normalization,ramintense}/sage/stats.csv"
# path = "out/base/_old/fragment_stats_config={default,no_normalization,ramintense}/sage/edge_node_counts_summary.csv"
