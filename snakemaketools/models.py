from __future__ import annotations

import copy
import json

from pony.orm import (
    Database,
    Optional,
    PrimaryKey,
    Required,
    Set,
    commit,
    composite_index,
    db_session,
)

db = Database()


class Path(db.Entity):
    """Any unique path identifier."""

    id = PrimaryKey(int, auto=True, unsigned=True)
    path = Required(str)
    type = Required(str)
    rule_or_config_id = Optional(int)
    composite_index(path, type)

    @db_session
    def parent_paths(self) -> dict[str, str]:
        return RuleOrConfig[self.rule_or_config_id].input_paths()

    @classmethod
    @db_session
    def GETINSERT(
        cls, path: str, type: str, rule_or_config: RuleOrConfig | None = None
    ) -> Path:
        """Get an object ID from the DB if exists; otherwise first create it."""
        node = cls.get(path=path, type=type)
        commit()
        if node is None:
            rule_or_config_id = rule_or_config.id if rule_or_config != None else None
            node = cls(
                path=path,
                type=type,
                rule_or_config_id=rule_or_config_id,
            )
            commit()
        return node

    @classmethod
    @db_session
    def GET(cls, path: str, type: str) -> Path:
        """Get an object ID from the DB by path.

        This is used only by the Snakemake.

        Arguments:
            path (str): Path's path.
            type (str): Path's type.

        Returns:
            Path: An instance of the path.

        Raises:
            KeyError: if a path with a given (meta, type) does not exist in the db.
        """
        path = cls.get(path=path, type=type)
        commit()
        if path is None:
            raise KeyError(f"There DB does not contain a Path(path={path})")
        return path


class RuleOrConfig(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    _meta = Required(str)
    type = Required(str)
    composite_index(_meta, type)

    @db_session
    def inputs(self) -> dict[str, Path]:
        return {
            input_type: Path[input_id]
            for input_type, input_id in self.meta["inputs"].items()
        }

    @db_session
    def input_paths(self) -> dict[str, str]:
        return {input_type: path.path for input_type, path in self.inputs().items()}

    @property
    def meta(self) -> dict:
        return json.loads(self._meta)

    @db_session
    def get_config(self, type) -> dict:
        assert self.type == type
        return self.meta["subconfig"]["config"]

    @classmethod
    @db_session
    def GETINSERT(cls, meta: dict, type: str) -> RuleOrConfig:
        """Get an object ID from the DB if exists; otherwise first create it."""
        assert (
            "inputs" in meta
        ), "The meta information about the rule must contain `inputs` dictionary, even if empty."
        _meta = json.dumps(meta, sort_keys=True)
        rule = cls.get(_meta=_meta, type=type)
        commit()
        if rule is None:
            rule = cls(_meta=_meta, type=type)
            commit()
        return rule

    @classmethod
    @db_session
    def GETCONFIG(cls, path: str, type: str):
        path = Path.GET(path=path, type=type)
        return cls[path.rule_or_config_id].get_config(type)


def add_rule_and_paths_to_DB(
    type: str,
    outputs: dict,
    inputs: dict[str, Path] = {},
    **meta,
) -> tuple[Path, ...]:
    meta["inputs"] = {}
    for input_type, input_path in inputs.items():
        assert input_path.id is not None
        meta["inputs"][input_type] = input_path.id
    rule = RuleOrConfig.GETINSERT(meta=meta, type=type)
    output_paths = [
        Path.GETINSERT(path=output_path, type=output_type, rule_or_config=rule)
        for output_type, output_path in inputs.items()
    ]
    return output_paths
