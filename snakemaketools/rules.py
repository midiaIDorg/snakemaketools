"""
TODO: 
would be nicer to add some level of abstraction so that Rule is an interface with specific implementations.
"""
from __future__ import annotations

import abc
import copy
import dataclasses
import typing
from collections.abc import Callable

import snakemaketools.parsers
from snakemaketools.datastructures import DotDict


@dataclasses.dataclass
class Node:
    """An object representing an entity used in the pipeline."""

    location: str = ""
    db_node_id: int | None = None
    type: typing.Type | str | None = None  # like for future

    def __post_init__(self):
        self.parents = {}  # this does not print it out ;)

    def copy(self) -> Node:
        return copy.deepcopy(self)

    def __iter__(self):
        for key, value in self.__dict__.items():
            if key != "parents":
                yield key, value


@dataclasses.dataclass
class Wildcard:
    """An object representing a wildcard."""

    name: str
    value: str = ""
    type: typing.Type | None = None
    _reserved_wildcard: str = "id"

    def __post_init__(self):
        assert self.name != self._reserved_wildcard, "Wildcard name `id` is reserved."

    @classmethod
    def from_location(
        cls,
        location: str,
        _parser: Callable[[str], list[str]] = snakemaketools.parsers.get_wildcards,
    ) -> dict[str, Wildcard]:
        wildcards = {
            wildcard_name: cls(name=wildcard_name)
            for wildcard_name in _parser(location)
            if wildcard_name != cls._reserved_wildcard
        }
        return wildcards

    @classmethod
    def from_named_values(cls, **kwargs: str) -> dict[str, Wildcard]:
        return {name: cls(name=name, value=value) for name, value in kwargs.items()}

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, Wildcard):
            return (
                self.name == other.name
                and self.value == other.value
                and self.type == other.type
            )
        else:
            return False


@dataclasses.dataclass
class Config:
    """
    An object representing a config for some specific rule.

    Arguments:
        serialized (str): Serialized version of the config.
        parsed (dict): Parsed config, mapping name to value.
        location_wildcards (dict): Represent parts of the config that should fill the `get_config_from_db_into_file_system` location.
    """

    serialized: str
    parsed: dict
    location_wildcards: DotDict[str, Wildcard]

    @classmethod
    def new(
        cls,
        config: dict | str,
        extension: Wildcard,  # a required Wildcard
        _converters: dict[
            str, snakemaketools.parsers.DictSerializer
        ] = snakemaketools.parsers.serializers,
        _to_wildcards: Callable[
            [dict[str, str]], Wildcard
        ] = Wildcard.from_named_values,
        **location_wildcards: Wildcard,
    ):
        if isinstance(config, str):
            serialized = config
            parsed = _converters[extension].loads(config)
        elif isinstance(config, dict):
            serialized = _converters[extension].dumps(config)
            parsed = config
        else:
            raise ValueError
        location_wildcards["extension"] = extension
        location_wildcards = _to_wildcards(**location_wildcards)
        return cls(
            serialized=serialized,
            parsed=parsed,
            location_wildcards=DotDict(location_wildcards),
        )


