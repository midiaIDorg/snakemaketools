from __future__ import annotations

import json

from pony.orm import Database, PrimaryKey, Required, commit, composite_index, db_session

db = Database()


class Node(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    _origin = Required(str)
    type = Required(str)
    composite_index(_origin, type)

    @property
    def origin(self) -> dict:
        return json.loads(self._origin)

    @classmethod
    @db_session
    def GETINSERT(cls, origin: dict, type: str) -> Node:
        """Get an object ID from the DB if exists; otherwise first create it.

        Arguments:
            origin (dict): Node's origin description.
            type (str): The type of the node.

        Returns:
            Node: An instance of the node.
        """
        _origin = json.dumps(origin, sort_keys=True)
        node = cls.get(_origin=_origin, type=type)
        commit()
        if node is not None:
            return node
        node = cls(_origin=_origin, type=type)
        commit()
        return node

    @classmethod
    @db_session
    def GET(cls, origin: dict, type: str) -> Node:
        """Get an object ID from the DB and raise exception otherwise.

        Arguments:
            origin (dict): Node's origin description.
            type (str): The type of the node.

        Returns:
            Node: An instance of the node.

        Raises:
            KeyError: if a node with a given (origin, type) does not exist in the db.
        """
        _origin = json.dumps(origin, sort_keys=True)
        node = cls.get(_origin=_origin, type=type)
        commit()
        if node is None:
            raise KeyError(
                f"There DB does not contain a Node(origin={origin}, type={type})"
            )
        return node
