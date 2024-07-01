#!/usr/bin/env python3

import argparse
import pathlib
import sys
import typing
from pathlib import Path
from warnings import warn

import pandas as pd
from pandas_ops.io import read_df, save_df
from snakemaketools.io_ops import expand_path, parse_path

args = dict(fixed_parametrization="F/S/T", paths=["test/{a,b}/{c,d,e}/haha/gua.csv"])

parser = argparse.ArgumentParser(
    description="Combine statistics from a fixed parametrization path. names specified in fixed_parametrization will appear as column names in the output csv."
)
parser.add_argument(
    "fixed_parametrization",
    help="A string of fixed number of folders where the results should be search for, e.g. a/b/c/d",
    type=str,
)
parser.add_argument(
    "paths",
    help="Paths that should be parsed.",
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
args = parser.parse_args().__dict__

# col_names = args["fixed_parametrization"].split("/")
# paths = args["paths"]


def iter_dfs(
    *paths: str,
    _warn_if_missing: bool = True,
) -> typing.Iterable[pd.DataFrame]:
    for path in paths:
        for expanded_path in expand_path(path):
            expanded_path = Path(expanded_path)
            if expanded_path.exists():
                data = pd.read_csv(expanded_path)
                description = pd.DataFrame(
                    [expanded_path.parts[: len(col_names)]] * len(data),
                    columns=col_names,
                )
                yield pd.concat([description, data], axis=1)

            else:
                msg = f"File `{expanded_path}` does not exist!"
                if _warn_if_missing:
                    warn(msg)
                else:
                    raise OSError(msg)


if __name__ == "__main__":
    dfs = list(
        iter_dfs(
            *args["paths"],
            _warn_if_missing=not args["strict_on_path_existance"],
        )
    )
    if len(dfs) == 0:
        warn("Nothing found.")
        sys.exit(1)
    else:
        all_stats = pd.concat(
            dfs,
            ignore_index=True,
        )
        if args["output"] is None:`
            print(all_stats.to_csv(index=False))
        else:
            save_df(all_stats, args["output"])
# # path = "out/base/{default,_old}/dataset=G8602/calibration=G8605/matches_config=_mz8/fragment_clusters_postprocessing=simple/fragment_clusters_postprocessing_config=default/edge_refinement_config=_ms2_norm_score_geq_{40,50,60,q10} out/base/{default,_old}/dataset=G8602/calibration=G8605/matches_config=_mz8/fragment_clusters_postprocessing=simple/fragment_clusters_postprocessing_config=default/edge_refinement_config=_maxRankLeq{6,8,10,12}"
# path = "out/base/_old/fragment_stats_config={default,no_normalization,ramintense}/sage/stats.csv"
# path = "out/`base/_old/fragment_stats_config={default,no_normalization,ramintense}/sage/edge_node_counts_summary.csv"
`
