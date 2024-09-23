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
    add_rule_and_paths_to_DB: typing.Callable = dataclasses.field(
        default=add_rule_and_paths_to_DB
    )
    _type_ignore: str = "type_not_important"

    def __call__(self, **inputs: Path | str) -> DotDict:
        paths = {}
        meta = {}

        for input, input_path in inputs.items():
            if input in self.inputs:
                if isinstance(input_path, Path):
                    assert input_path.type == self.inputs[input]
                    input_path = input_path.path
                paths[input] = input_path
            else:
                meta[input] = input_path

        if "rule_id" in meta:  # we are registering a ROOT
            rule_or_config = None
            rule_id = meta["rule_id"]
        else:
            rule_or_config = RuleOrConfig.GETINSERT(meta=meta, type=type)
            rule_id = rule_or_config.id

        output_paths = DotDict()
        for output_name, output in self.outputs.items():
            output_paths[output_name] = Path.GETINSERT(
                path=output["path"].format(rule_id=rule_id, **meta),
                type=output["type"],
                rule_or_config=rule_or_config,
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
    """Represent multiple rules in a pipeline.

    Gist of the idea: a pipeline is a python script that can use rules specified in this class.
    The class offers a simple interface:

    rules.<rule_name>(**inputs)

    E.G.

    rules = Rules.from_config(rule_config)

    rules.remove_raw_data_baseline_parametrization(dataset)
    """

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
