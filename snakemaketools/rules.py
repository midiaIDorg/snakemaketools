from __future__ import annotations

import abc
import collections.abc
import copy
import dataclasses
import typing

from snakemaketools.datastructures import DotDict


@dataclasses.dataclass
class Node:
    """An object representing an entity used in the pipeline."""

    data_type: str
    location: str

    def __iter__(self):
        yield "data_type", self.data_type
        yield "location", self.location

    def copy(self) -> Node:
        return copy.deepcopy(self)


@dataclasses.dataclass
class Rule:
    node_storage: NodeStorage
    expected_inputs: DotDict[str, Node]
    expected_outputs: tuple[Node, ...]

    def __call__(self, **inputs: Node) -> tuple[Node]:
        for node_name, node in inputs.items():
            assert (
                node_name in self.expected_inputs
            ), f"Node `{node_name}` not among expected inputs: `{self.expected_inputs}`."

            expected_data_type = self.expected_inputs[in_path_name].data_type
            assert (
                node.data_type == expected_data_type
            ), f"Types mismatch: `{node_name}` is of type `{node.data_type}`. Its expected type is `{expected_data_type}`."

        for expected_input in self.expected_inputs:
            assert expected_input in inputs, f"Missing input `{expected_input}`."

        return self.node_storage.get_outputs(
            inputs=inputs,
            expected_outputs=self.expected_outputs,
        )

    def __repr__(self) -> str:
        inputs = ", ".join(
            f"{input_name}: {input_type}" if input_type else input_name
            for input_name, input_type in self.expected_inputs.items()
        )
        outputs = ", ".join(repr(output) for output in self.expected_outputs)
        return f"CALLABLE[({inputs}) -> DotDict({outputs})]"


@dataclasses.dataclass
class NodeStorage(abc.ABC):
    node_factory: collections.abc.Callable[..., Node] = Node

    @abc.abstractmethod
    def get_outputs(
        self,
        inputs: dict[str, Node],
        expected_outputs: tuple[Node, ...],
    ) -> tuple[Node, ...]:
        """Get output nodes"""

    @abc.abstractmethod
    def get_parent_nodes(self, location: str) -> DotDict[str, Node]:
        """Get nodes that lead to the creation of the current Node."""
