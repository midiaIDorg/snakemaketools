from collections import OrderedDict
from typing import Generic, TypeVar

DotDictKey = TypeVar("DotDictKey")
DotDictValue = TypeVar("DotDictValue")


class DotDict(OrderedDict, Generic[DotDictKey, DotDictValue]):
    def __getattr__(self, key: DotDictKey) -> DotDictValue:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'")

    def __setattr__(self, key: DotDictKey, value: DotDictValue) -> None:
        self[key] = value

    def __delattr__(self, key: DotDictKey) -> None:
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'")

    @classmethod
    def Recursive(cls, dct):
        return cls(
            {k: cls.Recursive(v) if isinstance(v, dict) else v for k, v in dct.items()}
        )
