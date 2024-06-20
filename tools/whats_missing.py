#!/usr/bin/env python3

import argparse
import pathlib
import sys
import typing
from warnings import warn

import pandas as pd
from pandas_ops.io import read_df, save_df
from snakemaketools.io_ops import expand_path, parse_path

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
    for expandable_bash_path in args.expandable_bash_paths:
        for expanded_path in expand_path(path):
            if not expanded_path.exists():
                print(expanded_path)
