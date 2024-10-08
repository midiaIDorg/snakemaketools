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

    location: str
    data_type: str | None = (
        None  # None = no special data type # think of using typing system
    )
    _debug: dict = dataclasses.field(default_factory=dict)

    def __iter__(self):
        yield "location", self.location
        yield "data_type", self.data_type

    def copy(self) -> Node:
        return self.__class__(
            location=self.location,
            data_type=self.data_type,
        )


@dataclasses.dataclass
class Rule:
    name: str
    node_storage: NodeStorage
    expected_inputs: dict[str, str]
    expected_outputs: tuple[Node, ...]

    def run(
        self,
        config: dict | None,
        input_nodes: dict[str, Node],
        wildcards: dict[str, str],
    ) -> tuple[Node, ...] | Node:
        for node_name, node in input_nodes.items():
            assert (
                node_name in self.expected_inputs
            ), f"Node `{node_name}` not among expected inputs: `{self.expected_inputs}`."

            expected_data_type = self.expected_inputs[node_name]
            if expected_data_type != None:
                assert (
                    node.data_type == expected_data_type
                ), f"Types mismatch: `{node_name}` is of type `{node.data_type}`. Its expected type is `{expected_data_type}`."

        for expected_input in self.expected_inputs:
            assert expected_input in input_nodes, f"Missing input `{expected_input}`."

        outputs = self.node_storage.get_outputs(
            inputs=input_nodes,
            expected_outputs=self.expected_outputs,
            config=config,
            wildcards=wildcards,
        )

        if len(outputs) == 1:
            return outputs[0]

        return outputs

    def __call__(self, **inputs: Node) -> tuple[Node, ...] | Node:
        nodes = {}
        wildcards = {}
        for key, value in inputs.items():
            if isinstance(value, Node):
                nodes[key] = value
            elif isinstance(value, str):
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

    @abc.abstractmethod
    def get_outputs(
        self,
        inputs: dict[str, Node],
        expected_outputs: tuple[Node, ...],
        config: dict | None = None,
        wildcards: dict | None = None,
    ) -> tuple[Node, ...]:
        """Get output nodes"""

    @abc.abstractmethod
    def get_rule_input_paths(self, rule_id: int) -> dict[str, str]:
        """Get names of input and their paths for a given rule_id."""

    @abc.abstractmethod
    def get_config(self, location: str) -> str:
        """Get a string with config that is supposed to be saved under the proded location."""
