"""Process-stable rendering of recognition values for digests and revisions.

``recognition_revision`` must be identical across processes for the same
library snapshot: it is the stamp that tells a consumer *which* recognition
tree produced a result, so a value that changes between two runs of the same
snapshot cannot be used to tell "different library" from "different process".

``repr()`` cannot be used for that. A ``frozenset`` / ``set`` / ``dict``
renders in iteration order, and string hashing is randomised per process
(``PYTHONHASHSEED``), so the same value renders differently in two
interpreters. ``repr()`` of an unbound function or a bound method also carries
a memory address on some builds.

``stable_repr`` renders values canonically instead:

* sets are sorted, so iteration order cannot leak in;
* dicts are sorted by rendered key;
* sequences keep their order — order is meaningful there;
* dataclasses render their ``init`` fields in declaration order, recursively;
* callables render by ``__qualname__``, never by address;
* compiled patterns render by source and flags;
* anything unmodelled keeps its ``repr`` with memory addresses stripped.

Every digest that feeds ``recognition_revision`` uses this instead of
``repr()``.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Any, cast

# A default ``object.__repr__`` carries a per-process memory address
# (``<Foo object at 0x7f3c...>``). Strip the digits so an unmodelled payload
# still renders identically in two interpreters.
_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")


def stable_repr(obj: Any) -> str:
    """Render ``obj`` canonically, independent of process hash randomisation.

    Args:
        obj: Any value appearing in a matcher's recognition payload.

    Returns:
        A string that is equal for two values that are equal as recognition
        inputs, in any process.
    """
    if isinstance(obj, re.Pattern):
        pattern = cast(re.Pattern[str], obj)
        return f"re({pattern.pattern!r},{pattern.flags})"
    if obj is None or isinstance(obj, (bool, int, float, complex, str, bytes)):
        return repr(obj)
    if isinstance(obj, (frozenset, set)):
        items: frozenset[Any] | set[Any] = cast(frozenset[Any] | set[Any], obj)
        return "{" + ",".join(sorted(stable_repr(item) for item in items)) + "}"
    if isinstance(obj, tuple):
        seq: tuple[Any, ...] = cast(tuple[Any, ...], obj)
        return "(" + ",".join(stable_repr(item) for item in seq) + ")"
    if isinstance(obj, list):
        lst: list[Any] = cast(list[Any], obj)
        return "[" + ",".join(stable_repr(item) for item in lst) + "]"
    if isinstance(obj, dict):
        mapping: dict[Any, Any] = cast(dict[Any, Any], obj)
        pairs = sorted(
            (stable_repr(key), stable_repr(val)) for key, val in mapping.items()
        )
        return "{" + ",".join(f"{key}:{val}" for key, val in pairs) + "}"
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        rendered = [
            f"{f.name}={stable_repr(getattr(obj, f.name))}"
            for f in dataclasses.fields(obj)
            if f.repr and f.init
        ]
        return f"{type(obj).__qualname__}(" + ",".join(rendered) + ")"
    if callable(obj):
        return getattr(obj, "__qualname__", type(obj).__name__)
    # Unmodelled payload: keep what its repr says, minus any memory address.
    return _ADDRESS.sub("0x", repr(obj))