@dataclasses.dataclass
class Rule:
    name: str
    node_storage: NodeStorage
    expected_inputs: dict[str, Node]
    expected_outputs: tuple[Node, ...]
    expected_wildcards: dict[str, Wildcard]
    config_setter: bool = False

    def __post_init__(self):
        if self.config_setter:
            assert (
                len(self.expected_inputs) == 0
            ), "A config setter should not expect any inputs."

    @classmethod
    def from_config(
        cls,
        rule_name: str,
        node_storage: NodeStorage,
        expected_outputs: list[dict],
        expected_inputs: dict = {},
        config_setter: bool = False,
        node_factory: Callable[..., Node] = Node,
        wildcard_factory: Callable[..., Wildcard] = Wildcard,
    ):
        assert (
            len(expected_outputs) > 0
        ), "A rule without expected outputs does not find place in Snakemake."
        locations = [
            expected_output["location"] for expected_output in expected_outputs
        ]
        expected_wildcard_sets = list(map(wildcard_factory.from_location, locations))
        expected_wildcards = (
            expected_wildcard_sets.pop() if expected_wildcard_sets else {}
        )
        for i, wildcards_from_other_locations in enumerate(expected_wildcard_sets, 1):
            assert set(wildcards_from_other_locations) == set(
                expected_wildcards
            ), f"All locations should share their wildcards. However, it is not the case for `{locations[0]}` and `{locations[i]}`"

        return cls(
            name=rule_name,
            node_storage=node_storage,
            expected_inputs={
                node_name: node_factory(**node_info)
                for node_name, node_info in expected_inputs.items()
            },
            expected_outputs=tuple(
                node_factory(**expected_output) for expected_output in expected_outputs
            ),
            expected_wildcards=expected_wildcards,
            config_setter=config_setter,
        )

    def run(
        self,
        inputs: dict[str, Node],
        wildcards: dict[str, Wildcard],
        config: Config | None,
    ) -> tuple[Node, ...]:
        if self.config_setter:
            assert config is not None, "Config setter did not receive any Config."
            assert isinstance(  # TODO: use typeguard module?
                config, Config
            ), "Please provide a Config or an inheriter."
            assert (
                len(inputs) == 0
            ), "config setting rules only take `Config` argument. Provided `inputs`."
        else:
            for node_name, node in inputs.items():
                assert (
                    node_name in self.expected_inputs
                ), f"Node `{node_name}` not among expected inputs: `{self.expected_inputs}`."

                expected_type = self.expected_inputs[node_name].type
                if expected_type != None:
                    assert (
                        node.type == expected_type
                    ), f"Types mismatch: `{node_name}` is of type `{node.type}`. Its expected type is `{expected_type}`."

            for expected_input in self.expected_inputs:
                assert expected_input in inputs, f"Missing input `{expected_input}`."

            for wildcard_name in wildcards:
                assert (
                    wildcard_name in self.expected_wildcards
                ), f"Providing an unexpected wildcard `{wildcard_name}`"

            for wildcard_name in self.expected_wildcards:
                assert (
                    wildcard_name in wildcards
                ), f"Missing expected wildcard `{wildcard_name}`."

        return self.node_storage.get_outputs(
            inputs=inputs,
            expected_outputs=self.expected_outputs,
            config=config,
            wildcards=wildcards,
        )

    def __call__(self, **inputs: Node | Wildcard) -> tuple[Node, ...] | Node:
        nodes: dict[str, Node] = {}
        wildcards: dict[str, Wildcard] = {}
        config: Config | None = None
        for key, value in inputs.items():
            if isinstance(value, Node):
                nodes[key] = value
            elif isinstance(value, Wildcard):
                wildcards[key] = value
            elif isinstance(value, Config):
                assert (
                    self.config_setter
                ), "Passed in Config to rule that is not a config_setter."
                assert config is None, "can only set config once."
                config = value
            else:
                raise ValueError(
                    f"Rule `{self.name}` received an invalid type: {type(value).__name__}."
                )
        outputs = self.run(inputs=nodes, wildcards=wildcards, config=config)

        for output in outputs:
            output.parents[self.name] = DotDict(inputs)

        if len(outputs) == 1:
            return outputs[0]

        return outputs


@dataclasses.dataclass
class NodeStorage(abc.ABC):
    @abc.abstractmethod
    def get_outputs(
        self,
        inputs: dict[str, Node],
        expected_outputs: tuple[Node, ...],
        wildcards: dict[str, Wildcard],
        config: Config | None,
    ) -> tuple[Node, ...]:
        """Get output nodes"""

    @abc.abstractmethod
    def get_rule_input_paths(self, rule_id: int) -> dict[str, str]:
        """Get names of input and their paths for a given rule_id."""

    @abc.abstractmethod
    def get_config(self, location: str) -> DotDict:
        """Get a string with config that is supposed to be saved under the proded location."""
