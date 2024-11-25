%load_ext autoreload
%autoreload 2

import pathlib
from collections import defaultdict
from pathlib import Path

import toml

from snakemaketools.parsers import iter_lines_recursively, simple_toml_finder

tomls = simple_toml_finder(iter_lines_recursively(root="workflow"))
