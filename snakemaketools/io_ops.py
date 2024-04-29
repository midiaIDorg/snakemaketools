from pathlib import Path
from pprint import pprint
from types import SimpleNamespace
from warnings import warn

import tomllib
from snakemaketools.encodings import BestPathEncoder, fill_path_templates_with_wildcards
from snakemaketools.import_ops import script_to_globals
from snakemaketools.wildcard_ops import update_wildcards


def get_wished_inputs_and_outputs(
    forward_rules_path: str | Path,
    config_path: str | Path,
    pipeline_script_path: str | Path,
    pipeline_output_folder: str | Path,
    wildcard_diffs_serialized: str | None = None,
    silent: bool = False,
) -> dict[str, tuple[str, str]]:
    """
    Get a dictionary mapping the name of a path template to a tuple (temporary pipeline location, final pipeline location).

    Arguments:
        forward_rules_path (str,Path): A path to pipeline agnostic forward path template rules.
        config_path (str,Path): Path to a toml config with potentially [wildcard_diffs] and required [wishlist].
        pipeline_script_path (str,Path): A path to a python script defining paths.
        pipeline_output_folder (str,Path): Path to the final location [relative to midia_pipe].
        wildcard_diffs_serialized (str,Path): Serialized wildcard diffs in form of '<param_name_0>=<param_value_0>/.../<param_name_{k-1}>=<param_value_{k-1}>/'. Take precedence over other entries.
        silent (bool): Refrain from pushing to stdout.
    """
    (
        config_path,
        pipeline_script_path,
        pipeline_output_folder,
        forward_rules_path,
    ) = map(
        Path,
        (
            config_path,
            pipeline_script_path,
            pipeline_output_folder,
            forward_rules_path,
        ),
    )
    forward_rules = SimpleNamespace(**script_to_globals(forward_rules_path))

    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    assert "wishlist" in config, "This config needs to contain section [wishlist]"
    assert (
        len(config["wishlist"]) > 0
    ), "This config's [wishlist] section cannot be empty."

    wildcard_diffs = {}
    if "wildcard_diffs" in config:
        wildcard_diffs = config["wildcard_diffs"]

    if (
        wildcard_diffs_serialized is not None
        and wildcard_diffs_serialized != "default_wildcards"
    ):
        for key_equals_value in wildcard_diffs_serialized.split("/"):
            key, value = key_equals_value.split("=")
            wildcard_diffs[key] = value

    with open(pipeline_script_path, "r") as script:
        script_globals = {}
        exec(script.read(), script_globals)
        wildcards = script_globals["wildcards"]
        create_path_templates = script_globals["create_path_templates"]

    update_wildcards(wildcards, wildcard_diffs)

    if not silent:
        print("Using the following final wildcards:")
        pprint(wildcards)

    path_templates = create_path_templates(wildcards, forward_rules)

    fullfillable_wishes = {}
    obtainable_path_templates = {}
    for wish, locations in config["wishlist"].items():
        if wish in path_templates.__dict__:
            fullfillable_wishes[wish] = locations
            obtainable_path_templates[wish] = path_templates.__dict__[wish]
        else:
            msg = f"You cannot wish for `{wish}`. Your settings prevent that wish of coming true."
            warn(msg)
    obtainable_path_templates = SimpleNamespace(**obtainable_path_templates)

    encoder = BestPathEncoder()
    filled_paths = fill_path_templates_with_wildcards(
        obtainable_path_templates, wildcards
    )
    encoded_paths = encoder.encode_paths(filled_paths)

    path_template_copy_from_to = {}
    for path_template_name, final_location in fullfillable_wishes.items():
        assert (
            path_template_name in encoded_paths.__dict__
        ), f"Missing `{path_template_name}`"
        path_template_copy_from_to[path_template_name] = (
            str(encoded_paths.__dict__[path_template_name]),
            str(pipeline_output_folder / final_location),
        )
    return path_template_copy_from_to
