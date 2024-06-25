#!/usr/bin/env python3

import argparse
import pathlib
import subprocess

from snakemaketools.io_ops import expand_path

parser = argparse.ArgumentParser(
    description="Run some program sequentially on the set of provided input paths, i.e. ."
)
parser.add_argument(
    "command",
    help="A command that will be filled with a path, i.e. 'ls -a {path}'.",
    type=str,
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
        for path in expand_path(expandable_bash_path):
            formated_command = args.command.format(path=path)
            print("Running:\n{formated_command}\n\n")
            subprocess.run(
                formated_command,
                shell=True,
            )
            print("Finished\n")
