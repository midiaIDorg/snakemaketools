"""
TODO: 
would be nicer to add some level of abstraction so that Rule is an interface with specific implementations.
"""
from __future__ import annotations

import abc
import collections.abc
import copy
import dataclasses
import functools
import typing

from snakemaketools.datastructures import DotDict


@dataclasses.dataclass
class Node:
    """An object representing an entity used in the pipeline."""

    location: str | None = None
    type: typing.Type | str | None = None
    _debug: dict = dataclasses.field(default_factory=dict)

    def __iter__(self):
        yield "location", self.location
        yield "type", self.type

    def copy(self) -> Node:
        return self.__class__(
            location=self.location,
            type=self.type,
        )


@dataclasses.dataclass
class Wildcard:
    """An object representing a wildcard."""

    value: str = ""
    type: typing.Type | None = None


@dataclasses.dataclass
class Rule:
    name: str
    node_storage: NodeStorage
    expected_inputs: dict[str, Node]
    expected_outputs: tuple[Node, ...]
    expected_wildcards: dict[str, Wildcard]

    @classmethod
    def from_config(
        cls,
        rule_name: str,
        node_storage: NodeStorage,
        expected_outputs: dict,
        expected_inputs: dict = {},
        expected_wildcards: dict = {},
    ):
        assert (
            len(expected_outputs) > 0
        ), "A rule without expected outputs does not find place in Snakemake."
        return cls(
            name=rule_name,
            node_storage=node_storage,
            expected_inputs={
                node_name: node_storage.node_factory(**node_info)
                for node_name, node_info in expected_inputs.items()
            },
            expected_outputs=tuple(
                node_storage.node_factory(**expected_output)
                for expected_output in expected_outputs
            ),
            expected_wildcards={
                wildcard_name: node_storage.wildcard_factory(**wildcard_info)
                for wildcard_name, wildcard_info in expected_wildcards.items()
            },
        )

    def run(
        self,
        config: dict | None,
        input_nodes: dict[str, Node],
        wildcards: dict[str, Wildcard],
    ) -> tuple[Node, ...] | Node:
        for node_name, node in input_nodes.items():
            assert (
                node_name in self.expected_inputs
            ), f"Node `{node_name}` not among expected inputs: `{self.expected_inputs}`."

            expected_type = self.expected_inputs[node_name].type
            if expected_type != None:
                assert (
                    node.type == expected_type
                ), f"Types mismatch: `{node_name}` is of type `{node.type}`. Its expected type is `{expected_type}`."

        for expected_input in self.expected_inputs:
            assert expected_input in input_nodes, f"Missing input `{expected_input}`."

        for wildcard_name in wildcards:
            assert wildcard_name in self.expected_wildcards

        for wildcard_name in self.expected_wildcards:
            assert wildcard_name in wildcards

        outputs = self.node_storage.get_outputs(
            inputs=input_nodes,
            expected_outputs=self.expected_outputs,
            config=config,
            wildcards=wildcards,
        )

        if len(outputs) == 1:
            return outputs[0]

        return outputs

    # TODO: should allow for *args inputs, not only **nargs. Like any function.
    def __call__(self, **inputs: Node) -> tuple[Node, ...] | Node:
        nodes: dict[str, Node] = {}
        wildcards: dict[str, Wildcard] = {}
        for key, value in inputs.items():
            if isinstance(value, Node):
                nodes[key] = value
            elif isinstance(value, Wildcard):
                wildcards[key] = value
            else:
                raise ValueError(
                    f"Passed in a value that is not a string nor a Node (or inheriting therefrom)."
                )
        return self.run(config=None, input_nodes=nodes, wildcards=wildcards)

    def set(self, config: dict) -> tuple[Node, ...] | Node:
        return self.run(config=config, input_nodes={}, wildcards={})


@dataclasses.dataclass
class NodeStorage(abc.ABC):
    node_factory: collections.abc.Callable[..., Node] = Node
    wildcard_factory: collections.abc.Callable[..., Wildcard] = Wildcard

    @abc.abstractmethod
    def get_outputs(
        self,
        inputs: dict[str, Node],
        expected_outputs: tuple[Node, ...],
        wildcards: dict[str, Wildcard],
        config: dict | None = None,
    ) -> tuple[Node, ...]:
        """Get output nodes"""

    @abc.abstractmethod
    def get_rule_input_paths(self, rule_id: int) -> dict[str, str]:
        """Get names of input and their paths for a given rule_id."""

    @abc.abstractmethod
    def get_config(self, location: str) -> str:
        """Get a string with config that is supposed to be saved under the proded location."""
