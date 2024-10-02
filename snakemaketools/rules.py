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

    data_type: str | None  # None = no special data type # think of using typing system
    location: str

    def __iter__(self):
        yield "data_type", self.data_type
        yield "location", self.location

    def copy(self) -> Node:
        return copy.deepcopy(self)


@dataclasses.dataclass
class Rule:
    name: str
    node_storage: NodeStorage
    expected_inputs: DotDict[str, Node]
    expected_outputs: tuple[Node, ...]
    expect_config_when_called: bool = False

    def __call__(
        self, config: dict | None = None, **inputs: Node
    ) -> tuple[Node, ...] | Node:
        assert not (
            self.expect_config_when_called and config == None
        ), f"Call of rule `{self.rule}` expects a config but you did not provide it, or provided None."

        for node_name, node in inputs.items():
            assert (
                node_name in self.expected_inputs
            ), f"Node `{node_name}` not among expected inputs: `{self.expected_inputs}`."

            expected_data_type = self.expected_inputs[node_name].data_type

            if expected_data_type != None:
                assert (
                    node.data_type == expected_data_type
                ), f"Types mismatch: `{node_name}` is of type `{node.data_type}`. Its expected type is `{expected_data_type}`."

        for expected_input in self.expected_inputs:
            assert expected_input in inputs, f"Missing input `{expected_input}`."

        outputs = self.node_storage.get_outputs(
            inputs=inputs,
            expected_outputs=self.expected_outputs,
            config=config,
        )

        if len(outputs) == 1:
            return outputs[0]

        return outputs


@dataclasses.dataclass
class NodeStorage(abc.ABC):
    node_factory: collections.abc.Callable[..., Node] = Node

    @abc.abstractmethod
    def get_outputs(
        self,
        inputs: dict[str, Node],
        expected_outputs: tuple[Node, ...],
        config: dict | None = None,
    ) -> tuple[Node, ...]:
        """Get output nodes"""

    @abc.abstractmethod
    def get_parent_nodes(self, location: str) -> DotDict[str, Node]:
        """Get nodes that lead to the creation of the current Node."""
