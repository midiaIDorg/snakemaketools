from __future__ import annotations

import dataclasses
import typing

from snakemaketools.datastructures import DotDict

# @dataclasses.dataclass
# class PathType:
#     name: str
#     # path_template: str  # should it be here or not

#     def __eq__(self, other: PathType):
#         assert self.name == other.name


@dataclasses.dataclass
class Path:
    """A path stored in the file system."""

    data_type: str
    location: str
    parent_paths: DotDict[str, Path] = dataclasses.field(default_factory=DotDict)


@dataclasses.dataclass
class Root:
    """Any root of a pipeline."""

    path: Path
    root_type: str
    meta: dict


class PathStorage(typing.Protocol):
    def get_parents(self, path: Path) -> DotDict[str, Path]:
        """Get paths of the rule resulting in the given path."""

    def getinsert_children(
        self, rule_type: RuleType, inputs: DotDict[str, Path]
    ) -> DotDict[str, Path]:
        """Given a rule type and its inputs, get the outputs.

        Crate them in the storage if not existing.
        """

    def get_siblings(self, path: Path) -> DotDict[str, Path]:
        """Get paths created by the same rule as the provided path."""

    def getinsert_roots(self, root_type: str, meta: dict) -> DotDict[str, Path]:
        """Get the path for a root with a given meta information."""

    def getinsert_config(self, config: dict) -> Path:
        """Insert a config into the storage."""

    def get_serialized_config(self, path: str) -> str:
        """Get the config string that can be directly saved under some path.

        To be used by Snakemake save_serialized_config rule.
        """


@dataclasses.dataclass
class Rule:
    rule_type: str
    expected_inputs: DotDict[str, str]
    expected_outputs: DotDict[str, str]
    path_storage: PathStorage

    def __call__(self, **input_paths: Path) -> DotDict[str, Path]:
        # inputs check
        for in_path_name, in_path in input_paths.items():
            assert (
                in_path_name in self.expected_inputs
            ), f"Path with name `{in_path_name}` not among expected inputs: `{self.expected_inputs}`."

            expected_type = self.expected_inputs[in_path_name]
            assert (
                in_path.data_type == expected_type
            ), f"Types do not match: `{in_path_name}` of type `{in_path.data_type}` vs expected type `{expected_type}`."

        for expected_input in self.input_paths:
            assert (
                expected_input in input_paths
            ), f"Missing argument `{expected_input}` in rule `{self.rule_type}` call."

        output_paths = self.path_storage.output_paths(input_paths)

        # outputs checks
        for output_name, output in output_paths.items():
            assert output_name in self.expected_outputs
            assert output.data_type == self.expected_outputs[output_name].data_type

        for output_name in self.expected_outputs:
            assert (
                output_name in input_paths
            ), f"Missing an expected output `{output_name}` among the provided input paths."

        return output_paths

    def __repr__(self) -> str:
        inputs = ", ".join(
            f"{input_name}: {input_type}" if input_type else input_name
            for input_name, input_type in self.expected_inputs.items()
        )
        outputs = ", ".join(
            f"{output_type}: {output_path_template['type']}"
            for output_type, output_path_template in self.expected_outputs.items()
        )
        return f"{self.rule_type}({inputs}) -> DotDict({outputs})"


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
