from __future__ import annotations

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

    @property
    @db_session
    def parent_paths(self) -> dict[str, str]:
        return RuleOrConfig[self.rule_or_config_id].input_paths

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
    def GET(cls, path: str) -> Path:
        """Get an object ID from the DB by path.

        This is used only by the Snakemake.

        Arguments:
            path (str): Path's path of storage.

        Returns:
            Path: An instance of the path.

        Raises:
            KeyError: if a path with a given (meta, type) does not exist in the db.
        """
        path = cls.get(path=path)
        commit()
        if path is None:
            raise KeyError(f"There DB does not contain a Path(path={path})")
        return path


class RuleOrConfig(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    _meta = Required(str)
    type = Required(str)
    composite_index(_meta, type)

    @property
    @db_session
    def inputs(self) -> dict[str, Path]:
        return {
            input_type: Path[input_id]
            for input_type, input_id in self.meta["inputs"].items()
        }

    @property
    @db_session
    def input_paths(self) -> dict[str, str]:
        return {input_type: path.path for input_type, path in self.inputs.items()}

    @property
    def meta(self) -> dict:
        return json.loads(self._meta)

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
    def get_input_paths(cls, fileid: int) -> dict[str, Path]:
        rule_or_config = cls[fileid]
        return rule_or_config.inputs
