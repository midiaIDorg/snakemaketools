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

import snakemaketools.rules
from snakemaketools.datastructures import DotDict

db = Database()


class Folder(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    serialized_meta = Required(str, index=True)

    @classmethod
    @db_session
    def GETINSERT(cls, **meta) -> Folder:
        serialized_meta = json.dumps(meta, sort_keys=True)
        rule = cls.get(serialized_meta=serialized_meta)
        commit()
        if rule is None:
            rule = cls(serialized_meta=serialized_meta)
            commit()
        return rule


class Rule(Folder):
    @db_session
    def input_paths(self) -> DotDict[str, snakemaketools.rules.Path]:
        return DotDict(
            {
                path_name: Node[path_id]
                for path_name, path_id in json.loads(self.serialized_meta).items()
            }
        )


class Config(Folder):
    @db_session
    def get_config(self) -> dict:
        return json.loads(self.serialized_meta)


class Node(db.Entity):
    """A meaningul pipeline entity."""

    id = PrimaryKey(int, auto=True, unsigned=True)
    location = Required(str, index=True)
    rule_id = Optional(int)

    @db_session
    def get_parent_nodes(self) -> DotDict[str, snakemaketools.rules.Path]:
        if self.rule_id == None:
            return DotDict()
        return Rule[self.db_rule_id].input_paths()

    @classmethod
    @db_session
    def GETINSERT(cls, location: str) -> Path:
        """Get an object ID from the DB if exists; otherwise first create it."""
        node = cls.get(location=location)
        commit()
        if node == None:
            node = cls(location=location)
            commit()
        return node

    @classmethod
    @db_session
    def GET(cls, location: str) -> Path:
        """Get an object ID from the DB if exists; otherwise first create it."""
        node = cls.get(location=location)
        commit()
        if node == None:
            raise KeyError(f"There is no Node with location `{location}` in the DB.")
        return node


class NodeStorage:
    """Simple implementation of a general NodeStorage protocol defined in snakemaketools.rules

    TODO: consider later on storing data_types.
    """

    def get_rule_id(
        self,
        inputs: dict[str, snakemaketools.rules.Node],
    ) -> int:
        """Get a rule id for a given set of input nodes."""
        rule = Rule.GETINSERT(
            **{input_name: node.location for input_name, node in inputs.keys()}
        )
        return rule.id

    def get_outputs(
        self,
        inputs: dict[str, snakemake.rules.Node],
        expected_outputs: tuple[snakemaketools.rules.Node, ...],
    ) -> tuple[snakemaketools.rules.Node, ...]:
        rule_id = self.get_rule_id(inputs=inputs)
        return tuple(
            Node(
                data_type=expected_output.data_type,
                location=expected_output.location.format(rule_id=rule_id),
            )
            for expected_output in self.expected_outputs
        )

    def get_parent_nodes(
        self,
        location: str,
    ) -> DotDict[str, snakemaketools.rules.Node]:
        """Used in Snakemake DAG construction."""
        return Node.GET(location).get_parent_nodes()

    def get_config(self, location: str):
        return

    # def getinsert_config_node(# but this is not necessary: configs could be registered with a Rule too
    #     self,
    #     config: dict,
    # ) -> snakemaketools.rules.Node:
    #     ...

    def getinsert_config(self, config, location_template="tmp/configs/{}.toml"):
        dbroot = DBRoot.GETINSERT(config)
        dbpath = Node(location=location_template.format(dbroot.id))
        return dbpath.location

    def get_serialized_config(self, path):
        raise NotImplementedError


# @classmethod
# @db_session
# def GET(cls, path: str) -> Node:
#     """Get an object ID from the DB if exists; otherwise first create it."""
#     path = cls.get(path=path)
#     commit()
#     assert path != None
#     return path
