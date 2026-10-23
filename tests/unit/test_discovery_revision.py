"""Gates for the ``recognition_revision`` stamp.

Two properties, both regression-pinned:

* **Cost** — ``freeze_registry`` uses each matcher's cached ``digest``
  (computed once at construction) instead of re-deriving sorted tokens per
  freeze, and snapshot hashing is memoized.
* **Stability** — the revision is identical across processes for the same
  library snapshot. Several payloads used to be rendered with ``repr()``,
  which for a ``frozenset[str]`` follows hash order, so the revision varied
  with ``PYTHONHASHSEED`` and could not distinguish "different library" from
  "different process".
"""

from __future__ import annotations


def test_freeze_twice_identical_recognition_revision() -> None:
    from paxman.capabilities.Country.capability import CountryCapability
    from paxman.core.discovery import (
        freeze_registry,
        get_recognition_revision,
        register_capability,
        reset_registry,
    )

    reset_registry()
    register_capability(CountryCapability())
    freeze_registry()
    rev1 = get_recognition_revision()
    reset_registry()
    register_capability(CountryCapability())
    freeze_registry()
    rev2 = get_recognition_revision()
    assert rev1 == rev2, (
        f"freeze twice must give identical revision: {rev1!r} != {rev2!r}"
    )
    assert rev1 != "0"
    reset_registry()


