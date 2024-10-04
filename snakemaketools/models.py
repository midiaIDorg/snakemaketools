"""
in Pony ORM: a single id is used for sublcasses: all of hierarchy is in one freaking table. so no clashes between Storable, Config, Rule, and Node instances possible if using id to get new paths.

That set, direct usage of Storable.GET is impossible, whenever two subclasses would share their content.
"""
from __future__ import annotations

import dataclasses
import json

from pony.orm import Optional, PrimaryKey, Required, commit, db_session

import snakemaketools.rules
from snakemaketools.datastructures import DotDict
from snakemaketools.db_config import db


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
    def GETINSERT(cls, **content) -> int:
        serialized_content = json.dumps(content, sort_keys=True)
        storable = cls.get(serialized_content=serialized_content)
        commit()
        if storable is None:
            storable = cls(serialized_content=serialized_content)
            commit()
        return storable.id

    @classmethod
    @db_session
    def GET(cls, **content: str) -> int:
        """Get an object ID from the DB if exists; otherwise first create it."""
        serialized_content = json.dumps(content, sort_keys=True)
        storable = cls.get(serialized_content=serialized_content)
        commit()
        if storable == None:
            raise KeyError(
                f"There is no storable with content `{serialized_content}` in the DB."
            )
        return storable.id


class Config(Storable):
    def get_config(self) -> dict:
        return self.get_content()["config"]


class Rule(Storable):
    def input_nodes(self) -> DotDict[str, dict]:  # order matters
        inputs: DotDict[str, dict] = DotDict()
        for node_name, node_id in self.get_content().items():
            inputs[node_name] = Node[node_id].get_node_contents()
        return inputs


class Node(Storable):
    """Any meaningul pipeline entity."""

    rule_id = Optional(int)
    config_id = Optional(int)
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
    def GETINSERT(
        cls,
        location,
        rule_id=None,
        config_id=None,
        **additional_content,
    ) -> int:
        serialized_content = json.dumps(
            {"location": location},
            sort_keys=True,
        )
        node = cls.get(serialized_content=serialized_content)
        commit()
        if node is None:
            serialized_additional_content = None
            if len(additional_content):
                serialized_additional_content = json.dumps(
                    additional_content,
                    sort_keys=True,
                )
            node = cls(
                rule_id=rule_id,
                config_id=config_id,
                serialized_content=serialized_content,
                serialized_additional_content=serialized_additional_content,
            )
            commit()
        return node.id


@dataclasses.dataclass
class SimplePonyNodeStorage(snakemaketools.rules.NodeStorage):
    """Implementation of a general NodeStorage Protocol using Pony ORM."""

    debug: bool = False

    def get_outputs(
        self,
        inputs: dict[str, snakemaketools.rules.Node],
        expected_outputs: tuple[snakemaketools.rules.Node, ...],
        config: dict | None = None,
    ) -> tuple[snakemaketools.rules.Node, ...]:
        """Create output nodes for a given rule."""

        # NOTE: even if ever inputs for Config.GETINSERT and Rule.GETINSERT would
        # coincide, that would not result in an error while calling GET of either
        # Confir nor Rule. But would for Storable.
        if config != None:
            storable_id = config_id = Config.GETINSERT(**config)
            rule_id = None
        else:
            storable_id = rule_id = Rule.GETINSERT(
                **{
                    name: Node.GET(location=node.location)
                    # name: Node[node.id]
                    for name, node in inputs.items()
                }
            )
            config_id = None

        outputs = []
        for expected_output in expected_outputs:
            node = expected_output.copy()
            node.location = node.location.format(id=storable_id)
            db_node_id = Node.GETINSERT(
                rule_id=rule_id,
                config_id=config_id,
                location=node.location,
                # **dict(node),
            )
            if self.debug:
                node._debug["rule_id"] = rule_id
                node._debug["config_id"] = config_id
                node._debug["db_node"] = db_node_id
            outputs.append(node)
        return tuple(outputs)

    @db_session
    def get_parent_nodes(
        self,
        location: str,
    ) -> DotDict[str, snakemaketools.rules.Node]:
        """Used in Snakemake DAG construction."""
        return DotDict(
            {
                node_name: self.node_factory(**node_kwargs)
                for node_name, node_kwargs in Node[Node.GET(location=location)]
                .get_parent_nodes()
                .items()
            }
        )

    @db_session
    def get_config(self, location: str) -> str:
        node = Storable[Storable.GET(location=location)]
        assert isinstance(node, Node), "Snakemake did not ask for a config."
        assert node.config_id != None
        return Config[node.config_id].get_config()
