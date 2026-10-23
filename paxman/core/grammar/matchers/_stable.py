"""Process-stable rendering of recognition values for digests and revisions.

``recognition_revision`` must be identical across processes for the same
library snapshot: it is the stamp that tells a consumer *which* recognition
tree produced a result, so a value that changes between two runs of the same
snapshot cannot be used to tell "different library" from "different process".

``repr()`` cannot be used for that. A ``frozenset`` / ``set`` / ``dict``
renders in iteration order, and string hashing is randomised per process
(``PYTHONHASHSEED``), so the same value renders differently in two
interpreters. ``repr()`` of a bound method or a plain object also carries a
memory address.

``stable_repr`` renders values canonically instead:

* containers carry their type, so an empty ``set``, ``frozenset`` and ``dict``
  stay distinguishable (``repr`` renders all three as ``{}``);
* set members and dict items are sorted, so iteration order cannot leak in;
* sequences keep their order — order is meaningful there;
* dataclasses render their ``init`` fields in declaration order, recursively.
  ``repr=False`` is ignored: it is a display hint, and a field the caller
  initialises can affect recognition;
* dataclasses and callables carry their defining module, so same-named
  objects from different modules cannot collide;
* callables render by qualified name plus any captured state (closure cells,
  ``functools.partial`` arguments) — never by address;
* compiled patterns render by source and flags;
* a payload that contains itself renders a back-edge marker instead of
  recursing forever;
* anything unmodelled keeps its ``repr`` with the memory-address suffix
  stripped.

Known limit: an unmodelled payload whose own ``repr`` embeds an unordered
container cannot be canonicalised from its text. An extension payload that
needs exact revision identity should be a dataclass, or expose a ``digest``.
"""

from __future__ import annotations

import dataclasses
import functools
import inspect
import re
from typing import Any, cast

# A default ``object.__repr__`` ends with `` at 0x7f3c...>``. Strip only that
# suffix: a ``0x`` value elsewhere in the repr may be meaningful data.
_ADDRESS_SUFFIX = re.compile(r" at 0x[0-9a-fA-F]+>")


def stable_repr(obj: Any) -> str:
    """Render ``obj`` canonically, independent of process hash randomisation.

    Args:
        obj: Any value appearing in a matcher's recognition payload.

    Returns:
        A string that is equal for two values that are equal as recognition
        inputs, in any process. Self-referential payloads terminate with a
        ``<cycle:...>`` back-edge marker.
    """
    return _render(obj, set())


def _qualified_name(obj: Any) -> str:
    """Return ``module.qualname`` for a dataclass instance or callable."""
    module = getattr(obj, "__module__", None) or type(obj).__module__
    qualname = getattr(obj, "__qualname__", None) or type(obj).__qualname__
    return f"{module}.{qualname}"


def _render_callable(obj: Any, seen: set[int]) -> str:
    """Render a callable by name plus any state that can change behaviour."""
    head = _qualified_name(obj)
    if inspect.ismethod(obj):
        # The bound instance is already rendered by the enclosing dataclass;
        # following it would just cycle back into the same matcher.
        return head
    if isinstance(obj, functools.partial):
        return (
            f"partial({_render(obj.func, seen)},"
            f"{_render(obj.args, seen)},"
            f"{_render(obj.keywords or {}, seen)})"
        )
    closure = getattr(obj, "__closure__", None)
    if not closure:
        return head
    cells: list[str] = []
    for cell in cast(tuple[Any, ...], closure):
        try:
            value = cast(Any, cell.cell_contents)
        except ValueError:  # pragma: no cover - cell not yet bound
            cells.append("<empty>")
            continue
        cells.append(_render(value, seen))
    return f"{head}[{','.join(cells)}]"


def _render(obj: Any, seen: set[int]) -> str:
    """Render one value, tracking in-flight containers/objects in ``seen``."""
    if isinstance(obj, re.Pattern):
        pattern = cast(re.Pattern[str], obj)
        return f"re({pattern.pattern!r},{pattern.flags})"
    if obj is None or isinstance(obj, (bool, int, float, complex, str, bytes)):
        return repr(obj)

    marker = id(obj)
    if marker in seen:
        # A payload that reaches itself. Name the shape and stop; recursing
        # would raise RecursionError into freeze_registry.
        return f"<cycle:{_qualified_name(obj)}>"

    if isinstance(obj, (frozenset, set)):
        items: frozenset[Any] | set[Any] = cast(frozenset[Any] | set[Any], obj)
        seen.add(marker)
        try:
            body = ",".join(sorted(_render(item, seen) for item in items))
        finally:
            seen.discard(marker)
        kind = "frozenset" if isinstance(obj, frozenset) else "set"
        return f"{kind}({{{body}}})"
    if isinstance(obj, tuple):
        seq: tuple[Any, ...] = cast(tuple[Any, ...], obj)
        seen.add(marker)
        try:
            body = ",".join(_render(item, seen) for item in seq)
        finally:
            seen.discard(marker)
        return f"tuple({body})"
    if isinstance(obj, list):
        lst: list[Any] = cast(list[Any], obj)
        seen.add(marker)
        try:
            body = ",".join(_render(item, seen) for item in lst)
        finally:
            seen.discard(marker)
        return f"list([{body}])"
    if isinstance(obj, dict):
        mapping: dict[Any, Any] = cast(dict[Any, Any], obj)
        seen.add(marker)
        try:
            pairs = sorted(
                (_render(key, seen), _render(val, seen)) for key, val in mapping.items()
            )
        finally:
            seen.discard(marker)
        body = ",".join(f"{key}:{val}" for key, val in pairs)
        return f"dict({{{body}}})"
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        seen.add(marker)
        try:
            rendered = [
                f"{f.name}={_render(getattr(obj, f.name), seen)}"
                for f in dataclasses.fields(obj)
                if f.init
            ]
        finally:
            seen.discard(marker)
        return _qualified_name(obj) + "(" + ",".join(rendered) + ")"
    if callable(obj):
        return _render_callable(obj, seen)
    # Unmodelled payload: keep what its repr says, minus any memory address.
    return _ADDRESS_SUFFIX.sub(" at 0x>", repr(obj))