def test_repeated_freeze_uses_cached_digests() -> None:
    """Second onward freeze must use cached digests via matcher.digest identity."""
    from paxman.core.discovery import (
        freeze_registry,
        reset_registry,
    )
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher
    from paxman.core.grammar.matchers.regex import RegexMatcher
    from paxman.core.grammar.matchers.scanner import ScannerMatcher
    from paxman.core.grammar.scan_context import View

    lex = LexiconMatcher(tokens=frozenset({"hello", "world"}))
    assert hasattr(lex, "digest")
    lex_d = getattr(lex, "digest", None)
    assert isinstance(lex_d, str) and len(lex_d) > 0

    reg = RegexMatcher(pattern=r"\d+", flags=0)
    assert hasattr(reg, "digest")
    reg_d = getattr(reg, "digest", None)
    assert isinstance(reg_d, str) and len(reg_d) > 0

    def _scan(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    scan = ScannerMatcher(scan=_scan, max_window=10)
    assert hasattr(scan, "digest")
    scan_d = getattr(scan, "digest", None)
    assert isinstance(scan_d, str) and len(scan_d) > 0

    lex_digest_id = id(lex_d)
    _ = (reg_d, scan_d)

    from paxman.capabilities.Country.capability import CountryCapability
    from paxman.core.discovery import register_capability

    for _ in range(5):
        reset_registry()
        register_capability(CountryCapability())
        freeze_registry()
        lex2 = LexiconMatcher(tokens=frozenset({"hello", "world"}))
        assert getattr(lex2, "digest", None) == getattr(lex, "digest", None), (
            "same tokens must give equal digest"
        )

    assert getattr(lex, "digest", None) == getattr(
        LexiconMatcher(tokens=frozenset({"hello", "world"})), "digest", None
    )
    # digest is computed once at construction, so the string object is retained
    assert id(getattr(lex, "digest", None)) == lex_digest_id

    for _ in range(3):
        assert hasattr(LexiconMatcher(tokens=frozenset({"a", "b"})), "digest")

    reset_registry()


def test_lexicon_digest_purity_same_tokens_equal() -> None:
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher

    a = LexiconMatcher(tokens=frozenset({"alpha", "beta", "gamma"}))
    b = LexiconMatcher(tokens=frozenset({"gamma", "beta", "alpha"}))
    assert getattr(a, "digest", None) == getattr(b, "digest", None), (
        "same tokens in any order must give equal digest"
    )
    assert isinstance(getattr(a, "digest", None), str)


def test_lexicon_digest_changes_on_token_add() -> None:
    from paxman.core.grammar.matchers.lexicon import LexiconMatcher

    base = LexiconMatcher(tokens=frozenset({"alpha", "beta"}))
    plus_one = LexiconMatcher(tokens=frozenset({"alpha", "beta", "gamma"}))
    assert getattr(base, "digest", None) != getattr(plus_one, "digest", None), (
        "+1 token must change digest"
    )


def test_regex_digest_purity() -> None:
    from paxman.core.grammar.matchers.regex import RegexMatcher

    a = RegexMatcher(pattern=r"hello\d+", flags=0)
    b = RegexMatcher(pattern=r"hello\d+", flags=0)
    c = RegexMatcher(pattern=r"hello\d+", flags=2)
    d = RegexMatcher(pattern=r"world\d+", flags=0)
    assert getattr(a, "digest", None) == getattr(b, "digest", None)
    assert getattr(a, "digest", None) != getattr(c, "digest", None), (
        "flags change must change digest"
    )
    assert getattr(a, "digest", None) != getattr(d, "digest", None), (
        "pattern change must change digest"
    )


def test_scanner_digest_purity() -> None:
    from paxman.core.grammar.boundary_spec import BoundarySpec
    from paxman.core.grammar.matchers.scanner import ScannerMatcher
    from paxman.core.grammar.scan_context import View

    def _scan_a(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    def _scan_b(view: View, pos: int):  # type: ignore[no-untyped-def]
        return None

    s1 = ScannerMatcher(scan=_scan_a, max_window=10)
    s2 = ScannerMatcher(scan=_scan_a, max_window=10)
    s3 = ScannerMatcher(scan=_scan_a, max_window=20)
    s4 = ScannerMatcher(scan=_scan_b, max_window=10)
    assert getattr(s1, "digest", None) == getattr(s2, "digest", None)
    assert getattr(s1, "digest", None) != getattr(s3, "digest", None), (
        "max_window change must change digest"
    )
    assert getattr(s1, "digest", None) != getattr(s4, "digest", None), (
        "qualname change must change digest"
    )

    s5 = ScannerMatcher(scan=_scan_a, max_window=10, boundary=BoundarySpec.WORD)
    assert getattr(s1, "digest", None) != getattr(s5, "digest", None)


def test_snapshot_hash_memo_dict_exists() -> None:
    import paxman.core.discovery as disc

    val = getattr(disc, "_snapshot_hashes", None)
    assert hasattr(disc, "_snapshot_hashes"), (
        "discovery must expose _snapshot_hashes memo dict"
    )
    assert isinstance(val, dict)


def test_discovery_freeze_reads_digest_not_sorted_tokens() -> None:
    """Ensure freeze_registry source reads matcher.digest."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    src = (repo_root / "paxman" / "core" / "discovery.py").read_text(encoding="utf-8")
    assert (
        "matcher.digest" in src
        or 'getattr(matcher, "digest"' in src
        or "getattr(matcher, 'digest'" in src
    ), "freeze_registry must read matcher.digest"
    freeze_section = src[
        src.find("def freeze_registry") : src.find("def is_registry_frozen")
    ]
    assert "sorted(cast(Iterable[str], tokens_set))" not in freeze_section, (
        "freeze_registry must not re-derive sorted tokens — use matcher.digest"
    )


def test_stable_repr_renders_sets_and_dicts_canonically() -> None:
    """Exact serialisation: sorted, and tagged by container type.

    Comparing two equal collections inside one interpreter cannot catch an
    iteration-order-dependent renderer — equal frozensets share an iteration
    order — so the canonical text is pinned instead.
    """
    import re

    from paxman.core.grammar.matchers._stable import stable_repr

    assert (
        stable_repr(frozenset({"alpha", "beta", "gamma"}))
        == "frozenset({'alpha','beta','gamma'})"
    )
    assert stable_repr({"b": 1, "a": 2}) == "dict({'a':2,'b':1})"
    assert stable_repr(("a", "b")) == "tuple('a','b')"
    assert stable_repr(["a", "b"]) == "list(['a','b'])"
    # An empty container keeps its type, so an empty set and an empty dict
    # never collapse onto the same revision input.
    assert stable_repr(set()) == "set({})"
    assert stable_repr(frozenset()) == "frozenset({})"
    assert stable_repr({}) == "dict({})"
    # Sequence order is meaningful and therefore preserved.
    assert stable_repr(("a", "b")) != stable_repr(("b", "a"))
    # Scalars render as repr.
    assert stable_repr("US") == "'US'"
    assert stable_repr(None) == "None"
    # Compiled patterns render by source and flags, not by object identity.
    assert stable_repr(re.compile("a+", re.I)) == "re('a+',34)"
    assert stable_repr(re.compile("a+")) != stable_repr(re.compile("a+", re.I))
    assert "0x" not in stable_repr(re.compile("a+"))


def test_stable_repr_terminates_on_self_referential_payloads() -> None:
    """A payload that contains itself gets a back-edge marker, not a crash.

    An extension-supplied cycle must not raise ``RecursionError`` out of
    ``freeze_registry`` — the registry is already frozen by then, so the
    revision would never be computed.
    """
    from paxman.core.grammar.matchers._stable import stable_repr

    cyclic: list[object] = []
    cyclic.append(cyclic)
    assert stable_repr(cyclic) == "list([<cycle:builtins.list>])"

    nested: dict[str, object] = {}
    nested["self"] = nested
    assert stable_repr(nested) == "dict({'self':<cycle:builtins.dict>})"

    # A *shared* subtree is not a cycle and is rendered in full at each site.
    shared = ("a",)
    assert stable_repr((shared, shared)) == "tuple(tuple('a'),tuple('a'))"


def test_stable_repr_captures_callable_state() -> None:
    """Callables render by name plus captured state, never by address."""
    import functools

    from paxman.core.grammar.matchers._stable import stable_repr

    def make(value: int):
        def predicate(text: str, subject: str) -> bool:
            return text == subject[:value]

        return predicate

    one, two = make(1), make(2)
    # Same factory line, same qualname, different captured value.
    assert stable_repr(one) != stable_repr(two)
    assert stable_repr(one) == stable_repr(make(1))
    assert ".predicate[1]" in stable_repr(one)
    # The defining module is part of the name, so same-qualname callables
    # from different modules cannot collide.
    assert stable_repr(one).startswith(__name__ + ".")
    assert "0x" not in stable_repr(one)

    assert (
        stable_repr(functools.partial(int, base=2))
        == "partial(builtins.int,tuple(),dict({'base':2}))"
    )
    assert stable_repr(functools.partial(int, base=2)) != stable_repr(
        functools.partial(int, base=8)
    )

    # A bound method renders by name only: its instance is already rendered by
    # the enclosing dataclass, and following it would cycle back.
    class _Bound:
        def method(self) -> None:  # pragma: no cover - identity only
            pass

    assert stable_repr(_Bound().method).endswith("._Bound.method")
    assert stable_repr(_Bound().method) == stable_repr(_Bound().method)


def test_stable_repr_captures_default_arguments() -> None:
    """A free variable bound as a default argument is still captured state.

    ``make`` closes over nothing: ``value`` is a default, so ``__closure__`` is
    ``None``. Rendering only closure cells made two such predicates — one
    matching ``"a"`` and one matching ``"b"`` — render identically, so a
    behaviour change would not move the digest.
    """
    from paxman.core.grammar.matchers._stable import stable_repr

    def make(value: str = "a"):
        def predicate(text: str, subject: str, expected: str = value) -> bool:
            return text == expected

        return predicate

    first, second = make("a"), make("b")
    assert first.__closure__ is None, "precondition: no closure to render"
    assert stable_repr(first) != stable_repr(second)
    assert stable_repr(first) == stable_repr(make("a"))
    assert "tuple('a')" in stable_repr(first)

    # Keyword-only defaults are a separate collection and must also count.
    def make_kw(value: str = "a"):
        def predicate(text: str, subject: str, *, expected: str = value) -> bool:
            return text == expected

        return predicate

    assert stable_repr(make_kw("a")) != stable_repr(make_kw("b"))
    assert "dict({'expected':'b'})" in stable_repr(make_kw("b"))
    # Positional defaults keep their order: they bind positionally.
    assert stable_repr(make_kw("a")) != stable_repr(make("a"))


def test_stable_repr_terminates_on_self_referential_callables() -> None:
    """A callable that closes over itself gets a cycle marker, not a crash.

    The callable must be in ``seen`` before its closure cells are rendered;
    otherwise ``_render`` re-enters ``_render_callable`` on the same object
    forever.
    """
    from paxman.core.grammar.matchers._stable import stable_repr

    def make():
        def predicate(text: str, subject: str) -> bool:
            return predicate is not None

        return predicate

    recursive = make()
    assert recursive.__closure__ is not None, "precondition: self-reference"
    rendered = stable_repr(recursive)
    assert "<cycle:" in rendered
    assert rendered.endswith(">]")
    assert "0x" not in rendered


def test_stable_repr_includes_repr_false_init_fields() -> None:
    """``repr=False`` is a display hint, not a reason to drop configuration."""
    import dataclasses

    from paxman.core.grammar.matchers._stable import stable_repr

    @dataclasses.dataclass(frozen=True)
    class _Payload:
        visible: str
        hidden: str = dataclasses.field(repr=False)
        derived: str = dataclasses.field(default="x", init=False, repr=False)

    first = _Payload(visible="v", hidden="one")
    second = _Payload(visible="v", hidden="two")
    assert stable_repr(first) != stable_repr(second)
    assert "hidden='one'" in stable_repr(first)
    # init=False is computed, not configured, so it stays out of the digest.
    assert "derived=" not in stable_repr(first)


def test_stable_repr_strips_only_the_address_suffix() -> None:
    """An unmodelled payload loses its address but keeps meaningful hex."""
    import re

    from paxman.core.grammar.matchers._stable import stable_repr

    class _Opaque:
        def __init__(self, value: int) -> None:
            self.value = value

        def __repr__(self) -> str:
            return f"_Opaque(value=0x{self.value:x})"

    # A meaningful hexadecimal payload survives the address filter.
    assert stable_repr(_Opaque(16)) == "_Opaque(value=0x10)"

    class _Default:
        pass

    first, second = _Default(), _Default()
    # A default repr's address is stripped, so two instances agree.
    assert stable_repr(first) == stable_repr(second)
    assert re.search(r"0x[0-9a-fA-F]", stable_repr(first)) is None


def test_anchor_set_stable_repr_is_canonical() -> None:
    """A dataclass payload renders its frozenset fields sorted."""
    from paxman.core.grammar.anchors import AnchorSet
    from paxman.core.grammar.matchers._stable import stable_repr

    anchors = AnchorSet(
        literals=frozenset({"y", "x"}), key_sets=(frozenset({"q", "p"}),)
    )
    rendered = stable_repr(anchors)
    assert "literals=frozenset({'x','y'})" in rendered
    assert "key_sets=tuple(frozenset({'p','q'}))" in rendered
    assert rendered.startswith("paxman.core.grammar.anchors.AnchorSet(")
    assert "0x" not in rendered


def test_recognition_revision_is_process_stable() -> None:
    """``recognition_revision`` must be identical across processes.

    The revision hashes every matcher's compiled payload. Several payloads
    were rendered with ``repr()`` — which for a ``frozenset[str]`` follows
    hash order and therefore varies with ``PYTHONHASHSEED``. A revision that
    changes between two runs of the same library snapshot cannot be used to
    tell "different library" from "different process".
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    script = (
        "import paxman\n"
        "from paxman.core.discovery import freeze_registry, get_recognition_revision\n"
        "paxman.register_all_shipped()\n"
        "freeze_registry()\n"
        "print(get_recognition_revision())\n"
    )
    revisions: set[str] = set()
    for seed in ("0", "1", "12345"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        revisions.add(completed.stdout.strip())
    assert len(revisions) == 1, (
        "recognition_revision varies across processes "
        f"(PYTHONHASHSEED 0/1/12345): {sorted(revisions)}"
    )
    assert revisions != {"0"}
