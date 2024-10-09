%load_ext autoreload
%autoreload 2

import inspect
import pathlib

from snakemaketools.models import SimplePonyNodeStorage


def get_function_info(func):
    # Get the signature of the function
    name = func.__name__
    sig = inspect.signature(func)

    # Get the argument names and their type hints (if provided)
    args = [
        (
            param.name,
            param.annotation if param.annotation != inspect._empty else None,
        )
        for param in sig.parameters.values()
    ]

    # Get the return type (if provided)
    return_type = (
        sig.return_annotation if sig.return_annotation != inspect._empty else None
    )

    return name, args, return_type


# Example function with type hints
def example_func(a: int, b: str) -> bool:
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


def postprocess_tims_clusters(
    in_clusters: pathlib.Path,
    out_clusters: pathlib.Path,
    out_additional_clusters_stats: pathlib.Path,
    in_analysis_tdf: pathlib.Path | None = None,
    silent: bool = True,
) -> None:
    pass

# OK, sort the question of inputs: it looks like a fairly simple thing to do: even passing in data-types.

node_storage = SimplePonyNodeStorage(debug=True)
# what we are missing, are the output paths: each expected output needs a location.
rule_name, rule_IO, _ = get_function_info(postprocess_tims_clusters)

expected_inputs = 

# by default, they should all go into one folder. And the folder should be in a path that is unique to the rule and its arguments. So that's not that limitting.


"tmp/general/rule={rule_name}/{rule_id}{resources}"
