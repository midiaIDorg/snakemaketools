"""
in Pony ORM: a single id is used for sublcasses: all of hierarchy is in one freaking table. so no clashes between Storable, Config, Rule, and Node instances possible if using id to get new paths.

That set, direct usage of Storable.GET is impossible, whenever two subclasses would share their content.
"""
from __future__ import annotations

import dataclasses
import json

import snakemaketools.rules
from pony.orm import Optional, PrimaryKey, Required, commit, db_session
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
        return self.get_content()


class Rule(Storable):
    @db_session
    def get_input_nodes(self) -> dict[str, str]:  # order matters
        return {
            node_name: Node[node_id].get_node_contents()["location"]
            for node_name, node_id in self.get_content().items()
        }


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
        return Rule[self.rule_id].get_input_nodes()

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
        config: dict | str | None = None,
        wildcards: dict | None = None,
    ) -> tuple[snakemaketools.rules.Node, ...]:
        """Create output nodes for a given rule."""

        # NOTE: even if ever inputs for Config.GETINSERT and Rule.GETINSERT would
        # coincide, that would not result in an error while calling GET of either
        # Confir nor Rule. But would for Storable.
        if config != None:
            if isinstance(config, str):
                config = {"config": config}
            assert "config_id" not in config, "Do not put `config_id` key into config."
            assert "rule_id" not in config, "Do not put `rule_id` key into config."
            storable_id = config_id = Config.GETINSERT(**config)
            rule_id = None
        else:
            storable_id = rule_id = Rule.GETINSERT(
                **{
                    name: Node.GET(location=node.location)
                    for name, node in inputs.items()
                }
            )
            config_id = None

        outputs = []
        assert "id" not in wildcards
        for expected_output in expected_outputs:
            node = expected_output.copy()
            node.location = node.location.format(id=storable_id, **wildcards)
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
    def get_rule_input_paths(
        self,
        rule_id: int,
    ) -> dict[str, str]:
        """Used in Snakemake DAG construction."""
        return Rule[rule_id].get_input_nodes()

    @db_session
    def get_config(self, location: str) -> str:
        node = Storable[Storable.GET(location=location)]
        assert isinstance(node, Node), "Snakemake did not ask for a config."
        assert node.config_id != None
        return Config[node.config_id].get_config()
