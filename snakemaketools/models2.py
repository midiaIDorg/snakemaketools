from __future__ import annotations

import copy
import dataclasses
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


class Storable(db.Entity):
    """A general entry in a DB.

    Only one table is needed to represent all things on this approach.

    Everything is indexed by the json-serialized content string.
    """

    id = PrimaryKey(int, auto=True, unsigned=True)
    serialized_content = Required(str, index=True)

    @db_session
    def get_content(self):
        return json.loads(self.serialized_content)

    @classmethod
    @db_session
    def GETINSERT(cls, **content) -> Storable:
        serialized_content = json.dumps(content, sort_keys=True)
        storable = cls.get(serialized_content=serialized_content)
        commit()
        if storable is None:
            storable = cls(serialized_content=serialized_content)
            commit()
        return storable

    @classmethod
    @db_session
    def GET(cls, **content: str) -> Storable:
        """Get an object ID from the DB if exists; otherwise first create it."""
        serialized_content = json.dumps(content, sort_keys=True)
        storable = cls.get(serialized_content=serialized_content)
        commit()
        if storable == None:
            raise KeyError(
                f"There is no storable with content `{serialized_content}` in the DB."
            )
        return storable


class Config(Storable):
    def get_config(self) -> dict:
        return self.get_content()


class Rule(Storable):
    def input_nodes(self) -> DotDict[str, dict]:  # order matters
        inputs = DotDict()
        for node_name, node_id in self.get_content.items():
            inputs[node_name] = Node[node_id].get_node_contents()
        return inputs


class Node(Storable):
    """Any meaningul pipeline entity."""

    rule_id = Optional(int)
    # only to store info from a potential subclass of Node:
    serialized_additional_content = Optional(str)

    @db_session
    def get_parent_nodes(self) -> DotDict[str, dict]:
        if self.rule_id == None:
            return DotDict()
        return Rule[self.rule_id].input_nodes()

    @db_session
    def get_additional_content(self) -> dict:
        if self.serialized_additional_content == None:
            return {}
        return json.loads(self.serialized_additional_content)

    @db_session
    def get_node_contents(self) -> dict:
        return {
            **self.get_content(),
            **self.get_additional_content(),
        }

    @classmethod
    @db_session
    def GETINSERT(cls, location, **additional_content) -> Storable:
        serialized_content = json.dumps(
            {"location": location},
            sort_keys=True,
        )
        node = cls.get(serialized_content=serialized_content)
        commit()
        if node is None:
            node = cls(
                serialized_content=serialized_content,
                serialized_additional_content=json.dumps(
                    additional_content,
                    sort_keys=True,
                ),
            )
            commit()
        return storable


@dataclasses.dataclass
class SimplePonyNodeStorage(snakemaketools.rules.NodeStorage):
    """Implementation of a general NodeStorage Protocol using Pony ORM.

    If you don't want to use the DB but use current IN-RAM numbering scheme, pass in `register_in_db=False` on init.
    """

    register_in_db: bool = True
    _rule_cnt: int = -1

    def get_rule_id(
        self,
        inputs: dict[str, snakemake.rules.Node],
    ) -> int:
        """Get a rule id for a given set of input nodes."""
        if not self.register_in_db:
            self._rule_cnt += 1
            return self._rule_cnt

        rule = Rule.GETINSERT(**{name: node.location for name, node in inputs.items()})
        # Rule's are thefore indexed by their serialized argument indices.
        return rule.id

    def get_outputs(
        self,
        inputs: dict[str, snakemake.rules.Node],
        expected_outputs: tuple[snakemaketools.rules.Node, ...],
    ) -> tuple[snakemaketools.rules.Node, ...]:
        """Create output nodes for a given rule."""
        rule_id = self.get_rule_id(inputs=inputs)
        try:
            outputs = []
            for expected_output in expected_outputs:
                node = expected_output.copy()
                node.location = node.location.format(
                    rule_id=rule_id
                )  # node.location might not contain a wildcard for rule_id.
                if self.register_in_db:
                    Node.GETINSERT(**dict(node))
                outputs.append(node)
            return tuple(outputs)
        except Exception as e:
            self._rule_cnt -= 1  # roll back
            raise e

    def get_parent_nodes(
        self,
        location: str,
    ) -> DotDict[str, snakemaketools.rules.Node]:
        """Used in Snakemake DAG construction."""
        return DotDict(
            {
                node_name: self.node_factory(**node_kwargs)
                for node_name, node_kwargs in Node.GET(location)
                .get_parent_nodes()
                .items()
            }
        )

    # def getinsert_config(self, config):
    #     dbroot = DBRoot.GETINSERT(config)
    #     dbpath = Node(location=location_template.format(dbroot.id))
    #     return dbpath.location

    # def get_config(self, location: str):
    #     raise NotImplementedError

    # def get_serialized_config(self, path):
    #     raise NotImplementedError


# def getinsert_config_node(# but this is not necessary: configs could be registered with a Rule too
#     self,
#     config: dict,
# ) -> snakemaketools.rules.Node:
#     ...


# @classmethod
# @db_session
# def GET(cls, path: str) -> Node:
#     """Get an object ID from the DB if exists; otherwise first create it."""
#     path = cls.get(path=path)
#     commit()
#     assert path != None
#     return path
