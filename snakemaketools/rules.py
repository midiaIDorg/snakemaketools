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


# @dataclasses.dataclass
# class Folder:
#     location: str


# @dataclasses.dataclass
# class PathType:
#     name: str
#     # path_template: str  # should it be here or not

#     def __eq__(self, other: PathType):
#         assert self.name == other.name


# @dataclasses.dataclass
# class Root:
#     """Any root of a pipeline."""

#     path: Path
#     root_type: str
#     meta: dict


# def parse_rules(config: dict, outputs_maker: OutputsMakerType) -> DotDict[str, Rule]:
#     rules = DotDict()
#     for rule_type, subconfig in config.items():
#         try:
#             rules[rule_type] = Rule(
#                 rule_type=rule_type,
#                 expected_inputs={
#                     key: PathType(**value)
#                     for key, value in subconfig["expected_inputs"].items()
#                 },
#                 expected_outputs={
#                     key: PathType(**value)
#                     for key, value in subconfig["expected_outputs"].items()
#                 },
#                 outputs_maker=outputs_maker,
#             )
#         except TypeError as e:
#             print(f"Trouble at '{rule_type}'")
#             raise TypeError(f"Problem with `{rule_type}`:\n{repr(e)}")
#     return rules


# from snakemaketools.models import Path, RuleOrConfig

# @dataclasses.dataclass
# class Rule:
#     """A representation of a Snakemake rule.

#     Arguments:
#         type (str): Name/type of the rule.
#         inputs (dict[str,str]): A mapping assigning types to inputs (used e.g. to check user su
#         outputs (dict[str,str]): A mapping assigning to each output type its path template in the pipeline.
#         meta (dict): Optional additional information to be stored perhaps in a DB?
#     """

#     type: str
#     inputs: dict[str, str]
#     outputs: dict[str, str]
#     _type_ignore: str = "type_not_important"

#     def __call__(self, **inputs: Path | str) -> DotDict:
#         paths = {}
#         meta = {}

#         for input, input_path in inputs.items():
#             if input in self.inputs:
#                 if not isinstance(input_path, str):
#                     assert input_path.type == self.inputs[input]
#                     input_path = input_path.path
#                 paths[input] = input_path
#             else:
#                 meta[input] = input_path

#         if "rule_id" in meta:  # we are registering a ROOT
#             rule_or_config = None
#             rule_id = meta["rule_id"]
#         else:
#             rule_or_config = RuleOrConfig.GETINSERT(meta=meta, type=type)
#             rule_id = rule_or_config.id

#         output_paths = DotDict()
#         for output_name, output in self.outputs.items():
#             output_paths[output_name] = Path.GETINSERT(
#                 path=output["path"].format(rule_id=rule_id, **meta),
#                 type=output["type"],
#                 rule_or_config=rule_or_config,
#             )
#         return output_paths

#     def __repr__(self) -> str:
#         inputs = ", ".join(
#             f"{input_name}: {input_type}"
#             for input_name, input_type in self.inputs.items()
#         )
#         outputs = ", ".join(
#             f"{output_type}: {output_path_template}"
#             for output_type, output_path_template in self.outputs.items()
#         )
#         return f"{self.type}({inputs}) -> DotDict({outputs})"
