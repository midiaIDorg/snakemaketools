import copy
import inspect
import itertools
import typing

import click


def get_function_info(func):
    # Get the signature of the function
    name = func.__name__
    sig = inspect.signature(func)

    # Get the argument names and their type hints (if provided)
    args = [
        (
            param.name,
            param.annotation if param.annotation != inspect._empty else None,
            param.default if param.default != inspect._empty else None,
        )
        for param in sig.parameters.values()
    ]

    # Get the return type (if provided)
    return_type = (
        sig.return_annotation if sig.return_annotation != inspect._empty else None
    )

    return name, args, return_type


def get_click_option(dct):
    dct = copy.deepcopy(dct)
    name = dct.pop("name")
    return click.Option([f"--{name}"], **dct)


def iter_items(*dicts):
    for d in dicts:
        yield from d.items()


def long_snakemake_wrap(
    foo: typing.Callable[..., None],
    inputs: list[dict[str, str]] = [],
    outputs: list[dict[str, str]] = [],
    wildcards: list[dict[str, str]] = [],
    pipeline_configurable: list[dict[str, str]] = [],
    context_settings: dict = {"show_default": True},
) -> tuple[click.Command, dict]:
    foo_repr: dict = {
        "expected_inputs": {dct["name"]: {} for dct in inputs},
        "expected_outputs": [{"location": } for dct in outputs],
        "expected_wildcards": {dct["name"]: {} for dct in wildcards},
    }
    foo_cmd = click.Command(
        name=foo.__name__,
        context_settings=context_settings,
        params=list(
            map(
                get_click_option,
                (*inputs, *outputs, *wildcards, *pipeline_configurable),
            )
        ),
        callback=foo,
    )
    decorated_params = {p.name for p in foo_cmd.params}
    _, foo_params, _ = get_function_info(foo)
    missing: list[str] = []
    for param, _, _ in foo_params:
        if not param in decorated_params:
            missing.append(param)
    assert (
        len(missing) == 0
    ), f"Missing description of parameters `{missing}` in function `{foo.__name__}`."
    return foo_cmd, foo_repr
