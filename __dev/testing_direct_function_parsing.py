%load_ext autoreload
%autoreload 2

import hashlib
import importlib
import inspect
import pathlib
from collections import defaultdict
from typing import Callable

import click
from snakemaketools.cli import greet
from snakemaketools.models import SimplePonyNodeStorage
from snakemaketools.wrappers import get_function_info, long_snakemake_wrap


# Example function with type hints
def example_func(a: int, b: str="dupa") -> bool:
    return str(a) == b

def example_func2(c, d):
    return str(a) == b


# Extracting info
get_function_info(example_func)
get_function_info(example_func2)

print("Arguments:", arguments)
print("Return Type:", output_type)

sig = inspect.signature(example_func2)
example_func2.__name__

# we could allow for importing of functions.
# and then annotating them.

# that would be enough! And if provided paths: then easier to analyze.
# def foo(in0, in1, in2, out0, out1)




def hash256(in_file: str, out_hash: str):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    # cause who will stop us? nobody!
    # here we are, born to be kings
    # we're the coders of universe...
    sha256 = hashlib.sha256()
    with open(str(in_filepath), "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    with open(str(out_filepath), "w") as f:
        f.write(sha256.hexdigest())

foo_name, arguments, _ = get_function_info(hash256)

args = defaultdict(list)
for arg in arguments:
    what, name = arg[0].split("_")
    args[what].append(name)

args["in"]
args["out"]




inputs = [arg[0].split('_')[1]  if ]

def postprocess_tims_clusters(
    out_additional_clusters_stats: pathlib.Path,
    out_clusters: pathlib.Path,
    in_clusters: pathlib.Path,
    in_analysis_tdf: pathlib.Path | None = None,
    silent: bool = True,
) -> None:
    pass


foo = postprocess_tims_clusters
get_function_info(foo)


"tims": {
      "expected_inputs": {
           "dataset": {},
           "config": {}
      },
      "expected_outputs": [
           {
                "location": "tmp/clusters/tims/{id}.hdf"
           },
           {
                "location": "tmp/clusters/tims/{id}/qc"
           }
      ],
      "expected_wildcards": {
           "executable":{},
           "dim":{}
      }
 },

# how to include information on the stupid location....
# "location": "tmp/clusters/tims/{id}.hdf"
# ????

postprocess_tims_clusters_cmd, postprocess_tims_clusters_dct = long_snakemake_wrap(
    foo = postprocess_tims_clusters,
    inputs = [
        {
            "name": "in_clusters",
            "help": "Path to the '.hdf' file with tims clusters.",
        },
        {
            "name": "in_analysis_tdf",
            "help": "Path to the 'analysis_tdf' file. Necessary for fragment cluster computations.",
            "default": None
        }
    ],
    outputs = [
        {
            "name": "out_clusters",
            "help": "Path to the '.startrek' folder to save the results into.",
        },
        {
            "name": "out_additional_clusters_stats",
            "help": "Path to the '.parquet' file storing addtional cluster stats that tims provides.",
        },
    ],
    wildcards = [],
    pipeline_configurable = [
        {
            "name": "silent",
            "help": "Stop printing to stdout.",
        }
    ],
)

importlib.import_module("snakemaketools.cli").greet("Matteo")

importlib.import_module("snakemaketools.cli")


def import_function(path):
    """Get an object from an installed module.

    Arguments:
        path (str): Follow patten "path.to.module:object"
    """
    module, function = path.split(":")
    return getattr(importlib.import_module(module), function)


import_function("snakemaketools.cli:greet")





list(map(get_click_option, [*inputs, *outputs, *path_wildcards, *pipeline_configurable]))

# this can be very simply added.
greet_cmd = click.Command(
    name="greet",
    context_settings={"show_default": True},
    params=[
        click.Option(["--name"], help="Put your name.", default="Stranger"),
        click.Option(["--something"], help="Put something (optional)", default=None),
    ],
    callback=greet,
)



# OK, sort the question of inputs: it looks like a fairly simple thing to do: even passing in data-types.

node_storage = SimplePonyNodeStorage(debug=True)
# what we are missing, are the output paths: each expected output needs a location.
rule_name, rule_IO, _ = get_function_info(postprocess_tims_clusters)

expected_inputs = 

# by default, they should all go into one folder. And the folder should be in a path that is unique to the rule and its arguments. So that's not that limitting.


"tmp/general/rule={rule_name}/{rule_id}{resources}"


# cli.py
def greet(name):
    """A simple greeting command."""
    click.echo(f"Hello, {name}!")

greet("a")

greet_cmd = click.command()(click.argument("name")(greet))
