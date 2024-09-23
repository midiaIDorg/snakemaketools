import dataclasses
import typing

from snakemaketools.datastructures import DotDict
from snakemaketools.models import Path, RuleOrConfig, add_rule_and_paths_to_DB


@dataclasses.dataclass
class Rule:
    """A representation of a Snakemake rule.

    Arguments:
        type (str): Name/type of the rule.
        inputs (dict[str,str]): A mapping assigning types to inputs (used e.g. to check user supplied arguments).
        outputs (dict[str,str]): A mapping assigning to each output type its path template in the pipeline.
        meta (dict): Optional additional information to be stored perhaps in a DB?
        add_rule_and_paths_to_DB (Callable): A function used to add register the rule, its inputs and outputs, and potential meta information in some form of a DB. Dependency injection possible here.

    """

    type: str
    inputs: dict[str, str]
    outputs: dict[str, str]
    meta: dict = dataclasses.field(default_factory=dict)
    add_rule_and_paths_to_DB: typing.Callable = dataclasses.field(
        default=add_rule_and_paths_to_DB
    )

    def __call__(self, **inputs: str) -> DotDict:
        # IO control
        for _input in inputs:
            assert (
                _input in self.inputs
            ), f"`{_input}` is not among accepted input types for rule {self.type}: {self.inputs}"

        for _input in self.inputs:
            assert (
                _input in inputs
            ), f"Missing input `{_input}` in rule {self.type}. Requiring `{self.inputs}`."

        output_paths = self.add_rule_and_paths_to_DB(
            type=self.type,
            inputs=inputs,
            outputs=self.outputs,
            **self.meta,
        )

        return output_paths

    def __repr__(self) -> str:
        inputs = ", ".join(
            f"{input_name}: {input_type}"
            for input_name, input_type in self.inputs.items()
        )
        outputs = ", ".join(
            f"{output_type}: {output_path_template}"
            for output_type, output_path_template in self.outputs.items()
        )
        return f"{self.type}({inputs}) -> DotDict({outputs})"


class Rules:
    def __init__(self, rules: dict[str, Rule]):
        self._rules = rules

    @classmethod
    def from_config(cls, config: dict):
        rules = {}
        for rule_type, subconfig in config.items():
            try:
                rules[rule_type] = Rule(type=rule_type, **subconfig)
            except TypeError as e:
                print(f"Trouble at '{rule_type}'")
                raise TypeError(f"Problem with `{rule_type}`:\n{repr(e)}")
        return cls(rules)

    def __getattr__(self, rule_name):
        try:
            return self._rules[rule_name]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no rule '{rule_name}'")

    def __repr__(self) -> str:
        txt = "\n\n".join(map(repr, self._rules.values()))
        return f"Rules:\n{txt}"
