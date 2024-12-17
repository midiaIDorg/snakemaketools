"""
in Pony ORM: a single id is used for sublcasses: all of hierarchy is in one freaking table. so no clashes between Storable, Config, Rule, and Node instances possible if using id to get new paths.

That set, direct usage of Storable.GET is impossible, whenever two subclasses would share their content.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from pony.orm import Optional, PrimaryKey, Required, commit, db_session

import snakemaketools.db_config
import snakemaketools.rules
from snakemaketools.datastructures import DotDict


class Storable(snakemaketools.db_config.db.Entity):
    """A general entry in a DB.

    Only one DB table is used to represent all inheritance structure by PonyORM.
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
    def get_config(self) -> DotDict:
        return DotDict(self.get_content())


class Rule(Storable):
    @db_session
    def get_input_nodes(self) -> dict[str, str]:  # order matters
        return {
            node_name: Node[node_id].get_node_contents()["location"]
            for node_name, node_id in self.get_content().items()
        }

    @classmethod
    def GETINSERT_RULEID(cls, inputs: dict[str, snakemaketools.rules.Node]) -> int:
        return cls.GETINSERT(
            **{name: Node.GET(location=node.location) for name, node in inputs.items()}
        )


class Node(Storable):
    """Any meaningul pipeline entity."""

    rule_id = Optional(int)
    config_id = Optional(int)
    serialized_additional_content = Optional(str)  # for subclasses

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
        assert (
            "{" not in location or "}" not in location
        ), f"Some wildcards left unfilled before storing in the DB in\n`{location}`\n."
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

    def __init__(self):
        # Representing `none` in the DB.
        assert Path(
            "none"
        ).exists(), "Missing file `none` in the working directory. Please restore it."
        Node.GETINSERT(location="none")

    def get_outputs(
        self,
        inputs: dict[str, snakemaketools.rules.Node],
        expected_outputs: tuple[snakemaketools.rules.Node, ...],
        wildcards: dict[str, snakemaketools.rules.Wildcard],
        config: snakemaketools.rules.Config | None,
    ) -> tuple[snakemaketools.rules.Node, ...]:
        """
        Create output nodes for a given rule.
        """
        location_wildcards = {
            wildcard_name: wildcard.value
            for wildcard_name, wildcard in wildcards.items()
        }
        if config is not None:
            # NOTE: even if ever inputs for Config.GETINSERT and Rule.GETINSERT would
            # coincide, that would not result in an error while calling GET of either
            # Config nor Rule. But would for Storable.
            storable_id = config_id = Config.GETINSERT(
                parsed=config.parsed,
                serialized=config.serialized,
            )
            rule_id = None
            for name, location_wildcard in config.location_wildcards.items():
                assert (
                    name not in location_wildcards
                ), f"`{name}` already in `location_wildcards`"
                location_wildcards[name] = location_wildcard.value
        else:
            storable_id = rule_id = Rule.GETINSERT_RULEID(inputs)
            config_id = None

        outputs = []
        for expected_output in expected_outputs:
            node = expected_output.copy()
            node.location = node.location.format(id=storable_id, **location_wildcards)
            node.db_node_id = Node.GETINSERT(
                rule_id=rule_id,
                config_id=config_id,
                location=node.location,
            )
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
    def get_config(self, location: str) -> DotDict:
        node = Storable[Storable.GET(location=location)]
        assert isinstance(node, Node), "Snakemake did not ask for a config."
        assert (
            node.config_id != None
        ), "Passed in a node with config_id being null pointer."
        return Config[node.config_id].get_config()
